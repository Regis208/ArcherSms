#!/usr/bin/env python3
"""
Serveur API Flask pour envoyer des SMS via le TP-Link MR200
Écoute sur le port 5333
"""

from flask import Flask, request, jsonify
import os
import logging
from  mr200_sms import TPLinkMR200

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation Flask
app = Flask(__name__)

# Configuration
ROUTER_IP = os.getenv("ROUTER_IP", "192.168.1.1")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "admin")

# Instance globale du routeur
router = None


def get_router():
    """Obtenir ou créer une instance du routeur connectée"""
    global router
    
    if router is None:
        logger.info("Création d'une nouvelle connexion au routeur...")
        router = TPLinkMR200(host=ROUTER_IP, password=ROUTER_PASSWORD)
        
        if not router.login():
            logger.error("Échec de connexion au routeur")
            router = None
            return None
    
    return router


@app.route('/', methods=['GET'])
def index():
    """Page d'accueil avec documentation"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>TP-Link MR200 SMS API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        h1 { color: #009fda; }
        h2 { color: #333; border-bottom: 2px solid #009fda; padding-bottom: 5px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
        .endpoint { background: #e8f5e9; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>📱 TP-Link MR200 SMS API</h1>
    <p>Service d'envoi de SMS via API REST</p>
    
    <h2>Endpoints disponibles</h2>
    
    <div class="endpoint">
        <h3>POST /send_sms</h3>
        <p>Envoyer un SMS</p>
        <pre>{
    "phone": "+3312345678",
    "message": "Votre message"
}</pre>
        <p><strong>Réponse :</strong></p>
        <pre>{
    "success": true,
    "message": "SMS sent successfully",
    "to": "+3312345678"
}</pre>
    </div>
    
    <div class="endpoint">
        <h3>GET /health</h3>
        <p>Vérifier l'état du service</p>
        <pre>{
    "status": "ok",
    "router": "192.168.1.1",
    "connected": true
}</pre>
    </div>
    
    <div class="endpoint">
        <h3>POST /reconnect</h3>
        <p>Forcer la reconnexion au routeur</p>
    </div>
    
    <h2>Exemples d'utilisation</h2>
    
    <h3>cURL</h3>
    <pre>curl -X POST http://localhost:5333/send_sms \\
  -H "Content-Type: application/json" \\
  -d '{"phone":"+3312345678","message":"Test SMS"}'</pre>
    
    <h3>Python</h3>
    <pre>import requests

response = requests.post('http://localhost:5333/send_sms', 
    json={
        'phone': '+3312345678',
        'message': 'Test SMS'
    }
)

print(response.json())</pre>
    
    <h3>Home Assistant</h3>
    <pre># configuration.yaml
rest_command:
  send_sms_mr200:
    url: "http://192.168.1.XXX:5333/send_sms"
    method: POST
    content_type: 'application/json'
    payload: '{"phone": "{{ phone }}", "message": "{{ message }}"}'

# Automation
automation:
  - alias: "SMS Alerte"
    trigger:
      - platform: state
        entity_id: binary_sensor.door
        to: 'on'
    action:
      - service: rest_command.send_sms_mr200
        data:
          phone: "+3312345678"
          message: "Porte ouverte !"</pre>
    
    <h3>JavaScript/Node.js</h3>
    <pre>fetch('http://localhost:5333/send_sms', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        phone: '+3312345678',
        message: 'Test SMS'
    })
})
.then(res => res.json())
.then(data => console.log(data));</pre>
</body>
</html>
    """


@app.route('/health', methods=['GET'])
def health():
    """Vérifier l'état du service"""
    return jsonify({
        "status": "ok",
        "router": ROUTER_IP,
        "connected": router is not None
    }), 200


@app.route('/send_sms', methods=['POST'])
def send_sms():
    """
    Envoyer un SMS
    
    Body JSON accepté:
    - {"phone": "06...", "message": "..."}
    - {"to": "06...", "text": "..."}
    - {"number": "06...", "content": "..."}
    """
    try:
        # Récupérer les données JSON
        data = request.get_json()
        
        if not data:
            logger.warning("Requête sans JSON")
            return jsonify({
                "error": "No JSON data provided",
                "success": False
            }), 400
        
        # Support de plusieurs formats de champs
        phone = data.get('phone') or data.get('to') or data.get('number')
        message = data.get('message') or data.get('text') or data.get('content')
        
        # Validation
        if not phone:
            logger.warning("Champ 'phone' manquant")
            return jsonify({
                "error": "Missing 'phone' field (or 'to', 'number')",
                "success": False
            }), 400
        
        if not message:
            logger.warning("Champ 'message' manquant")
            return jsonify({
                "error": "Missing 'message' field (or 'text', 'content')",
                "success": False
            }), 400
        
        logger.info(f"Requête SMS - To: {phone}, Message: {message[:50]}...")
        
        # Obtenir le routeur
        r = get_router()
        if r is None:
            logger.error("Impossible de se connecter au routeur")
            return jsonify({
                "error": "Failed to connect to router",
                "success": False
            }), 500
        
        # Envoyer le SMS
        success = r.send_sms(phone, message)
        
        if success:
            logger.info(f"✓ SMS envoyé avec succès à {phone}")
            return jsonify({
                "success": True,
                "message": "SMS sent successfully",
                "to": phone
            }), 200
        else:
            logger.error(f"✗ Échec d'envoi SMS à {phone}")
            
            # Réinitialiser la connexion en cas d'échec
            global router
            router = None
            
            return jsonify({
                "error": "Failed to send SMS",
                "success": False,
                "details": "Check logs for more information"
            }), 500
            
    except Exception as e:
        logger.exception("Erreur lors du traitement de la requête")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/reconnect', methods=['POST'])
def reconnect():
    """Forcer la reconnexion au routeur"""
    global router
    
    logger.info("Reconnexion forcée au routeur...")
    router = None
    
    r = get_router()
    if r:
        logger.info("✓ Reconnexion réussie")
        return jsonify({
            "success": True,
            "message": "Reconnected to router successfully"
        }), 200
    else:
        logger.error("✗ Échec de reconnexion")
        return jsonify({
            "error": "Failed to reconnect to router",
            "success": False
        }), 500


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Démarrage du serveur API SMS")
    logger.info("=" * 60)
    logger.info(f"Port: 5333")
    logger.info(f"Routeur: {ROUTER_IP}")
    logger.info(f"Documentation: http://localhost:5333/")
    logger.info("=" * 60)
    
    # Connexion initiale
    logger.info("Connexion initiale au routeur...")
    if get_router():
        logger.info("✓ Prêt à envoyer des SMS")
    else:
        logger.warning("⚠ Impossible de se connecter au routeur au démarrage")
        logger.warning("  Le service tentera de se connecter à la première requête")
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=5333, debug=False)
