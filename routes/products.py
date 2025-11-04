"""
Routes pour la gestion des produits
"""
import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from models import db, Product, BrandEnum
from schemas import product_schema, products_schema, pagination_schema
from utils.security import require_api_key, validate_json_content_type
from utils.cache import cache, invalidate_products_cache

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_products():
    """
    Récupère la liste de tous les produits avec filtrage et pagination optionnels
    
    Query params:
        - brand: Filtrer par marque (planete_kebab ou mamapizza)
        - category: Filtrer par catégorie
        - available: Filtrer par disponibilité (true/false)
        - page: Numéro de page (défaut: 1)
        - limit: Nombre d'éléments par page (défaut: 10, max: 100)
    
    Returns:
        200: Liste des produits
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
        
        # Construction de la requête de base
        query = Product.query
        
        # Filtrage par marque
        brand_filter = request.args.get('brand')
        if brand_filter:
            try:
                brand_enum = BrandEnum(brand_filter)
                query = query.filter(Product.brand == brand_enum)
            except ValueError:
                return jsonify({
                    'error': 'Marque invalide',
                    'message': f'La marque doit être {[b.value for b in BrandEnum]}'
                }), 400
        
        # Filtrage par catégorie
        category_filter = request.args.get('category')
        if category_filter:
            query = query.filter(Product.category.ilike(f'%{category_filter}%'))
        
        # Filtrage par disponibilité
        available_filter = request.args.get('available')
        if available_filter:
            is_available = available_filter.lower() == 'true'
            query = query.filter(Product.available == is_available)
        
        # Tri par nom
        query = query.order_by(Product.name)
        
        # Pagination
        total = query.count()
        products = query.offset((page - 1) * limit).limit(limit).all()
        
        # Sérialisation
        result = products_schema.dump(products)
        
        return jsonify({
            'products': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des produits: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors de la récupération des produits'
        }), 500


@products_bp.route('/<int:product_id>', methods=['GET'])
@cache.cached(timeout=600)
def get_product(product_id):
    """
    Récupère les détails d'un produit spécifique
    
    Args:
        product_id: ID du produit
        
    Returns:
        200: Détails du produit
        404: Produit non trouvé
    """
    try:
        product = db.session.get(Product, product_id)
        
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        result = product_schema.dump(product)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du produit {product_id}: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@products_bp.route('', methods=['POST'])
@require_api_key
@validate_json_content_type
def create_product():
    """
    Crée un nouveau produit
    
    Body (JSON):
        - name: Nom du produit (requis)
        - description: Description
        - price: Prix (requis, > 0)
        - image_url: URL de l'image
        - category: Catégorie (requis)
        - available: Disponibilité (défaut: true)
        - brand: Marque (requis: planete_kebab ou mamapizza)
        
    Returns:
        201: Produit créé avec succès
        400: Données invalides
    """
    try:
        # Validation des données
        data = request.get_json()
        validated_data = product_schema.load(data)
        
        # Création du produit
        product = Product(
            name=validated_data['name'],
            description=validated_data.get('description'),
            price=validated_data['price'],
            image_url=validated_data.get('image_url'),
            category=validated_data['category'],
            available=validated_data.get('available', True),
            brand=BrandEnum(validated_data['brand'])
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Invalider le cache
        invalidate_products_cache()
        
        logger.info(f"Produit créé: {product.name} (ID: {product.id})")
        
        result = product_schema.dump(product)
        return jsonify({
            'message': 'Produit créé avec succès',
            'product': result
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation échouée',
            'message': e.messages
        }), 400
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erreur base de données lors de la création: {str(e)}")
        return jsonify({
            'error': 'Erreur base de données',
            'message': 'Impossible de créer le produit'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du produit: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@products_bp.route('/<int:product_id>', methods=['PUT'])
@require_api_key
@validate_json_content_type
def update_product(product_id):
    """
    Met à jour un produit existant
    
    Args:
        product_id: ID du produit à modifier
        
    Body (JSON): Mêmes champs que la création (tous optionnels)
    
    Returns:
        200: Produit mis à jour
        404: Produit non trouvé
        400: Données invalides
    """
    try:
        product = db.session.get(Product, product_id)
        
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        # Validation des données (partial=True pour permettre les mises à jour partielles)
        data = request.get_json()
        validated_data = product_schema.load(data, partial=True)
        
        # Mise à jour des champs
        if 'name' in validated_data:
            product.name = validated_data['name']
        if 'description' in validated_data:
            product.description = validated_data['description']
        if 'price' in validated_data:
            product.price = validated_data['price']
        if 'image_url' in validated_data:
            product.image_url = validated_data['image_url']
        if 'category' in validated_data:
            product.category = validated_data['category']
        if 'available' in validated_data:
            product.available = validated_data['available']
        if 'brand' in validated_data:
            product.brand = BrandEnum(validated_data['brand'])
        
        db.session.commit()
        
        # Invalider le cache
        invalidate_products_cache()
        
        logger.info(f"Produit mis à jour: {product.name} (ID: {product.id})")
        
        result = product_schema.dump(product)
        return jsonify({
            'message': 'Produit mis à jour avec succès',
            'product': result
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
            'message': 'Impossible de mettre à jour le produit'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour du produit: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@require_api_key
def delete_product(product_id):
    """
    Supprime un produit
    
    Args:
        product_id: ID du produit à supprimer
        
    Returns:
        200: Produit supprimé
        404: Produit non trouvé
    """
    try:
        product = db.session.get(Product, product_id)
        
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        
        # Invalider le cache
        invalidate_products_cache()
        
        logger.info(f"Produit supprimé: {product_name} (ID: {product_id})")
        
        return jsonify({
            'message': 'Produit supprimé avec succès',
            'product_id': product_id
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erreur base de données lors de la suppression: {str(e)}")
        return jsonify({
            'error': 'Erreur base de données',
            'message': 'Impossible de supprimer le produit'
        }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression du produit: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500
