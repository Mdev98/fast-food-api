"""
Utilitaires pour la gestion du cache
"""
import logging
from flask_caching import Cache

logger = logging.getLogger(__name__)

# Instance globale du cache
cache = Cache()


def init_cache(app):
    """
    Initialise le système de cache pour l'application Flask
    
    Args:
        app: Instance Flask de l'application
    """
    cache_config = {
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 600)
    }
    
    cache.init_app(app, config=cache_config)
    logger.info(f"Cache initialisé: {cache_config['CACHE_TYPE']}")


def clear_cache(key_prefix: str | None = None):
    """
    Vide le cache (totalement ou pour un préfixe donné)
    
    Args:
        key_prefix: Préfixe des clés à supprimer (None = tout le cache)
        
    Returns:
        True si le cache a été vidé avec succès
    """
    try:
        if key_prefix:
            # Supprimer les clés avec un préfixe spécifique
            cache.delete_memoized(key_prefix)
            logger.info(f"Cache vidé pour le préfixe: {key_prefix}")
        else:
            # Vider tout le cache
            cache.clear()
            logger.info("Cache entièrement vidé")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache: {str(e)}")
        return False


def invalidate_products_cache():
    """
    Invalide le cache des produits
    Utilisé après création/modification/suppression d'un produit
    """
    try:
        # Supprimer toutes les clés liées aux produits
        cache.delete('view//products')
        cache.delete_memoized('get_products')
        logger.info("Cache des produits invalidé")
    except Exception as e:
        logger.warning(f"Impossible d'invalider le cache des produits: {str(e)}")


def invalidate_orders_cache():
    """
    Invalide le cache des commandes
    Utilisé après création/modification d'une commande
    """
    try:
        cache.delete('view//orders')
        cache.delete_memoized('get_orders')
        logger.info("Cache des commandes invalidé")
    except Exception as e:
        logger.warning(f"Impossible d'invalider le cache des commandes: {str(e)}")
