"""
Utilitaires pour l'envoi de SMS via l'API IntechSMS
"""
import logging
import requests
import json
from typing import Optional, List
from flask import current_app

logger = logging.getLogger(__name__)


class IntechSMS:
    """Client pour l'API IntechSMS"""
    
    def __init__(self, app_key: str, sender_id: str = "FastFood"):
        """
        Initialise le client IntechSMS
        
        Args:
            app_key: Clé API IntechSMS
            sender_id: Identifiant de l'expéditeur (max 11 caractères)
        """
        self.app_key = app_key
        self.sender_id = sender_id
        self.base_url = "https://gateway.intechsms.sn/api/send-sms"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def send_sms(self, recipients: List[str], message: str) -> dict:
        """
        Envoie un SMS à un ou plusieurs destinataires
        
        Args:
            recipients: Liste de numéros de téléphone (format international)
            message: Contenu du SMS
            
        Returns:
            Réponse de l'API ou message d'erreur
        """
        if not isinstance(recipients, list) or not all(isinstance(num, str) for num in recipients):
            return {"error": "Les destinataires doivent être une liste de chaînes de caractères"}
        
        payload = {
            "app_key": self.app_key,
            "sender": self.sender_id,
            "content": message,
            "msisdn": recipients
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("Timeout lors de l'envoi du SMS")
            return {"error": "Délai d'attente dépassé"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête: {str(e)}")
            return {"error": f"Échec de la requête: {str(e)}"}
        except json.JSONDecodeError:
            logger.error("Impossible de décoder la réponse JSON")
            return {"error": "Réponse invalide de l'API"}


def send_sms_intech(
    destination_number: str,
    message: str,
    mock_mode: bool = True
) -> bool:
    """
    Envoie un SMS via l'API IntechSMS
    
    Args:
        destination_number: Numéro de téléphone du destinataire (format international)
        message: Contenu du message SMS
        mock_mode: Si True, simule l'envoi (mode développement)
        
    Returns:
        True si l'envoi est réussi, False en cas d'erreur
    """
    try:
        # Validation basique du numéro
        if not destination_number:
            logger.warning("Numéro de téléphone manquant")
            return False
        
        # S'assurer que le numéro est au format international
        if not destination_number.startswith('+'):
            logger.warning(
                f"Le numéro doit être au format international (+221... ou +33...): {destination_number}"
            )
            # Tentative de conversion si c'est un numéro sénégalais
            if destination_number.startswith('77') or destination_number.startswith('76') or destination_number.startswith('78'):
                destination_number = f"+221{destination_number}"
                logger.info(f"Numéro converti: {destination_number}")
        
        # Validation du message
        if not message or len(message.strip()) == 0:
            logger.warning("Le message SMS ne peut pas être vide")
            return False
        
        # Mode simulation (développement)
        if mock_mode:
            logger.info("=" * 80)
            logger.info("📱 SMS ENVOYÉ (MODE SIMULATION)")
            logger.info(f"Destinataire: {destination_number}")
            logger.info(f"Message: {message}")
            logger.info("=" * 80)
            return True
        
        # Mode production : envoi réel via IntechSMS
        try:
            app_key = current_app.config.get('INTECH_API_KEY')
            sender_id = current_app.config.get('INTECH_SENDER_ID', 'FastFood')
            
            if not app_key:
                logger.error("INTECH_API_KEY non configurée")
                return False
            
            # Initialiser le client IntechSMS
            sms_client = IntechSMS(app_key=app_key, sender_id=sender_id)
            
            # Envoyer le SMS
            response = sms_client.send_sms(
                recipients=[destination_number],
                message=message
            )
            
            # Vérifier la réponse
            if "error" in response:
                logger.error(f"Erreur IntechSMS: {response['error']}")
                return False
            
            logger.info(f"✅ SMS envoyé avec succès à {destination_number}")
            logger.debug(f"Réponse API: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi réel du SMS: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du SMS à {destination_number}: {str(e)}")
        return False


def send_order_confirmation_sms(
    order_id: int,
    customer_mobile: str,
    total: int,  # Amount in FCFA (integer)
    address: str,
    mock_mode: bool = True
) -> bool:
    """
    Envoie un SMS de confirmation de commande au client
    
    Args:
        order_id: ID de la commande
        customer_mobile: Numéro du client
        total: Montant total de la commande en FCFA (entier)
        address: Adresse de livraison
        mock_mode: Si True, simule l'envoi (mode développement)
        
    Returns:
        True si l'envoi est réussi
    """
    # Message sans émojis pour compatibilité SMS
    message = (
        f"Commande #{order_id} confirmee ! "
        f"Total: {total} FCFA. "
        f"Livraison: {address}. "
        f"Merci pour votre commande !"
    )
    return send_sms_intech(customer_mobile, message, mock_mode=mock_mode)


def send_manager_notification_sms(
    order_id: int,
    customer_name: str,
    customer_mobile: str,
    address: str,
    total: int,  # Amount in FCFA (integer)
    items_summary: str,
    details: str,
    manager_mobile: str,
    mock_mode: bool = True
) -> bool:
    """
    Envoie un SMS de notification au gérant pour une nouvelle commande avec tous les détails
    
    Args:
        order_id: ID de la commande
        customer_name: Nom du client
        customer_mobile: Numéro du client
        address: Adresse de livraison
        total: Montant total de la commande en FCFA (entier)
        items_summary: Résumé des articles commandés
        details: Détails supplémentaires de la commande
        manager_mobile: Numéro du gérant
        mock_mode: Si True, simule l'envoi (mode développement)
        
    Returns:
        True si l'envoi est réussi
    """
    message = (
        f"Nouvelle commande #{order_id} recue !\n"
        f"Client: {customer_name} ({customer_mobile})\n"
        f"Adresse: {address}\n"
        f"Articles: {items_summary}\n"
    )
    
    if details:
        message += f"Details: {details}\n"
    
    message += f"Total: {total} FCFA"
    
    return send_sms_intech(manager_mobile, message, mock_mode=mock_mode)
