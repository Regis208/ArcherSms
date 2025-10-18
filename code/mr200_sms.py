#!/usr/bin/env python3
"""
TP-Link Archer MR200 - Client SMS
Gère la connexion et l'envoi de SMS via le routeur MR200
"""

import requests
import base64
import re
import random
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TPLinkMR200:
    """Client pour le routeur TP-Link Archer MR200"""
    
    def __init__(self, host="192.168.1.1", password="admin"):
        self.host = host
        self.password = password
        self.session = requests.Session()
        self.nn = None
        self.ee = None
        self.token = None
        self.jsessionid = None
        self.max_retry = 3
        
    def get_auth_params(self):
        """Récupérer les paramètres RSA (nn, ee) du routeur"""
        url = f"http://{self.host}/cgi/getParm"
        
        headers = {
            "Host": self.host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"http://{self.host}/",
            "Connection": "keep-alive"
        }
        
        try:
            response = self.session.post(url, headers=headers, timeout=10)
            
            # Parser la réponse JavaScript
            nn_match = re.search(r'var nn="([0-9A-Fa-f]+)"', response.text)
            ee_match = re.search(r'var ee="([0-9A-Fa-f]+)"', response.text)
            
            if nn_match and ee_match:
                self.nn = nn_match.group(1)
                self.ee = ee_match.group(1)
                logger.info(f"✓ Paramètres RSA récupérés (nn: {self.nn[:20]}..., ee: {self.ee})")
                return True
            else:
                logger.error("✗ Impossible de parser nn et ee")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération des paramètres RSA: {e}")
            return False
    
    def pkcs1_pad(self, message, key_length):
        """
        Padding PKCS#1 v1.5
        Compatible avec l'implémentation JavaScript du routeur
        """
        message_bytes = message.encode('utf-8')
        message_len = len(message_bytes)
        modulus_len = (key_length + 7) // 8
        
        if message_len > modulus_len - 11:
            raise ValueError("Message trop long pour PKCS#1 padding")
        
        # Générer le padding avec des octets aléatoires non-nuls
        padding_len = modulus_len - message_len - 3
        padding = bytearray()
        
        while len(padding) < padding_len:
            byte = random.randint(1, 255)
            padding.append(byte)
        
        # Format: 0x00 || 0x02 || padding || 0x00 || message
        padded = bytearray([0x00, 0x02]) + padding + bytearray([0x00]) + message_bytes
        
        return bytes(padded)
    
    def rsa_encrypt(self, message):
        """Chiffrer avec RSA (comme le routeur)"""
        # Convertir nn et ee en entiers
        n = int(self.nn, 16)
        e = int(self.ee, 16)
        
        # Encoder en Base64 d'abord
        encoded_message = base64.b64encode(message.encode('utf-8')).decode('utf-8')
        
        # Calculer la longueur de clé
        key_length = n.bit_length()
        
        # Appliquer le padding PKCS#1 v1.5
        padded_message = self.pkcs1_pad(encoded_message, key_length)
        
        # Convertir en entier
        message_int = int.from_bytes(padded_message, 'big')
        
        # Chiffrement RSA: c = m^e mod n
        encrypted_int = pow(message_int, e, n)
        
        # Convertir en hex avec padding
        modulus_bytes = (key_length + 7) // 8
        encrypted_hex = format(encrypted_int, f'0{modulus_bytes*2}x')
        
        return encrypted_hex
    
    def login(self):
        """Se connecter au routeur"""
        # Récupérer les paramètres RSA
        #if not self.nn or not self.ee:
        retry=0    
        while (not (ok := self.get_auth_params())) and retry < self.max_retry:
          retry=retry+1
          logger.error(f"✗ Retreaving RSA parameters #{retry}")
            
        if not ok:
          logger.error(f"✗ Impossible de récupérer les paramètres RSA ") 
            
        # Chiffrer les identifiants
        encrypted_password = self.rsa_encrypt(self.password)
        encrypted_username = self.rsa_encrypt("admin")
        
        # Envoyer la requête de login
        url = f"http://{self.host}/cgi/login"
        params = {
            "UserName": encrypted_username,
            "Passwd": encrypted_password,
            "Action": "1",
            "LoginStatus": "0"
        }
        
        headers = {
            "Host": self.host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"http://{self.host}/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            response = self.session.post(url, params=params, headers=headers, 
                                        allow_redirects=False, timeout=10)
            
            # Vérifier la réponse
            if response.status_code in [200, 302]:
                # Récupérer le JSESSIONID
                for cookie in self.session.cookies:
                    if cookie.name == 'JSESSIONID':
                        self.jsessionid = cookie.value
                        logger.info(f"✓ JSESSIONID: {self.jsessionid[:20]}...")
                
                logger.info("✓ Connexion réussie")
                
                # Récupérer le token
                return self.get_token()
            else:
                logger.error(f"✗ login - Échec de connexion: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur lors du login: {e}")
            return False
    
    def get_token(self):
        """Récupérer le token depuis la page d'accueil"""
        url = f"http://{self.host}/"
        
        headers = {
            "Host": self.host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"http://{self.host}/",
            "Connection": "keep-alive"
        }
        
        # Ajouter les cookies
        if self.jsessionid:
            self.session.cookies.set('JSESSIONID', self.jsessionid)
            self.session.cookies.set('loginErrorShow', '1')
            self.session.cookies.set('qrClose', 'true')
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Chercher le token dans les headers HTTP             
                
                # Chercher dans le contenu HTML/JS
                pattern = r'var\s+token\s*=\s*["\']([a-zA-Z0-9]+)["\']'                    
                                  
                token_match = re.search(pattern, response.text, re.IGNORECASE)
                if token_match:
                    self.token = token_match.group(1)
                    logger.info(f"✓ Token récupéré depuis page: {self.token}")
                    return True
                
                logger.warning("⚠ Token non trouvé, tentative sans token...")
                return True
            else:
                logger.error(f"✗ Échec récupération token: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération du token: {e}")
            return False
    
    def close(self):
        """Properly close the session and release resources"""
        if self.session:
            try:
                self.session.close()
                logger.info("✓ Session closed")
            except Exception as e:
                logger.warning(f"⚠ Error closing session: {e}")

    def __del__(self):
        """Cleanup when object is garbage collected"""
        self.close()

    def __enter__(self):
        """Support context manager"""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Cleanup when exiting context manager"""
        self.close()

    def send_sms(self, phone_number, message):
        """Envoyer un SMS"""
        # Format du payload avec CRLF
        payload = (
            f"[LTE_SMS_SENDNEWMSG#0,0,0,0,0,0#0,0,0,0,0,0]0,3\r\n"
            f"index=1\r\n"
            f"to={phone_number}\r\n"
            f"textContent={message}\r\n"
            f"\r\n"
        )
        
        # URL d'envoi
        url = f"http://{self.host}/cgi?2"
        
        headers = {
            "Host": self.host,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"http://{self.host}/",
            "Connection": "keep-alive"
        }
        
        # Ajouter le TokenID si disponible
        headers["TokenID"] = self.token
        logger.info(f"✓ Utilisation du token: {self.token}")
    
        # Ajouter les cookies
        cookie_string = f"JSESSIONID={self.jsessionid};loginErrorShow=1;qrClose=true"
        headers["Cookie"] = cookie_string
    
        try:
            response = self.session.post(url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✓ SMS envoyé à {phone_number}")
                return True
            else:
                logger.error(f"✗ Échec envoi SMS: {response.status_code}")
                logger.error(f"  Réponse: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'envoi du SMS: {e}")
            return False


def main():
    """Point d'entrée principal pour tests"""
    import os
    
    # Configuration
    ROUTER_IP = os.getenv("ROUTER_IP", "192.168.1.1")
    ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD", "admin")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+3312345678")
    MESSAGE = os.getenv("MESSAGE", "Test depuis Python")
    
    # Créer l'instance
    router = TPLinkMR200(host=ROUTER_IP, password=ROUTER_PASSWORD)
    
    # Se connecter
    logger.info("Connexion au routeur...")
    if not router.login():
        logger.error("Échec de connexion")
        return 1
    
    # Envoyer un SMS
    logger.info(f"Envoi du SMS à {PHONE_NUMBER}...")
    if router.send_sms(PHONE_NUMBER, MESSAGE):
        logger.info("✓ Opération terminée avec succès")
        return 0
    else:
        logger.error("✗ Échec de l'envoi")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

