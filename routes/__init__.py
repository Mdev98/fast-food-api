"""
Fichier __init__.py pour le package routes
"""
from .products import products_bp
from .orders import orders_bp

__all__ = ['products_bp', 'orders_bp']
