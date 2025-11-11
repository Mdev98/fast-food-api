# 🍕 API Fast-Food - Planète Kebab & MamaPizza

API REST complète pour la gestion d'une chaîne de fast-food avec deux marques : **Planète Kebab** et **MamaPizza**.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Technologies utilisées](#-technologies-utilisées)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Utilisation](#-utilisation)
- [Endpoints API](#-endpoints-api)
- [Intégration Google Sheets](#-intégration-google-sheets)
- [Tests](#-tests)
- [Architecture du projet](#-architecture-du-projet)

---

## ✨ Fonctionnalités

### Gestion des Produits
- ✅ CRUD complet sur les produits (Create, Read, Update, Delete)
- ✅ Filtrage par marque, catégorie et disponibilité
- ✅ Pagination des résultats
- ✅ Support de deux marques : Planète Kebab et MamaPizza
- ✅ **Gestion des images via Cloudinary** (upload, suppression, optimisation automatique)
- ✅ **Upload automatique d'images depuis URL externe** (parfait pour Google Sheets)
- ✅ Cache automatique avec invalidation intelligente
- ✅ **Intégration Google Sheets** via App Script pour gestion CMS

### Gestion des Commandes
- ✅ Création de commandes avec validation automatique
- ✅ Calcul automatique des totaux et sous-totaux
- ✅ Vérification de la disponibilité des produits
- ✅ Mise à jour du statut (received → prepared → delivered)
- ✅ Filtrage par statut

### Notifications SMS
- ✅ SMS de confirmation au client (simulé)
- ✅ SMS de notification au gérant (simulé)
- ✅ Préparé pour intégration avec l'API Intech

### Sécurité & Performance
- ✅ Authentification par clé API (header X-API-KEY)
- ✅ Validation des données avec Marshmallow
- ✅ Cache Redis ou SimpleCache (fallback)
- ✅ CORS configuré pour frontend
- ✅ Logging complet des opérations
- ✅ Gestion des erreurs globale

---

## 🛠 Technologies utilisées

- **Backend**: Flask 3.0
- **Base de données**: SQLite (SQLAlchemy)
- **Validation**: Marshmallow
- **Cache**: Flask-Caching (Redis/SimpleCache)
- **Tests**: Pytest
- **CORS**: Flask-CORS
- **Autres**: python-dotenv, Alembic

---

## 📦 Installation

### Prérequis
- Python 3.11+
- pip
- (Optionnel) Redis pour le cache

### Étapes d'installation

1. **Cloner le projet**
```bash
cd /Users/mamour/Documents/PROJECTS/fast-food-api
```

2. **Créer un environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos propres valeurs
```

5. **Initialiser la base de données**
```bash
python init_db.py
```

---

## ⚙️ Configuration

Créez un fichier `.env` à la racine du projet (basé sur `.env.example`):

```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=votre_cle_secrete_ici

# Database
DATABASE_URL=sqlite:///fastfood.db

# Security
ADMIN_API_KEY=votre_cle_api_ici

# SMS (Intech API)
MANAGER_MOBILE=+33123456789
INTECH_API_ENDPOINT=https://api.intech.com/sms
INTECH_API_KEY=votre_cle
INTECH_API_SECRET=votre_secret

# Cache
CACHE_TTL=600
CACHE_TYPE=SimpleCache
# REDIS_URL=redis://localhost:6379/0  # Décommenter si Redis est utilisé
```

---

## 🚀 Utilisation

### Démarrer le serveur de développement

```bash
# Méthode 1 : Via Flask CLI
flask run

# Méthode 2 : Via Python
python app.py
```

Le serveur démarre sur `http://localhost:5000`

### Vérifier que l'API fonctionne

```bash
curl http://localhost:5000/health
```

Réponse attendue :
```json
{
  "status": "healthy",
  "message": "API Fast-Food opérationnelle",
  "version": "1.0.0"
}
```

---

## 📡 Endpoints API

### Produits

| Méthode | Endpoint | Description | Auth requise |
|---------|----------|-------------|--------------|
| `GET` | `/products` | Liste tous les produits | Non |
| `GET` | `/products/<id>` | Détails d'un produit | Non |
| `POST` | `/products` | Créer un produit | Oui |
| `POST` | `/products/create-with-image` | **🆕 Créer avec upload image auto** | Oui |
| `PUT` | `/products/<id>` | Modifier un produit | Oui |
| `DELETE` | `/products/<id>` | Supprimer un produit | Oui |
| `POST` | `/products/upload-image` | Upload image vers Cloudinary | Oui |
| `DELETE` | `/products/delete-image` | Supprimer image de Cloudinary | Oui |

**Paramètres de filtrage (GET /products)** :
- `brand` : planete_kebab ou mamapizza
- `category` : Nom de la catégorie
- `available` : true ou false
- `page` : Numéro de page (défaut: 1)
- `limit` : Éléments par page (défaut: 10, max: 100)

### Commandes

| Méthode | Endpoint | Description | Auth requise |
|---------|----------|-------------|--------------|
| `GET` | `/orders` | Liste toutes les commandes | Non |
| `GET` | `/orders/<id>` | Détails d'une commande | Non |
| `POST` | `/orders` | Créer une commande | Oui |
| `PUT` | `/orders/<id>` | Mettre à jour le statut | Oui |

**Paramètres de filtrage (GET /orders)** :
- `status` : received, prepared ou delivered
- `page` : Numéro de page
- `limit` : Éléments par page

### Administration

| Méthode | Endpoint | Description | Auth requise |
|---------|----------|-------------|--------------|
| `POST` | `/cache/clear` | Vider le cache | Oui |
| `GET` | `/health` | Vérification de santé | Non |
| `GET` | `/` | Documentation de base | Non |

---

## 📝 Exemples de requêtes

### Créer un produit

```bash
curl -X POST http://localhost:5000/products \
  -H "X-API-KEY: votre_cle_api" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pizza Margherita",
    "description": "Pizza classique avec mozzarella",
    "price": "9.00",
    "category": "Pizzas",
    "brand": "mamapizza",
    "available": true
  }'
```

### Créer une commande

```bash
curl -X POST http://localhost:5000/orders \
  -H "X-API-KEY: votre_cle_api" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "mobile": "+33612345678",
    "address": "123 Rue de Paris, 75001 Paris",
    "details": "Sans oignons, avec supplément piment",
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      },
      {
        "product_id": 3,
        "quantity": 1
      }
    ]
  }'
```

### Mettre à jour le statut d'une commande

```bash
curl -X PUT http://localhost:5000/orders/1 \
  -H "X-API-KEY: votre_cle_api" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "prepared"
  }'
```

### Filtrer les produits par marque

```bash
curl "http://localhost:5000/products?brand=planete_kebab&page=1&limit=10"
```

### Vider le cache

```bash
curl -X POST http://localhost:5000/cache/clear \
  -H "X-API-KEY: votre_cle_api"
```

---

## 📊 Intégration Google Sheets

L'API peut être intégrée avec **Google Sheets** pour gérer vos produits directement depuis une feuille de calcul.

### 🆕 Endpoint optimisé : `POST /products/create-with-image`

Cet endpoint **combine 3 opérations en 1 seule requête** :
1. ✅ Télécharge l'image depuis une URL externe (Google Drive, Imgur, etc.)
2. ✅ Upload automatique sur Cloudinary
3. ✅ Crée le produit avec l'URL Cloudinary optimisée

**Avantages :**
- 1 seule requête HTTP (au lieu de 2)
- Parfait pour Google Apps Script
- Upload automatique sans gestion manuelle
- Image optimisée automatiquement (800x800px, CDN Cloudinary)

### Exemple d'utilisation

```javascript
// Google Apps Script
const payload = {
  name: "Pizza Margherita",
  description: "Pizza classique italienne",
  price: 9.99,
  category: "pizza",
  brand: "mamapizza",
  available: true,
  image_url: "https://drive.google.com/uc?export=view&id=ABC123"  // URL externe
};

const response = UrlFetchApp.fetch("https://votre-api.com/api/products/create-with-image", {
  method: "POST",
  headers: {
    "X-API-KEY": "votre_cle",
    "Content-Type": "application/json"
  },
  payload: JSON.stringify(payload)
});

// Réponse : produit créé avec image_url pointant vers Cloudinary
const result = JSON.parse(response.getContentText());
console.log(result.product.image_url);  // https://res.cloudinary.com/...
```

### 📚 Documentation complète

Consultez **[GOOGLE_SHEETS_INTEGRATION.md](./GOOGLE_SHEETS_INTEGRATION.md)** pour :
- Configuration du script Google Sheets
- Synchronisation bidirectionnelle automatique
- Workflow complet (ajout, modification, suppression)
- Gestion des images depuis Google Drive
- Script complet prêt à l'emploi

---

## 🧪 Tests

### Exécuter tous les tests

```bash
pytest
```

### Exécuter avec couverture de code

```bash
pytest --cov=. --cov-report=html
```

### Exécuter un test spécifique

```bash
pytest tests/test_api.py::TestProductsEndpoints::test_create_product_success -v
```

Les tests couvrent :
- ✅ Création/Lecture/Mise à jour/Suppression de produits
- ✅ Création et gestion de commandes
- ✅ Validation des données
- ✅ Authentification
- ✅ Gestion des erreurs
- ✅ Filtrage et pagination

---

## 🏗 Architecture du projet

```
fast-food-api/
├── app.py                      # Point d'entrée Flask
├── config.py                   # Configuration de l'application
├── models.py                   # Modèles SQLAlchemy
├── schemas.py                  # Schémas Marshmallow
├── init_db.py                  # Script d'initialisation DB
├── requirements.txt            # Dépendances Python
├── .env.example                # Template de configuration
├── README.md                   # Documentation
├── fastfood.postman_collection.json  # Collection Postman
├── routes/
│   ├── __init__.py
│   ├── products.py             # Routes produits
│   └── orders.py               # Routes commandes
├── utils/
│   ├── __init__.py
│   ├── sms.py                  # Utilitaires SMS
│   ├── cache.py                # Gestion du cache
│   └── security.py             # Sécurité et authentification
└── tests/
    ├── __init__.py
    └── test_api.py             # Tests unitaires
```

---

## 📊 Modèles de données

### Product
```python
{
    "id": int,
    "name": str,
    "description": str,
    "price": decimal,
    "image_url": str,
    "category": str,
    "available": bool,
    "brand": enum ("planete_kebab", "mamapizza"),
    "created_at": datetime,
    "updated_at": datetime
}
```

### Order
```python
{
    "id": int,
    "customer_name": str,
    "mobile": str,
    "address": str,
    "details": str (optional),  # Préférences: sans tomates, avec piment, etc.
    "items": [
        {
            "product_id": int,
            "name": str,
            "unit_price": decimal,
            "quantity": int,
            "subtotal": decimal
        }
    ],
    "total": decimal,
    "status": enum ("received", "prepared", "delivered"),
    "created_at": datetime,
    "updated_at": datetime
}
```

---

## 🔐 Sécurité

- **Authentification** : Toutes les routes de modification (POST, PUT, DELETE) requièrent le header `X-API-KEY`
- **Validation** : Toutes les données entrantes sont validées via Marshmallow
- **SQL Injection** : Protection via SQLAlchemy ORM
- **CORS** : Configuré pour permettre les appels depuis le frontend

---

## 📱 Notifications SMS

L'API utilise **IntechSMS** pour l'envoi de SMS aux clients et au gérant.

### Mode développement (Mock)
Par défaut, les SMS sont simulés et affichés dans les logs (pratique pour le développement).

### Mode production (Envoi réel)
Pour activer l'envoi réel de SMS :

1. **Obtenir votre clé API IntechSMS**
   - Créez un compte sur [IntechSMS](https://gateway.intechsms.sn)
   - Récupérez votre `APP_KEY` depuis le dashboard

2. **Configurer le fichier `.env`**
   ```env
   INTECH_API_KEY=votre_app_key_ici
   INTECH_SENDER_ID=FastFood
   SMS_MOCK_MODE=false
   MANAGER_MOBILE=+221777293282
   ```

3. **Installer requests** (si ce n'est pas déjà fait)
   ```bash
   pip install requests==2.31.0
   ```

4. **Redémarrer l'application**
   ```bash
   python app.py
   ```

### Format des numéros
- **Sénégal** : +221XXXXXXXXX (ex: +221777293282)
- **France** : +33XXXXXXXXX (ex: +33612345678)
- **Autres** : Format international avec indicatif pays

### Messages envoyés
- **Client** : Confirmation de commande avec total et adresse
- **Gérant** : Notification de nouvelle commande avec montant

---

## 🧪 Test de l'envoi SMS

Pour tester l'intégration IntechSMS sans créer de commande :

```bash
python test_sms.py
```

Ce script :
- Vérifie la configuration
- Envoie un SMS de test au numéro du gérant
- Affiche la réponse de l'API

## 🐛 Troubleshooting

### Erreur : "Impossible de résoudre l'importation"
```bash
# Installer les dépendances
pip install -r requirements.txt
```

### Erreur : "Table already exists"
```bash
# Réinitialiser la base de données
rm fastfood.db
python init_db.py
```

### Redis non disponible
Le système bascule automatiquement sur SimpleCache si Redis n'est pas disponible.

### SMS non envoyés
1. Vérifier que `INTECH_API_KEY` est correctement configurée
2. Vérifier que `SMS_MOCK_MODE=false` pour l'envoi réel
3. Vérifier le format des numéros (international avec +)
4. Consulter les logs de l'application pour plus de détails

---

## 📚 Collection Postman

### Collection principale
Importez le fichier `fastfood.postman_collection.json` dans Postman pour tester facilement tous les endpoints.

### Collection gestion d'images
Importez le fichier `postman_images_collection.json` pour tester l'upload et la gestion des images.

**Variables à configurer dans Postman :**
- `base_url` : http://localhost:5001
- `api_key` : Votre clé API définie dans `.env`

**Guides disponibles :**
- `IMAGES_GUIDE.md` - Documentation complète de la gestion des images

---

## 👥 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 📧 Contact

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur le projet.

---

**Bon appétit ! 🍕🥙**
