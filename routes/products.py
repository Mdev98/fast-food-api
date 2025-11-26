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
        - image_url: URL externe de l'image OU image_base64: Données base64 de l'image
        - category: Catégorie (requis)
        - available: Disponibilité (défaut: true)
        - brand: Marque (requis: planete_kebab ou mamapizza)
        
    Returns:
        201: Produit créé avec succès
        400: Données invalides
    """
    try:
        from utils.image_handler import ensure_products_folder, download_and_compress, compress_from_base64
        from flask import current_app
        
        # Validation des données
        data = request.get_json()
        validated_data = product_schema.load(data)
        
        # Créer le produit d'abord pour obtenir l'ID
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
        db.session.flush()  # Obtenir l'ID sans commit
        
        # Traiter l'image si fournie
        image_url = None
        image_base64 = data.get('image_base64')
        
        if image_url or image_base64:
            ensure_products_folder()
            
            if image_base64:
                # Traiter depuis base64
                result = compress_from_base64(
                    image_base64,
                    product.id
                )
                if result:
                    image_url = result['public_url']
                    logger.info(f"Image base64 traitée pour produit {product.id}")
            elif image_url and (image_url.startswith('http://') or image_url.startswith('https://')):
                # Télécharger et traiter depuis URL externe
                result = download_and_compress(
                    image_url,
                    product.id
                )
                if result:
                    image_url = result['public_url']
                    logger.info(f"Image téléchargée pour produit {product.id}")
        
        # Mettre à jour l'image_url du produit
        if image_url:
            product.image_url = image_url
        
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
        db.session.rollback()
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
        - image_url: URL externe de l'image OU image_base64: Données base64 de l'image
    
    Returns:
        200: Produit mis à jour
        404: Produit non trouvé
        400: Données invalides
    """
    try:
        from utils.image_handler import ensure_products_folder, download_and_compress, compress_from_base64, extract_filename_from_url, delete_local_image
        from flask import current_app
        
        product = db.session.get(Product, product_id)
        
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        # Validation des données (partial=True pour permettre les mises à jour partielles)
        data = request.get_json()
        validated_data = product_schema.load(data, partial=True)
        
        # Gérer l'image si fournie
        image_base64 = data.get('image_base64')
        image_url_provided = validated_data.get('image_url')
        
        if image_url_provided or image_base64:
            # Supprimer l'ancienne image locale si elle existe
            if product.image_url and '/static/products/' in product.image_url:
                old_filename = extract_filename_from_url(product.image_url)
                if old_filename:
                    delete_local_image(old_filename)
                    logger.info(f"Ancienne image supprimée: {old_filename}")
            
            ensure_products_folder()
            
            if image_base64:
                # Traiter depuis base64
                result = compress_from_base64(
                    image_base64,
                    product.id
                )
                if result:
                    product.image_url = result['public_url']
                    logger.info(f"Image base64 traitée pour produit {product.id}")
            elif image_url_provided and (image_url_provided.startswith('http://') or image_url_provided.startswith('https://')):
                # Télécharger et traiter depuis URL externe
                result = download_and_compress(
                    image_url_provided,
                    product.id
                )
                if result:
                    product.image_url = result['public_url']
                    logger.info(f"Image téléchargée pour produit {product.id}")
        else:
            # Mise à jour des champs sans image
            if 'name' in validated_data:
                product.name = validated_data['name']
            if 'description' in validated_data:
                product.description = validated_data['description']
            if 'price' in validated_data:
                product.price = validated_data['price']
            if 'category' in validated_data:
                product.category = validated_data['category']
            if 'available' in validated_data:
                product.available = validated_data['available']
            if 'brand' in validated_data:
                product.brand = BrandEnum(validated_data['brand'])
        
        # Mise à jour des champs sans image
        if 'name' in validated_data:
            product.name = validated_data['name']
        if 'description' in validated_data:
            product.description = validated_data['description']
        if 'price' in validated_data:
            product.price = validated_data['price']
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


