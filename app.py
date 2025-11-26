"""
Application principale Flask pour l'API Fast-Food
"""
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import config
from models import db
from utils.cache import init_cache, cache, clear_cache
from utils.security import log_request_info, require_api_key
from routes import products_bp, orders_bp

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Factory function pour créer et configurer l'application Flask
    
    Args:
        config_name: Nom de la configuration à utiliser (development, production, testing)
        
    Returns:
        app: Instance Flask configurée
    """
    app = Flask(__name__)
    
    # Déterminer l'environnement
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Charger la configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    logger.info(f"Application démarrée en mode: {config_name}")
    
    # Initialiser les extensions
    db.init_app(app)
    init_cache(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'))
    
    # Initialiser le dossier des images locales
    from utils.image_handler import ensure_products_folder
    ensure_products_folder()
    
    # Configurer le servage des fichiers statiques
    with app.app_context():
        db.create_all()
        logger.info("Base de données initialisée")
        
        # En production, initialiser avec des données de base si la DB est vide
        if config_name == 'production':
            from models import Product, BrandEnum
            try:
                # Vérifier si des produits existent déjà
                existing_products = Product.query.count()
                if existing_products == 0:
                    logger.info("📦 Initialisation des données de production...")
                    
                    # Produits Planète Kebab
                    kebab_products = [
                        Product(name='Kebab Classique', description='Kebab avec viande, salade, tomate, oignon', 
                                price=6.50, category='Kebabs', brand=BrandEnum.PLANETE_KEBAB, available=True),
                        Product(name='Kebab Complet', description='Kebab avec frites et sauce au choix', 
                                price=8.00, category='Kebabs', brand=BrandEnum.PLANETE_KEBAB, available=True),
                        Product(name='Tacos Poulet', description='Tacos garni de poulet, frites et sauce fromagère', 
                                price=7.50, category='Tacos', brand=BrandEnum.PLANETE_KEBAB, available=True),
                        Product(name='Assiette Kebab', description='Viande kebab servie avec frites et salade', 
                                price=9.00, category='Assiettes', brand=BrandEnum.PLANETE_KEBAB, available=True),
                        Product(name='Coca-Cola', description='Boisson gazeuse 33cl', 
                                price=2.00, category='Boissons', brand=BrandEnum.PLANETE_KEBAB, available=True),
                    ]
                    
                    # Produits MamaPizza
                    pizza_products = [
                        Product(name='Pizza Margherita', description='Sauce tomate, mozzarella, basilic', 
                                price=9.00, category='Pizzas', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Pizza Reine', description='Sauce tomate, mozzarella, jambon, champignons', 
                                price=11.00, category='Pizzas', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Pizza 4 Fromages', description='Mozzarella, gorgonzola, chèvre, emmental', 
                                price=12.00, category='Pizzas', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Pizza Calzone', description='Pizza pliée garnie de jambon, champignons et mozzarella', 
                                price=11.50, category='Pizzas', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Tiramisu', description='Dessert italien au café et mascarpone', 
                                price=5.00, category='Desserts', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Salade César', description='Salade verte, poulet, parmesan, croûtons', 
                                price=8.00, category='Salades', brand=BrandEnum.MAMAPIZZA, available=True),
                        Product(name='Limonade', description='Boisson rafraîchissante 33cl', 
                                price=2.50, category='Boissons', brand=BrandEnum.MAMAPIZZA, available=True),
                    ]
                    
                    # Ajouter tous les produits
                    for product in kebab_products + pizza_products:
                        db.session.add(product)
                    
                    db.session.commit()
                    logger.info(f"✅ {len(kebab_products) + len(pizza_products)} produits initialisés!")
                else:
                    logger.info(f"ℹ️  Base de données contient déjà {existing_products} produits")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'initialisation des données: {str(e)}")
                db.session.rollback()
    
    # Hook before_request pour logger les requêtes
    @app.before_request
    def before_request():
        """Log les informations de chaque requête"""
        log_request_info()
    
    # Enregistrer les blueprints (routes)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    
    # Routes d'administration
    @app.route('/cache/clear', methods=['POST'])
    @require_api_key
    def clear_cache_route():
        """
        Vide le cache de l'application
        
        Query params:
            - prefix: Préfixe des clés à supprimer (optionnel)
            
        Returns:
            200: Cache vidé avec succès
        """
        try:
            prefix = request.args.get('prefix')
            clear_cache(prefix)
            
            message = f"Cache vidé (préfixe: {prefix})" if prefix else "Cache entièrement vidé"
            logger.info(message)
            
            return jsonify({
                'message': message,
                'success': True
            }), 200
            
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {str(e)}")
            return jsonify({
                'error': 'Erreur lors du vidage du cache',
                'message': str(e)
            }), 500
    
    # Route de santé
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Endpoint de vérification de santé de l'API
        
        Returns:
            200: API fonctionnelle
        """
        return jsonify({
            'status': 'healthy',
            'message': 'API Fast-Food opérationnelle',
            'version': '1.0.0'
        }), 200
    
    # Route racine
    @app.route('/', methods=['GET'])
    def index():
        """
        Page d'accueil de l'API avec documentation de base
        
        Returns:
            200: Informations sur l'API
        """
        return jsonify({
            'message': 'Bienvenue sur l\'API Fast-Food',
            'brands': ['Planète Kebab', 'MamaPizza'],
            'endpoints': {
                'products': {
                    'GET /products': 'Liste tous les produits (filtrage par brand, category, available)',
                    'GET /products/<id>': 'Détails d\'un produit',
                    'POST /products': 'Créer un produit (API key requise)',
                    'PUT /products/<id>': 'Modifier un produit (API key requise)',
                    'DELETE /products/<id>': 'Supprimer un produit (API key requise)'
                },
                'orders': {
                    'GET /orders': 'Liste toutes les commandes (filtrage par status)',
                    'GET /orders/<id>': 'Détails d\'une commande',
                    'POST /orders': 'Créer une commande (API key requise)',
                    'PUT /orders/<id>': 'Mettre à jour le statut (API key requise)'
                },
                'admin': {
                    'POST /cache/clear': 'Vider le cache (API key requise)',
                    'GET /health': 'Vérification de santé'
                }
            },
            'documentation': 'Utilisez Postman avec la collection fournie pour tester l\'API'
        }), 200
    
    # Gestionnaires d'erreurs globaux
    @app.errorhandler(400)
    def bad_request(e):
        """Gestion des erreurs 400 Bad Request"""
        return jsonify({
            'error': 'Requête invalide',
            'message': str(e)
        }), 400
    
    @app.errorhandler(404)
    def not_found(e):
        """Gestion des erreurs 404 Not Found"""
        return jsonify({
            'error': 'Ressource non trouvée',
            'message': 'L\'endpoint demandé n\'existe pas'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """Gestion des erreurs 405 Method Not Allowed"""
        return jsonify({
            'error': 'Méthode non autorisée',
            'message': 'La méthode HTTP utilisée n\'est pas autorisée pour cet endpoint'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(e):
        """Gestion des erreurs 500 Internal Server Error"""
        logger.error(f"Erreur interne du serveur: {str(e)}")
        return jsonify({
            'error': 'Erreur interne du serveur',
            'message': 'Une erreur inattendue s\'est produite'
        }), 500
    
    logger.info("Application Flask configurée avec succès")
    
    return app


# Créer l'instance de l'application pour Gunicorn
app = create_app()

# Point d'entrée pour le mode développement
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
