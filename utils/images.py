"""
Utilitaires pour la gestion des images via Cloudinary
"""
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


def init_cloudinary(app=None):
    """
    Initialise Cloudinary avec la configuration de l'application
    
    Args:
        app: Instance Flask (optionnel)
    """
    if app:
        cloud_name = app.config.get('CLOUDINARY_CLOUD_NAME')
        api_key = app.config.get('CLOUDINARY_API_KEY')
        api_secret = app.config.get('CLOUDINARY_API_SECRET')
    else:
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = os.getenv('CLOUDINARY_API_KEY')
        api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        logger.info(f"✅ Cloudinary configuré: {cloud_name}")
        return True
    else:
        logger.warning("⚠️  Cloudinary non configuré (variables manquantes)")
        return False


def upload_image(
    file_data,
    folder: str = "fast-food/products",
    public_id: Optional[str] = None,
    overwrite: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Upload une image vers Cloudinary
    
    Args:
        file_data: Données du fichier (file object, bytes, ou base64)
        folder: Dossier Cloudinary où stocker l'image
        public_id: ID public personnalisé (optionnel)
        overwrite: Écraser si existe déjà
        
    Returns:
        Dict avec les infos de l'image uploadée ou None en cas d'erreur
    """
    try:
        # Options d'upload
        upload_options = {
            'folder': folder,
            'overwrite': overwrite,
            'resource_type': 'image',
            'format': 'jpg',  # Convertir en JPG pour optimiser
            'transformation': [
                {
                    'width': 800,
                    'height': 800,
                    'crop': 'limit',  # Limiter la taille max sans déformer
                    'quality': 'auto',  # Qualité automatique optimale
                    'fetch_format': 'auto'  # Format optimal selon le navigateur
                }
            ]
        }
        
        if public_id:
            upload_options['public_id'] = public_id
        
        # Upload vers Cloudinary
        result = cloudinary.uploader.upload(file_data, **upload_options)
        
        logger.info(f"✅ Image uploadée: {result.get('secure_url')}")
        
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height'),
            'format': result.get('format'),
            'bytes': result.get('bytes')
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur upload image: {str(e)}")
        return None


def delete_image(public_id: str) -> bool:
    """
    Supprime une image de Cloudinary
    
    Args:
        public_id: ID public de l'image à supprimer
        
    Returns:
        True si suppression réussie
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        
        if result.get('result') == 'ok':
            logger.info(f"✅ Image supprimée: {public_id}")
            return True
        else:
            logger.warning(f"⚠️  Image non trouvée: {public_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur suppression image: {str(e)}")
        return False


def get_image_url(
    public_id: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    crop: str = "fill"
) -> str:
    """
    Génère une URL d'image avec transformations
    
    Args:
        public_id: ID public de l'image
        width: Largeur désirée (optionnel)
        height: Hauteur désirée (optionnel)
        crop: Mode de crop (fill, fit, limit, etc.)
        
    Returns:
        URL de l'image transformée
    """
    try:
        transformation = []
        
        if width or height:
            transform_options = {'crop': crop}
            if width:
                transform_options['width'] = width
            if height:
                transform_options['height'] = height
            transformation.append(transform_options)
        
        url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=transformation,
            secure=True,
            fetch_format='auto',
            quality='auto'
        )
        
        return url
        
    except Exception as e:
        logger.error(f"❌ Erreur génération URL: {str(e)}")
        return ""


def extract_public_id_from_url(cloudinary_url: str) -> Optional[str]:
    """
    Extrait le public_id depuis une URL Cloudinary
    
    Args:
        cloudinary_url: URL complète Cloudinary
        
    Returns:
        Public ID ou None
        
    Example:
        https://res.cloudinary.com/demo/image/upload/v1234/fast-food/products/kebab.jpg
        → fast-food/products/kebab
    """
    try:
        if not cloudinary_url or 'cloudinary.com' not in cloudinary_url:
            return None
        
        # Extraire la partie après /upload/
        parts = cloudinary_url.split('/upload/')
        if len(parts) < 2:
            return None
        
        # Retirer la version (vXXXX) si présente
        path = parts[1]
        if path.startswith('v'):
            path_parts = path.split('/', 1)
            if len(path_parts) > 1:
                path = path_parts[1]
        
        # Retirer l'extension
        public_id = path.rsplit('.', 1)[0]
        
        return public_id
        
    except Exception as e:
        logger.error(f"❌ Erreur extraction public_id: {str(e)}")
        return None


def validate_image_file(file) -> tuple[bool, str]:
    """
    Valide qu'un fichier est une image valide
    
    Args:
        file: Fichier uploadé (werkzeug FileStorage)
        
    Returns:
        Tuple (is_valid, error_message)
    """
    # Vérifier que le fichier existe
    if not file or not file.filename:
        return False, "Aucun fichier fourni"
    
    # Extensions autorisées
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    
    if file_ext not in allowed_extensions:
        return False, f"Extension non autorisée. Utilisez: {', '.join(allowed_extensions)}"
    
    # Taille max: 5MB
    max_size = 5 * 1024 * 1024  # 5MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size:
        return False, f"Fichier trop volumineux. Taille max: 5MB"
    
    # Vérifier le type MIME
    allowed_mimes = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
    if file.mimetype not in allowed_mimes:
        return False, f"Type MIME non autorisé: {file.mimetype}"
    
    return True, ""