@products_bp.route('/upload-image', methods=['POST'])
@require_api_key
def upload_product_image():
    """
    Upload une image de produit vers le stockage local
    
    Form data:
        - image: Fichier image (PNG, JPG, JPEG, GIF, WEBP, max 5MB)
        - product_id: ID du produit (requis)
        
    Returns:
        200: Image uploadée avec succès
        400: Erreur de validation
        500: Erreur serveur
    """
    try:
        from utils.image_handler import ensure_products_folder, compress_from_base64
        from flask import current_app
        
        # Vérifier qu'un fichier a été envoyé
        if 'image' not in request.files:
            return jsonify({
                'error': 'Fichier manquant',
                'message': 'Aucun fichier image fourni. Utilisez le champ "image".'
            }), 400
        
        file = request.files['image']
        product_id_str = request.form.get('product_id')
        
        if not product_id_str:
            return jsonify({
                'error': 'Paramètre manquant',
                'message': 'product_id est requis'
            }), 400
        
        try:
            product_id = int(product_id_str)
        except ValueError:
            return jsonify({
                'error': 'Paramètre invalide',
                'message': 'product_id doit être un nombre entier'
            }), 400
        
        # Vérifier que le produit existe
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        # Valider le fichier
        if not file or file.filename == '':
            return jsonify({
                'error': 'Fichier invalide',
                'message': 'Sélectionnez un fichier image'
            }), 400
        
        # Vérifier l'extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'error': 'Format invalide',
                'message': f'Format d\'image autorisé: {allowed_extensions}'
            }), 400
        
        ensure_products_folder()
        
        # Lire le fichier et le convertir en base64 pour utiliser compress_from_base64
        import base64
        file_content = file.read()
        base64_string = base64.b64encode(file_content).decode('utf-8')
        
        result = compress_from_base64(
            base64_string,
            product_id
        )
        
        if not result:
            return jsonify({
                'error': 'Échec traitement',
                'message': 'Impossible de traiter l\'image'
            }), 500
        
        # Supprimer l'ancienne image locale si elle existe
        from utils.image_handler import extract_filename_from_url, delete_local_image
        if product.image_url and '/static/products/' in product.image_url:
            old_filename = extract_filename_from_url(product.image_url)
            if old_filename:
                delete_local_image(old_filename)
        
        # Mettre à jour le produit
        product.image_url = result['public_url']
        db.session.commit()
        invalidate_products_cache()
        
        logger.info(f"Image uploadée avec succès: {result['public_url']}")
        
        return jsonify({
            'message': 'Image uploadée avec succès',
            'image_url': result['public_url'],
            'filename': result['filename']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de l'upload d'image: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors de l\'upload'
        }), 500


