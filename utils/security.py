"""
Utilitaires de sécurité pour l'API
"""
import logging
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    Décorateur pour protéger les routes avec une clé API
    
    Vérifie la présence et la validité du header X-API-KEY
    Retourne 401 si la clé est manquante ou invalide
    
    Usage:
        @app.route('/protected')
        @require_api_key
        def protected_route():
            return jsonify({'message': 'Accès autorisé'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Récupérer la clé API du header
        api_key = request.headers.get('X-API-KEY')
        
        # Vérifier si la clé est présente
        if not api_key:
            logger.warning(f"Tentative d'accès sans clé API à {request.path}")
            return jsonify({
                'error': 'API key manquante',
                'message': 'Le header X-API-KEY est requis'
            }), 401
        
        # Vérifier si la clé est valide
        valid_api_key = current_app.config.get('ADMIN_API_KEY')
        if api_key != valid_api_key:
            logger.warning(f"Tentative d'accès avec clé API invalide à {request.path}")
            return jsonify({
                'error': 'API key invalide',
                'message': 'La clé API fournie n\'est pas valide'
            }), 401
        
        # Clé valide, continuer
        logger.debug(f"Accès autorisé à {request.path}")
        return f(*args, **kwargs)
    
    return decorated_function


def public_route(f):
    """
    Décorateur pour marquer explicitement une route comme publique
    (pas de vérification de clé API)
    
    Usage:
        @app.route('/public')
        @public_route
        def public_route():
            return jsonify({'message': 'Route publique'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorated_function


def validate_json_content_type(f):
    """
    Décorateur pour valider que le Content-Type est application/json
    pour les requêtes POST/PUT/PATCH
    
    Usage:
        @app.route('/api', methods=['POST'])
        @validate_json_content_type
        def api_route():
            return jsonify({'message': 'OK'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                logger.warning(
                    f"Tentative d'envoi de données non-JSON à {request.path}"
                )
                return jsonify({
                    'error': 'Content-Type invalide',
                    'message': 'Le Content-Type doit être application/json'
                }), 415
        
        return f(*args, **kwargs)
    
    return decorated_function


def log_request_info():
    """
    Log les informations de la requête (méthode, path, IP)
    À appeler dans un before_request hook
    """
    logger.info(
        f"{request.method} {request.path} - "
        f"IP: {request.remote_addr} - "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """
    Nettoie et sécurise une entrée utilisateur
    
    Args:
        data: Données à nettoyer
        max_length: Longueur maximale autorisée
        
    Returns:
        Données nettoyées
    """
    if not data:
        return ""
    
    # Limiter la longueur
    sanitized = str(data)[:max_length]
    
    # Supprimer les caractères de contrôle dangereux
    sanitized = sanitized.strip()
    
    return sanitized
