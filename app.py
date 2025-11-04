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
    
    # Créer les tables de base de données
    with app.app_context():
        db.create_all()
        logger.info("Base de données initialisée")
    
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
