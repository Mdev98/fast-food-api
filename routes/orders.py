"""
Routes pour la gestion des commandes
"""
import logging
from decimal import Decimal
from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from models import db, Order, Product, OrderStatusEnum
from schemas import order_create_schema, order_schema, orders_schema, order_update_schema, pagination_schema
from utils.security import require_api_key, validate_json_content_type
from utils.cache import cache, invalidate_orders_cache
from utils.sms import send_order_confirmation_sms, send_manager_notification_sms

logger = logging.getLogger(__name__)

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


def calculate_order_items(items_data):
    """
    Calcule et valide les items d'une commande
    
    Args:
        items_data: Liste des items avec product_id et quantity
        
    Returns:
        tuple: (items_list, total) où items_list contient les détails complets
        
    Raises:
        ValueError: Si un produit n'existe pas ou n'est pas disponible
    """
    items = []
    total = Decimal('0.00')
    
    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        
        # Vérifier que le produit existe
        product = db.session.get(Product, product_id)
        if not product:
            raise ValueError(f"Produit avec ID {product_id} introuvable")
        
        # Vérifier la disponibilité
        if not product.available:
            raise ValueError(f"Le produit '{product.name}' n'est pas disponible")
        
        # Calculer le sous-total
        unit_price = Decimal(str(product.price))
        subtotal = unit_price * quantity
        total += subtotal
        
        # Ajouter l'item complet
        items.append({
            'product_id': product.id,
            'name': product.name,
            'unit_price': float(unit_price),
            'quantity': quantity,
            'subtotal': float(subtotal)
        })
    
    return items, total


@orders_bp.route('', methods=['POST'])
@require_api_key
@validate_json_content_type
def create_order():
    """
    Crée une nouvelle commande
    
    Body (JSON):
        - customer_name: Nom du client (requis)
        - mobile: Téléphone du client (requis, format +33...)
        - address: Adresse de livraison (requis)
        - items: Liste d'objets {product_id, quantity} (requis)
        
    Returns:
        201: Commande créée
        400: Données invalides
    """
    try:
        # Validation des données de base
        data = request.get_json()
        validated_data = order_create_schema.load(data)
        
        # Calculer les items et le total
        try:
            items, total = calculate_order_items(validated_data['items'])
        except ValueError as e:
            return jsonify({
                'error': 'Validation des produits échouée',
                'message': str(e)
            }), 400
        
        # Créer la commande
        order = Order(
            customer_name=validated_data['customer_name'],
            mobile=validated_data['mobile'],
            address=validated_data['address'],
            details=validated_data.get('details'),
            items=items,
            total=total,
            status=OrderStatusEnum.RECEIVED
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Invalider le cache
        invalidate_orders_cache()
        
        logger.info(
            f"Commande créée: #{order.id} - {order.customer_name} - {float(order.total)}€"
        )
        
        # Envoyer les SMS de notification
        manager_mobile = current_app.config.get('MANAGER_MOBILE')
        mock_mode = current_app.config.get('SMS_MOCK_MODE', True)
        
        # Créer un résumé des articles pour le SMS
        items_summary = ", ".join([
            f"{item['quantity']}x {item['name']}" 
            for item in items
        ])
        
        # SMS au gérant avec tous les détails
        send_manager_notification_sms(
            order_id=order.id,
            customer_name=order.customer_name,
            customer_mobile=order.mobile,
            address=order.address,
            total=float(order.total),
            items_summary=items_summary,
            details=order.details or "",
            manager_mobile=manager_mobile,
            mock_mode=mock_mode
        )
        
        # SMS de confirmation au client
        send_order_confirmation_sms(
            order_id=order.id,
            customer_mobile=order.mobile,
            total=float(order.total),
            address=order.address,
            mock_mode=mock_mode
        )
        
        result = order_schema.dump(order)
        return jsonify({
            'message': 'Commande créée avec succès',
            'order': result
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation échouée',
            'message': e.messages
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erreur base de données lors de la création de commande: {str(e)}")
        return jsonify({
            'error': 'Erreur base de données',
            'message': 'Impossible de créer la commande'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de la commande: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@orders_bp.route('', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_orders():
    """
    Récupère la liste de toutes les commandes avec filtrage optionnel
    
    Query params:
        - status: Filtrer par statut (received, prepared, delivered)
        - page: Numéro de page (défaut: 1)
        - limit: Nombre d'éléments par page (défaut: 10, max: 100)
        
    Returns:
        200: Liste des commandes
    """
    try:
        # Validation des paramètres de pagination
        pagination_params = request.args.to_dict()
        try:
            validated_pagination = pagination_schema.load(pagination_params)
        except ValidationError:
            validated_pagination = {'page': 1, 'limit': 10}
        
        page = validated_pagination['page']
        limit = validated_pagination['limit']
        
        # Construction de la requête
        query = Order.query
        
        # Filtrage par statut
        status_filter = request.args.get('status')
        if status_filter:
            try:
                status_enum = OrderStatusEnum(status_filter)
                query = query.filter(Order.status == status_enum)
            except ValueError:
                return jsonify({
                    'error': 'Statut invalide',
                    'message': f'Le statut doit être {[s.value for s in OrderStatusEnum]}'
                }), 400
        
        # Tri par date (plus récentes en premier)
        query = query.order_by(Order.created_at.desc())
        
        # Pagination
        total = query.count()
        orders = query.offset((page - 1) * limit).limit(limit).all()
        
        # Sérialisation
        result = orders_schema.dump(orders)
        
        return jsonify({
            'orders': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@orders_bp.route('/<int:order_id>', methods=['GET'])
@cache.cached(timeout=600)
def get_order(order_id):
    """
    Récupère les détails d'une commande spécifique
    
    Args:
        order_id: ID de la commande
        
    Returns:
        200: Détails de la commande
        404: Commande non trouvée
    """
    try:
        order = db.session.get(Order, order_id)
        
        if not order:
            return jsonify({
                'error': 'Commande non trouvée',
                'message': f'Aucune commande avec l\'ID {order_id}'
            }), 404
        
        result = order_schema.dump(order)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la commande {order_id}: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@orders_bp.route('/<int:order_id>', methods=['PUT'])
@require_api_key
@validate_json_content_type
def update_order_status(order_id):
    """
    Met à jour le statut d'une commande
    
    Args:
        order_id: ID de la commande
        
    Body (JSON):
        - status: Nouveau statut (received, prepared, delivered)
        
    Returns:
        200: Commande mise à jour
        404: Commande non trouvée
        400: Données invalides
    """
    try:
        order = db.session.get(Order, order_id)
        
        if not order:
            return jsonify({
                'error': 'Commande non trouvée',
                'message': f'Aucune commande avec l\'ID {order_id}'
            }), 404
        
        # Validation des données
        data = request.get_json()
        validated_data = order_update_schema.load(data)
        
        # Mise à jour du statut
        new_status = OrderStatusEnum(validated_data['status'])
        old_status = order.status.value
        order.status = new_status
        
        db.session.commit()
        
        # Invalider le cache
        invalidate_orders_cache()
        
        logger.info(
            f"Commande #{order.id} - Statut mis à jour: {old_status} -> {new_status.value}"
        )
        
        result = order_schema.dump(order)
        return jsonify({
            'message': 'Statut de la commande mis à jour',
            'order': result
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation échouée',
            'message': e.messages
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erreur base de données lors de la mise à jour: {str(e)}")
        return jsonify({
            'error': 'Erreur base de données',
            'message': 'Impossible de mettre à jour la commande'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour de la commande: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500
