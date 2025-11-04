"""
Tests unitaires pour l'API Fast-Food
"""
import pytest
import json
from decimal import Decimal

from app import create_app
from models import db, Product, Order, BrandEnum, OrderStatusEnum


@pytest.fixture
def app():
    """Fixture pour créer une instance de l'application en mode test"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture pour créer un client de test"""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Fixture pour les headers d'authentification"""
    return {
        'X-API-KEY': app.config['ADMIN_API_KEY'],
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_product(app):
    """Fixture pour créer un produit d'exemple"""
    with app.app_context():
        product = Product(
            name='Pizza Test',
            description='Pizza de test',
            price=Decimal('10.00'),
            image_url='https://example.com/pizza.jpg',
            category='Pizzas',
            available=True,
            brand=BrandEnum.MAMAPIZZA
        )
        db.session.add(product)
        db.session.commit()
        return product.id


class TestHealthCheck:
    """Tests pour l'endpoint de santé"""
    
    def test_health_check(self, client):
        """Test de l'endpoint /health"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestProductsEndpoints:
    """Tests pour les endpoints de gestion des produits"""
    
    def test_get_products_empty(self, client):
        """Test GET /products avec base vide"""
        response = client.get('/products')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert len(data['products']) == 0
    
    def test_create_product_success(self, client, auth_headers):
        """Test POST /products avec données valides"""
        product_data = {
            'name': 'Pizza Margherita',
            'description': 'Pizza classique',
            'price': '9.00',
            'category': 'Pizzas',
            'brand': 'mamapizza',
            'available': True
        }
        
        response = client.post(
            '/products',
            data=json.dumps(product_data),
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Produit créé avec succès'
        assert data['product']['name'] == 'Pizza Margherita'
    
    def test_create_product_missing_api_key(self, client):
        """Test POST /products sans clé API"""
        product_data = {
            'name': 'Pizza Test',
            'price': '10.00',
            'category': 'Pizzas',
            'brand': 'mamapizza'
        }
        
        response = client.post(
            '/products',
            data=json.dumps(product_data),
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 401
    
    def test_create_product_invalid_data(self, client, auth_headers):
        """Test POST /products avec données invalides"""
        product_data = {
            'name': 'Test',
            'price': '-10.00',  # Prix négatif (invalide)
            'category': 'Test',
            'brand': 'invalid_brand'
        }
        
        response = client.post(
            '/products',
            data=json.dumps(product_data),
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_get_product_by_id(self, client, sample_product):
        """Test GET /products/<id>"""
        response = client.get(f'/products/{sample_product}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_product
        assert data['name'] == 'Pizza Test'
    
    def test_get_product_not_found(self, client):
        """Test GET /products/<id> avec ID inexistant"""
        response = client.get('/products/9999')
        assert response.status_code == 404
    
    def test_update_product(self, client, auth_headers, sample_product):
        """Test PUT /products/<id>"""
        update_data = {
            'name': 'Pizza Test Modifiée',
            'price': '12.00'
        }
        
        response = client.put(
            f'/products/{sample_product}',
            data=json.dumps(update_data),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product']['name'] == 'Pizza Test Modifiée'
        assert float(data['product']['price']) == 12.00
    
    def test_delete_product(self, client, auth_headers, sample_product):
        """Test DELETE /products/<id>"""
        response = client.delete(
            f'/products/{sample_product}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Vérifier que le produit n'existe plus
        response = client.get(f'/products/{sample_product}')
        assert response.status_code == 404
    
    def test_filter_products_by_brand(self, client, auth_headers):
        """Test filtrage des produits par marque"""
        # Créer des produits de différentes marques
        products = [
            {
                'name': 'Kebab',
                'price': '7.50',
                'category': 'Kebabs',
                'brand': 'planete_kebab'
            },
            {
                'name': 'Pizza',
                'price': '10.00',
                'category': 'Pizzas',
                'brand': 'mamapizza'
            }
        ]
        
        for product in products:
            response = client.post(
                '/products',
                data=json.dumps(product),
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # Filtrer par marque
        response = client.get('/products?brand=planete_kebab')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) >= 1
        # Vérifier que tous les produits retournés sont de la bonne marque
        for product in data['products']:
            assert product['brand'] == 'planete_kebab'


class TestOrdersEndpoints:
    """Tests pour les endpoints de gestion des commandes"""
    
    def test_create_order_success(self, client, auth_headers, sample_product):
        """Test POST /orders avec données valides"""
        order_data = {
            'customer_name': 'John Doe',
            'mobile': '+33612345678',
            'address': '123 Rue de Test, 75001 Paris',
            'details': 'Sans oignons, avec piment',
            'items': [
                {
                    'product_id': sample_product,
                    'quantity': 2
                }
            ]
        }
        
        response = client.post(
            '/orders',
            data=json.dumps(order_data),
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Commande créée avec succès'
        assert data['order']['customer_name'] == 'John Doe'
        assert data['order']['details'] == 'Sans oignons, avec piment'
        assert float(data['order']['total']) == 20.00  # 2 x 10.00
    
    def test_create_order_invalid_product(self, client, auth_headers):
        """Test POST /orders avec produit inexistant"""
        order_data = {
            'customer_name': 'John Doe',
            'mobile': '+33612345678',
            'address': '123 Rue de Test',
            'items': [
                {
                    'product_id': 9999,  # Produit inexistant
                    'quantity': 1
                }
            ]
        }
        
        response = client.post(
            '/orders',
            data=json.dumps(order_data),
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_create_order_invalid_phone(self, client, auth_headers, sample_product):
        """Test POST /orders avec numéro de téléphone invalide"""
        order_data = {
            'customer_name': 'John Doe',
            'mobile': '123',  # Numéro invalide
            'address': '123 Rue de Test',
            'items': [
                {
                    'product_id': sample_product,
                    'quantity': 1
                }
            ]
        }
        
        response = client.post(
            '/orders',
            data=json.dumps(order_data),
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_get_orders(self, client, auth_headers, sample_product):
        """Test GET /orders"""
        # Créer une commande
        order_data = {
            'customer_name': 'Jane Doe',
            'mobile': '+33687654321',
            'address': '456 Avenue Test',
            'items': [
                {
                    'product_id': sample_product,
                    'quantity': 1
                }
            ]
        }
        
        client.post(
            '/orders',
            data=json.dumps(order_data),
            headers=auth_headers
        )
        
        # Récupérer toutes les commandes
        response = client.get('/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orders' in data
        assert len(data['orders']) == 1
    
    def test_update_order_status(self, client, auth_headers, sample_product):
        """Test PUT /orders/<id> pour mettre à jour le statut"""
        # Créer une commande
        order_data = {
            'customer_name': 'Test User',
            'mobile': '+33611223344',
            'address': '789 Boulevard Test',
            'items': [
                {
                    'product_id': sample_product,
                    'quantity': 1
                }
            ]
        }
        
        response = client.post(
            '/orders',
            data=json.dumps(order_data),
            headers=auth_headers
        )
        
        order_id = json.loads(response.data)['order']['id']
        
        # Mettre à jour le statut
        update_data = {
            'status': 'prepared'
        }
        
        response = client.put(
            f'/orders/{order_id}',
            data=json.dumps(update_data),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['order']['status'] == 'prepared'
    
    def test_filter_orders_by_status(self, client, auth_headers, sample_product):
        """Test filtrage des commandes par statut"""
        # Créer deux commandes
        for i in range(2):
            order_data = {
                'customer_name': f'User {i}',
                'mobile': f'+3361122334{i}',
                'address': f'Address {i}',
                'items': [
                    {
                        'product_id': sample_product,
                        'quantity': 1
                    }
                ]
            }
            client.post(
                '/orders',
                data=json.dumps(order_data),
                headers=auth_headers
            )
        
        # Filtrer par statut
        response = client.get('/orders?status=received')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['orders']) == 2


class TestCacheEndpoint:
    """Tests pour l'endpoint de gestion du cache"""
    
    def test_clear_cache(self, client, auth_headers):
        """Test POST /cache/clear"""
        response = client.post(
            '/cache/clear',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_clear_cache_without_auth(self, client):
        """Test POST /cache/clear sans authentification"""
        response = client.post('/cache/clear')
        assert response.status_code == 401


class TestErrorHandlers:
    """Tests pour les gestionnaires d'erreurs"""
    
    def test_404_not_found(self, client):
        """Test erreur 404"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
