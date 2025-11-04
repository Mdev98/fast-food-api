"""
Script d'initialisation de la base de données
Crée la base et insère des données d'exemple pour les deux marques
"""
import os
import sys
from decimal import Decimal

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Product, BrandEnum

# Données d'exemple basées sur les catalogues des fast-foods
SAMPLE_PRODUCTS = [
    # Planète Kebab - Kebabs et sandwichs
    {
        'name': 'Kebab Complet',
        'description': 'Kebab avec viande, salade, tomates, oignons, sauce blanche',
        'price': Decimal('7.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Kebab+Complet',
        'category': 'Kebabs',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    {
        'name': 'Kebab Galette',
        'description': 'Kebab dans une galette turque avec crudités et sauce',
        'price': Decimal('8.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Kebab+Galette',
        'category': 'Kebabs',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    {
        'name': 'Tacos 3 Viandes',
        'description': 'Tacos avec poulet, kebab, merguez, frites et sauce fromagère',
        'price': Decimal('9.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Tacos+3+Viandes',
        'category': 'Tacos',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    {
        'name': 'Sandwich Poulet',
        'description': 'Sandwich au poulet grillé avec crudités',
        'price': Decimal('6.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Sandwich+Poulet',
        'category': 'Sandwichs',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    {
        'name': 'Assiette Kebab',
        'description': 'Assiette complète avec viande kebab, frites, salade et sauce',
        'price': Decimal('11.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Assiette+Kebab',
        'category': 'Assiettes',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    {
        'name': 'Coca-Cola 33cl',
        'description': 'Canette Coca-Cola 33cl',
        'price': Decimal('2.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Coca-Cola',
        'category': 'Boissons',
        'available': True,
        'brand': BrandEnum.PLANETE_KEBAB
    },
    
    # MamaPizza - Pizzas et accompagnements
    {
        'name': 'Pizza Margherita',
        'description': 'Pizza classique avec sauce tomate, mozzarella et basilic',
        'price': Decimal('9.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Pizza+Margherita',
        'category': 'Pizzas',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Pizza Regina',
        'description': 'Pizza avec sauce tomate, mozzarella, jambon et champignons',
        'price': Decimal('10.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Pizza+Regina',
        'category': 'Pizzas',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Pizza 4 Fromages',
        'description': 'Pizza avec mozzarella, gorgonzola, chèvre et emmental',
        'price': Decimal('11.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Pizza+4+Fromages',
        'category': 'Pizzas',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Pizza Calzone',
        'description': 'Pizza pliée farcie de jambon, champignons et mozzarella',
        'price': Decimal('12.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Pizza+Calzone',
        'category': 'Pizzas',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Pizza Végétarienne',
        'description': 'Pizza avec légumes grillés, mozzarella et basilic',
        'price': Decimal('10.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Pizza+Vegetarienne',
        'category': 'Pizzas',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Tiramisu',
        'description': 'Tiramisu maison au mascarpone et café',
        'price': Decimal('4.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Tiramisu',
        'category': 'Desserts',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Panna Cotta',
        'description': 'Panna cotta avec coulis de fruits rouges',
        'price': Decimal('4.00'),
        'image_url': 'https://via.placeholder.com/300x200?text=Panna+Cotta',
        'category': 'Desserts',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    },
    {
        'name': 'Limonade Artisanale',
        'description': 'Limonade maison 50cl',
        'price': Decimal('3.50'),
        'image_url': 'https://via.placeholder.com/300x200?text=Limonade',
        'category': 'Boissons',
        'available': True,
        'brand': BrandEnum.MAMAPIZZA
    }
]


def init_database():
    """
    Initialise la base de données et insère les données d'exemple
    """
    print("=" * 80)
    print("🚀 INITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    # Créer l'application
    app = create_app('development')
    
    with app.app_context():
        # Vérifier si des produits existent déjà
        existing_count = Product.query.count()
        
        if existing_count > 0:
            print(f"\n⚠️  La base contient déjà {existing_count} produit(s).")
            response = input("Voulez-vous réinitialiser la base ? (o/n) : ")
            
            if response.lower() == 'o':
                print("\n🗑️  Suppression des données existantes...")
                db.drop_all()
                db.create_all()
                print("✅ Base de données réinitialisée")
            else:
                print("\n❌ Opération annulée")
                return
        else:
            print("\n✅ Base de données vide détectée")
            db.create_all()
        
        # Insérer les produits d'exemple
        print(f"\n📦 Insertion de {len(SAMPLE_PRODUCTS)} produits...")
        
        planete_count = 0
        mama_count = 0
        
        for product_data in SAMPLE_PRODUCTS:
            product = Product(**product_data)
            db.session.add(product)
            
            if product_data['brand'] == BrandEnum.PLANETE_KEBAB:
                planete_count += 1
            else:
                mama_count += 1
            
            print(f"  ✓ {product_data['name']} ({product_data['brand'].value})")
        
        try:
            db.session.commit()
            print(f"\n✅ {len(SAMPLE_PRODUCTS)} produits insérés avec succès !")
            print(f"   • Planète Kebab : {planete_count} produits")
            print(f"   • MamaPizza : {mama_count} produits")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de l'insertion : {str(e)}")
            return
    
    print("\n" + "=" * 80)
    print("🎉 INITIALISATION TERMINÉE AVEC SUCCÈS")
    print("=" * 80)
    print("\n💡 Vous pouvez maintenant démarrer l'API avec : flask run")
    print("   ou : python app.py\n")


if __name__ == '__main__':
    init_database()
