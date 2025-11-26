"""
Modèles de données pour l'application Fast-Food API
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Enum
import enum

db = SQLAlchemy()


def utc_now():
    """Retourne l'heure actuelle en UTC (timezone-aware)"""
    return datetime.now(timezone.utc)


class BrandEnum(enum.Enum):
    """Énumération des marques disponibles"""
    PLANETE_KEBAB = "planete_kebab"
    MAMAPIZZA = "mamapizza"


class OrderStatusEnum(enum.Enum):
    """Énumération des statuts de commande"""
    RECEIVED = "received"
    PREPARED = "prepared"
    DELIVERED = "delivered"


class Country(db.Model):
    """
    Modèle pour les pays UEMOA
    
    Attributs:
        id: Identifiant unique
        code: Code ISO 2 lettres (SN, CI, ML, BF, etc.)
        name: Nom du pays en français
    """
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(2), unique=True, nullable=False)  # "SN", "CI", etc.
    name = db.Column(db.String(100), nullable=False)  # "Sénégal", "Côte d'Ivoire", etc.
    
    # Relations
    brands = db.relationship('Brand', back_populates='country')
    
    def __repr__(self):
        return f'<Country {self.code} - {self.name}>'
    
    def to_dict(self):
        """Convertit le pays en dictionnaire"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class Brand(db.Model):
    """
    Modèle pour les marques/restaurants
    
    Attributs:
        id: Identifiant unique
        name: Nom de la marque
        country_id: ID du pays (chaque restaurant appartient à un pays UEMOA)
    """
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    
    # Relations
    country = db.relationship('Country', back_populates='brands')
    
    def __repr__(self):
        return f'<Brand {self.name}>'
    
    def to_dict(self):
        """Convertit la marque en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'country_id': self.country_id,
            'country': self.country.to_dict() if self.country else None
        }


class Product(db.Model):
    """
    Modèle pour les produits du menu
    
    Attributs:
        id: Identifiant unique du produit
        name: Nom du produit
        description: Description détaillée
        price: Prix du produit en FCFA (entier, sans décimales)
        image_url: URL de l'image du produit
        category: Catégorie (pizza, kebab, boisson, etc.)
        available: Disponibilité du produit
        brand: Marque (planete_kebab ou mamapizza)
        available_in_countries: Liste de codes pays où le produit est disponible (["SN", "CI"])
        created_at: Date de création
        updated_at: Date de dernière modification
    """
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)  # Price in FCFA (integer) – 2500 = 2 500 FCFA
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(50), nullable=False)
    available = db.Column(db.Boolean, default=True, nullable=False)
    brand = db.Column(
        db.Enum(BrandEnum),
        nullable=False
    )
    available_in_countries = db.Column(db.JSON, default=lambda: ["SN"], nullable=False)  # ["SN", "CI"]
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    # Contraintes
    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
    )
    
    def __repr__(self):
        return f'<Product {self.name} - {self.brand.value}>'
    
    def to_dict(self):
        """Convertit le produit en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,  # Retourner comme entier
            'image_url': self.image_url,
            'category': self.category,
            'available': self.available,
            'brand': self.brand.value,
            'available_in_countries': self.available_in_countries,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Order(db.Model):
    """
    Modèle pour les commandes clients
    
    Attributs:
        id: Identifiant unique de la commande
        customer_name: Nom du client
        mobile: Numéro de téléphone du client
        address: Adresse de livraison
        details: Détails supplémentaires de la commande (préférences, instructions)
        items: Liste des articles commandés (JSON)
        total: Montant total de la commande en FCFA (entier)
        status: Statut de la commande
        created_at: Date de création
        updated_at: Date de dernière modification
    """
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)  # Préférences: sans tomates, avec piment, etc.
    items = db.Column(db.JSON, nullable=False)  # Liste d'objets {product_id, name, unit_price, quantity, subtotal}
    total = db.Column(db.Integer, nullable=False)  # Total in FCFA (integer)
    status = db.Column(
        db.Enum(OrderStatusEnum),
        default=OrderStatusEnum.RECEIVED,
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    # Contraintes
    __table_args__ = (
        CheckConstraint('total >= 0', name='check_total_positive'),
    )
    
    def __repr__(self):
        return f'<Order #{self.id} - {self.customer_name} - {self.total} FCFA>'
    
    def to_dict(self):
        """Convertit la commande en dictionnaire"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'mobile': self.mobile,
            'address': self.address,
            'details': self.details,
            'items': self.items,
            'total': self.total,  # Retourner comme entier
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

