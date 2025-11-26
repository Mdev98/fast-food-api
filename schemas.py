"""
Schémas de validation pour l'API Fast-Food
Utilise Marshmallow pour la sérialisation et la validation des données
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load, pre_dump
from models import BrandEnum, OrderStatusEnum
import re


class EnumField(fields.Field):
    """Champ personnalisé pour gérer les enums"""
    
    def __init__(self, enum_class, *args, **kwargs):
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
    
    def _serialize(self, value, attr, obj, **kwargs):
        """Convertit l'enum en string pour la sérialisation"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value
    
    def _deserialize(self, value, attr, data, **kwargs):
        """Convertit le string en enum pour la désérialisation"""
        try:
            if isinstance(value, str):
                return self.enum_class(value)
            return value
        except ValueError:
            raise ValidationError(f"Invalid value for {self.enum_class.__name__}")


class ProductSchema(Schema):
    """
    Schéma de validation pour les produits
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    price = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Le prix (FCFA) doit être positif")
    )
    image_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    category = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50)
    )
    available = fields.Bool(load_default=True)
    brand = EnumField(
        BrandEnum,
        required=True
    )
    available_in_countries = fields.List(
        fields.Str(validate=validate.Length(equal=2)),
        load_default=["SN"]
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('brand')
    def validate_brand(self, value):
        """Valide que la marque est correcte"""
        valid_values = [b.value for b in BrandEnum]
        if isinstance(value, str) and value not in valid_values:
            raise ValidationError(f"La marque doit être parmi: {', '.join(valid_values)}")
        elif isinstance(value, BrandEnum):
            return  # Déjà validé
    
    @validates('price')
    def validate_price(self, value):
        """Valide que le prix (FCFA) est positif"""
        if value <= 0:
            raise ValidationError("Le prix doit être supérieur à 0")


class OrderItemSchema(Schema):
    """
    Schéma pour les articles d'une commande
    """
    product_id = fields.Int(required=True)
    name = fields.Str(dump_only=True)
    unit_price = fields.Int(dump_only=True)  # Price in FCFA (integer)
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="La quantité doit être au moins 1")
    )
    subtotal = fields.Int(dump_only=True)  # Subtotal in FCFA (integer)


class OrderCreateSchema(Schema):
    """
    Schéma de validation pour la création de commandes
    """
    customer_name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100, error="Le nom du client est requis")
    )
    mobile = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=20, error="Numéro de téléphone invalide")
    )
    address = fields.Str(
        required=True,
        validate=validate.Length(min=5, error="L'adresse est requise")
    )
    details = fields.Str(
        allow_none=True,
        validate=validate.Length(max=500, error="Les détails sont trop longs (max 500 caractères)")
    )
    items = fields.List(
        fields.Nested(OrderItemSchema),
        required=True,
        validate=validate.Length(min=1, error="Au moins un article est requis")
    )
    
    @validates('mobile')
    def validate_mobile(self, value):
        """
        Valide le format du numéro de téléphone
        Accepte les formats internationaux comme +33XXXXXXXXX
        """
        # Pattern pour numéro international ou local
        pattern = r'^\+?[1-9]\d{8,14}$'
        if not re.match(pattern, value.replace(' ', '').replace('-', '')):
            raise ValidationError(
                "Format de numéro de téléphone invalide. "
                "Utilisez un format international (ex: +33612345678)"
            )


class OrderSchema(Schema):
    """
    Schéma complet pour les commandes (lecture)
    """
    id = fields.Int(dump_only=True)
    customer_name = fields.Str(required=True)
    mobile = fields.Str(required=True)
    address = fields.Str(required=True)
    details = fields.Str(allow_none=True)
    items = fields.List(fields.Nested(OrderItemSchema))
    total = fields.Int(dump_only=True)  # Total in FCFA (integer)
    status = EnumField(OrderStatusEnum)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class OrderUpdateSchema(Schema):
    """
    Schéma pour la mise à jour du statut d'une commande
    """
    status = fields.Str(
        required=True,
        validate=validate.OneOf(
            [status.value for status in OrderStatusEnum],
            error="Statut invalide. Valeurs acceptées: received, prepared, delivered"
        )
    )


class PaginationSchema(Schema):
    """
    Schéma pour les paramètres de pagination
    """
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    limit = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))


# Instances des schémas pour réutilisation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_create_schema = OrderCreateSchema()
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
order_update_schema = OrderUpdateSchema()

pagination_schema = PaginationSchema()
