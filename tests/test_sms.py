"""
Script de test pour l'envoi de SMS via IntechSMS
Usage: python test_sms.py
"""
import os
from dotenv import load_dotenv
from utils.sms import IntechSMS

# Charger les variables d'environnement
load_dotenv()


def test_sms():
    """Test d'envoi de SMS via IntechSMS"""
    
    # Récupérer la configuration
    app_key = os.getenv('INTECH_API_KEY')
    sender_id = os.getenv('INTECH_SENDER_ID', 'FastFood')
    test_number = os.getenv('MANAGER_MOBILE', '+221777293282')
    
    if not app_key or app_key == 'your_intech_app_key_here':
        print("❌ Erreur: INTECH_API_KEY non configurée dans .env")
        print("Veuillez configurer votre clé API IntechSMS dans le fichier .env")
        return
    
    print("🔧 Configuration IntechSMS")
    print(f"   APP_KEY: {app_key[:10]}...")
    print(f"   Sender ID: {sender_id}")
    print(f"   Numéro de test: {test_number}")
    print()
    
    # Créer le client SMS
    sms_client = IntechSMS(app_key=app_key, sender_id=sender_id)
    
    # Message de test
    message = "Test API Fast-Food: Votre API SMS fonctionne correctement !"
    
    print(f"📤 Envoi du SMS de test...")
    print(f"   Message: {message}")
    print()
    
    # Envoyer le SMS
    response = sms_client.send_sms(
        recipients=[test_number],
        message=message
    )
    
    # Afficher le résultat
    print("📨 Réponse de l'API:")
    if "error" in response:
        print(f"   ❌ Erreur: {response['error']}")
    else:
        print(f"   ✅ Succès!")
        print(f"   Réponse: {response}")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 TEST INTECHSMS - API FAST-FOOD")
    print("=" * 60)
    print()
    
    test_sms()
    
    print()
    print("=" * 60)
    print("💡 Pour activer l'envoi réel dans l'API:")
    print("   1. Configurez INTECH_API_KEY dans .env")
    print("   2. Définissez SMS_MOCK_MODE=false")
    print("   3. Redémarrez l'application")
    print("=" * 60)