@products_bp.route('/delete-image', methods=['DELETE'])
@require_api_key
def delete_product_image():
    """
    Supprime une image de produit du stockage local
    
    JSON body:
        - product_id: ID du produit (requis)
        
    Returns:
        200: Image supprimée
        400: Paramètres manquants
        404: Produit non trouvé
    """
    try:
        from utils.image_handler import extract_filename_from_url, delete_local_image
        
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({
                'error': 'Paramètre manquant',
                'message': 'product_id est requis'
            }), 400
        
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({
                'error': 'Produit non trouvé',
                'message': f'Aucun produit avec l\'ID {product_id}'
            }), 404
        
        # Supprimer l'image locale si elle existe
        if product.image_url and '/static/products/' in product.image_url:
            filename = extract_filename_from_url(product.image_url)
            if filename:
                delete_local_image(filename)
                product.image_url = None
                db.session.commit()
                invalidate_products_cache()
                logger.info(f"Image supprimée pour le produit {product_id}")
                return jsonify({
                    'message': 'Image supprimée avec succès'
                }), 200
        
        return jsonify({
            'message': 'Aucune image à supprimer'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression d'image: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500


@products_bp.route('/create-with-image', methods=['POST'])
@require_api_key
@validate_json_content_type
def create_product_with_image():
    """
    Crée un produit avec upload automatique d'image depuis URL externe
    
    ENDPOINT OPTIMISÉ POUR GOOGLE SHEETS APP SCRIPT
    
    Body (JSON):
        - name: Nom du produit (requis)
        - description: Description
        - price: Prix (requis, > 0)
        - category: Catégorie (requis)
        - brand: Marque (requis: planete_kebab ou mamapizza)
        - available: Disponibilité (défaut: true)
        - image_url: URL externe de l'image (optionnel)
                     Si fournie, l'image sera téléchargée et uploadée sur Cloudinary
        
    Workflow automatique:
        1. Valide les données du produit
        2. Si image_url fournie:
           - Télécharge l'image depuis l'URL
           - Upload sur Cloudinary
           - Remplace image_url par l'URL Cloudinary
        3. Crée le produit en base
        
    Returns:
        201: Produit créé avec succès (avec URL Cloudinary si image fournie)
        400: Données invalides ou image impossible à télécharger
        500: Erreur serveur
    """
    try:
        # Validation des données
        data = request.get_json()
        validated_data = product_schema.load(data)
        
        cloudinary_url = None
        external_image_url = validated_data.get('image_url')
        
        # Si une URL d'image externe est fournie, la télécharger et uploader sur Cloudinary
        if external_image_url:
            try:
                from utils.images import init_cloudinary, upload_image
                from flask import current_app
                import requests
                from io import BytesIO
                import re
                
                # Initialiser Cloudinary
                if not init_cloudinary(current_app):
                    logger.warning("Cloudinary non configuré, création sans image")
                else:
                    # Convertir les URLs Google Drive au format direct
                    if 'drive.google.com' in external_image_url:
                        # Extraire l'ID du fichier depuis différents formats possibles
                        match = re.search(r'/d/([a-zA-Z0-9_-]+)', external_image_url)
                        if not match:
                            match = re.search(r'id=([a-zA-Z0-9_-]+)', external_image_url)
                        
                        if match:
                            file_id = match.group(1)
                            # Utiliser le format de téléchargement direct (plus fiable)
                            external_image_url = f"https://drive.google.com/uc?id={file_id}&export=download"
                            logger.info(f"URL Google Drive convertie: {external_image_url}")
                    
                    # Télécharger l'image depuis l'URL externe
                    logger.info(f"Téléchargement image depuis: {external_image_url}")
                    
                    response = requests.get(external_image_url, timeout=10, stream=True)
                    response.raise_for_status()
                    
                    # Vérifier que c'est bien une image
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        raise ValueError(f"URL ne pointe pas vers une image (type: {content_type})")
                    
                    # Créer un objet fichier depuis le contenu téléchargé
                    image_data = BytesIO(response.content)
                    image_data.name = 'image.jpg'  # Nom par défaut
                    
                    # Générer un public_id depuis le nom du produit
                    import re
                    public_id = re.sub(r'[^a-z0-9_-]', '_', validated_data['name'].lower())
                    
                    # Upload sur Cloudinary
                    upload_result = upload_image(
                        file_data=image_data,
                        folder="fast-food/products",
                        public_id=public_id
                    )
                    
                    if upload_result:
                        cloudinary_url = upload_result['url']
                        logger.info(f"Image uploadée sur Cloudinary: {cloudinary_url}")
                    else:
                        logger.warning("Échec upload Cloudinary, création sans image")
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur téléchargement image: {str(e)}")
                return jsonify({
                    'error': 'Image inaccessible',
                    'message': f'Impossible de télécharger l\'image depuis l\'URL fournie: {str(e)}'
                }), 400
                
            except Exception as e:
                logger.error(f"Erreur traitement image: {str(e)}")
                # Continue sans image plutôt que d'échouer complètement
                logger.warning(f"Création du produit sans image suite à erreur: {str(e)}")
        
        # Créer le produit avec l'URL Cloudinary (ou l'URL externe si upload a échoué)
        product = Product(
            name=validated_data['name'],
            description=validated_data.get('description'),
            price=validated_data['price'],
            image_url=cloudinary_url or external_image_url,  # Priorité à Cloudinary
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
            'product': result,
            'image_uploaded_to_cloudinary': cloudinary_url is not None
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
        logger.error(f"Erreur lors de la création du produit avec image: {str(e)}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue'
        }), 500
