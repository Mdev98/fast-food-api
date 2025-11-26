"""
Utilitaires pour la gestion des images avec compression locale
"""
import logging
import os
import uuid
import requests
from io import BytesIO
from base64 import b64decode
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
STATIC_FOLDER = Path(__file__).parent.parent / 'static'
PRODUCTS_FOLDER = STATIC_FOLDER / 'products'
MAX_WIDTH = 800
QUALITY = 85
OUTPUT_FORMAT = 'WEBP'


def ensure_products_folder():
    """Crée le dossier ./static/products/ s'il n'existe pas"""
    try:
        PRODUCTS_FOLDER.mkdir(parents=True, exist_ok=True)
        logger.info(f"Dossier images assuré: {PRODUCTS_FOLDER}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du dossier: {str(e)}")
        return False


def generate_filename(product_id: int) -> str:
    """
    Génère un nom de fichier unique pour une image de produit
    
    Args:
        product_id: ID du produit
        
    Returns:
        Nom du fichier: product_{product_id}_{random_4_chars}.webp
    """
    random_suffix = str(uuid.uuid4())[:4]
    return f"product_{product_id}_{random_suffix}.webp"


def compress_image(image_obj: Image.Image) -> Image.Image:
    """
    Compresse une image PIL en redimensionnant et en optimisant la qualité
    
    Args:
        image_obj: Objet Image PIL
        
    Returns:
        Image compressée
    """
    # Redimensionner si largeur > MAX_WIDTH
    if image_obj.width > MAX_WIDTH:
        ratio = MAX_WIDTH / image_obj.width
        new_height = int(image_obj.height * ratio)
        image_obj = image_obj.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
        logger.info(f"Image redimensionnée: {MAX_WIDTH}x{new_height}")
    
    # Convertir RGBA en RGB si nécessaire (WebP ne supporte pas RGBA bien avec la qualité)
    if image_obj.mode in ('RGBA', 'LA', 'P'):
        # Créer un fond blanc
        background = Image.new('RGB', image_obj.size, (255, 255, 255))
        if image_obj.mode == 'P':
            image_obj = image_obj.convert('RGBA')
        background.paste(image_obj, mask=image_obj.split()[-1] if image_obj.mode == 'RGBA' else None)
        image_obj = background
    elif image_obj.mode != 'RGB':
        image_obj = image_obj.convert('RGB')
    
    return image_obj


def download_and_compress(url: str, product_id: int, base_url: str = '') -> dict | None:
    """
    Télécharge une image depuis une URL externe, la compresse et la sauvegarde localement
    
    Args:
        url: URL externe de l'image (http/https)
        product_id: ID du produit
        base_url: URL de base du serveur (auto-détection si vide)
        
    Returns:
        Dict avec 'filename' et 'public_url' ou None en cas d'erreur
    """
    try:
        # Auto-détection de base_url si vide
        if not base_url:
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except RuntimeError:
                base_url = 'http://localhost:5000'
        
        # Télécharger l'image
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Ouvrir comme image PIL
        image_obj = Image.open(BytesIO(response.content))
        logger.info(f"Image téléchargée: {url} ({image_obj.size})")
        
        # Compresser
        image_obj = compress_image(image_obj)
        
        # Générer le nom de fichier
        filename = generate_filename(product_id)
        filepath = PRODUCTS_FOLDER / filename
        
        # Sauvegarder
        image_obj.save(filepath, OUTPUT_FORMAT, quality=QUALITY, optimize=True)
        logger.info(f"Image sauvegardée: {filepath}")
        
        # Construire l'URL publique
        public_url = f"{base_url}/static/products/{filename}"
        
        return {
            'filename': filename,
            'public_url': public_url
        }
        
    except requests.RequestException as e:
        logger.error(f"Erreur téléchargement image: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Erreur traitement image: {str(e)}")
        return None


def compress_from_base64(base64_string: str, product_id: int, base_url: str = '') -> dict | None:
    """
    Décode une image en base64, la compresse et la sauvegarde localement
    
    Args:
        base64_string: Chaîne base64 de l'image (peut inclure le préfixe data:)
        product_id: ID du produit
        base_url: URL de base du serveur (auto-détection si vide)
        
    Returns:
        Dict avec 'filename' et 'public_url' ou None en cas d'erreur
    """
    try:
        # Auto-détection de base_url si vide
        if not base_url:
            try:
                from flask import request
                base_url = request.host_url.rstrip('/')
            except RuntimeError:
                base_url = 'http://localhost:5000'
        
        # Supprimer le préfixe data: si présent
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Décoder
        image_data = b64decode(base64_string)
        image_obj = Image.open(BytesIO(image_data))
        logger.info(f"Image base64 décodée ({image_obj.size})")
        
        # Compresser
        image_obj = compress_image(image_obj)
        
        # Générer le nom de fichier
        filename = generate_filename(product_id)
        filepath = PRODUCTS_FOLDER / filename
        
        # Sauvegarder
        image_obj.save(filepath, OUTPUT_FORMAT, quality=QUALITY, optimize=True)
        logger.info(f"Image sauvegardée: {filepath}")
        
        # Construire l'URL publique
        public_url = f"{base_url}/static/products/{filename}"
        
        return {
            'filename': filename,
            'public_url': public_url
        }
        
    except Exception as e:
        logger.error(f"Erreur décodage base64: {str(e)}")
        return None


def delete_local_image(filename: str) -> bool:
    """
    Supprime une image locale
    
    Args:
        filename: Nom du fichier à supprimer
        
    Returns:
        True si suppression réussie, False sinon
    """
    try:
        filepath = PRODUCTS_FOLDER / filename
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Image supprimée: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Erreur suppression image: {str(e)}")
        return False


def extract_filename_from_url(image_url: str) -> str | None:
    """
    Extrait le nom du fichier depuis une URL de static/products/
    
    Args:
        image_url: URL complète
        
    Returns:
        Nom du fichier ou None
    """
    if '/static/products/' in image_url:
        return image_url.split('/static/products/')[-1]
    return None
