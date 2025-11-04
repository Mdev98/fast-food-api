#!/usr/bin/env python
"""
Script pour initialiser la base de données en production (Render)
"""
import os
import sys
from app import app, db
from models import Product, Order, BrandEnum

def init_production_db():
    """Initialise la base de données avec des données de base"""
    with app.app_context():
        print("🔄 Création des tables...")
        db.create_all()
        print("✅ Tables créées avec succès!")
        
        # Vérifier si des produits existent déjà
        existing_products = Product.query.count()
        if existing_products > 0:
            print(f"ℹ️  La base contient déjà {existing_products} produits. Pas d'initialisation.")
            return
        
        print("📦 Ajout des produits de démonstration...")
        
        # Produits Planète Kebab
        kebab_products = [
            {
                'name': 'Kebab Classique',
                'description': 'Kebab avec viande, salade, tomate, oignon',
                'price': 6.50,
                'category': 'Kebabs',
                'brand': BrandEnum.PLANETE_KEBAB,
                'available': True,
                'image_url': 'https://example.com/kebab-classique.jpg'
            },
            {
                'name': 'Kebab Complet',
                'description': 'Kebab avec frites et sauce au choix',
                'price': 8.00,
                'category': 'Kebabs',
                'brand': BrandEnum.PLANETE_KEBAB,
                'available': True,
                'image_url': 'https://example.com/kebab-complet.jpg'
            },
            {
                'name': 'Tacos Poulet',
                'description': 'Tacos garni de poulet, frites et sauce fromagère',
                'price': 7.50,
                'category': 'Tacos',
                'brand': BrandEnum.PLANETE_KEBAB,
                'available': True,
                'image_url': 'https://example.com/tacos-poulet.jpg'
            },
            {
                'name': 'Assiette Kebab',
                'description': 'Viande kebab servie avec frites et salade',
                'price': 9.00,
                'category': 'Assiettes',
                'brand': BrandEnum.PLANETE_KEBAB,
                'available': True,
                'image_url': 'https://example.com/assiette-kebab.jpg'
            },
            {
                'name': 'Coca-Cola',
                'description': 'Boisson gazeuse 33cl',
                'price': 2.00,
                'category': 'Boissons',
                'brand': BrandEnum.PLANETE_KEBAB,
                'available': True,
                'image_url': 'https://example.com/coca.jpg'
            }
        ]
        
        # Produits MamaPizza
        pizza_products = [
            {
                'name': 'Pizza Margherita',
                'description': 'Sauce tomate, mozzarella, basilic',
                'price': 9.00,
                'category': 'Pizzas',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/margherita.jpg'
            },
            {
                'name': 'Pizza Reine',
                'description': 'Sauce tomate, mozzarella, jambon, champignons',
                'price': 11.00,
                'category': 'Pizzas',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/reine.jpg'
            },
            {
                'name': 'Pizza 4 Fromages',
                'description': 'Mozzarella, gorgonzola, chèvre, emmental',
                'price': 12.00,
                'category': 'Pizzas',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/4fromages.jpg'
            },
            {
                'name': 'Pizza Calzone',
                'description': 'Pizza pliée garnie de jambon, champignons et mozzarella',
                'price': 11.50,
                'category': 'Pizzas',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/calzone.jpg'
            },
            {
                'name': 'Tiramisu',
                'description': 'Dessert italien au café et mascarpone',
                'price': 5.00,
                'category': 'Desserts',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/tiramisu.jpg'
            },
            {
                'name': 'Salade César',
                'description': 'Salade verte, poulet, parmesan, croûtons',
                'price': 8.00,
                'category': 'Salades',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/cesar.jpg'
            },
            {
                'name': 'Limonade',
                'description': 'Boisson rafraîchissante 33cl',
                'price': 2.50,
                'category': 'Boissons',
                'brand': BrandEnum.MAMAPIZZA,
                'available': True,
                'image_url': 'https://example.com/limonade.jpg'
            }
        ]
        
        # Ajouter tous les produits
        all_products = kebab_products + pizza_products
        for product_data in all_products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        print(f"✅ {len(all_products)} produits ajoutés avec succès!")
        print("🎉 Initialisation terminée!")

if __name__ == '__main__':
    try:
        init_production_db()
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {str(e)}")
        sys.exit(1)
