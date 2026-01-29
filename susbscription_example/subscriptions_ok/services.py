# subscriptions/services.py
from datetime import time
from django.utils import timezone
import requests
from django.conf import settings
import uuid

class PaymentService:
    # Modifiez BASE_URL pour utiliser le bon domaine
    BASE_URL = 'https://my-coolpay.com/api'  # Ajout de 'api.' au domaine
    PUBLIC_KEY = '118a4852-7df8-46d9-834b-23b4ef25aaab'

    @classmethod
    def initiate_payment(cls, user, phone_number, language, amount, service_type='premium', coach_name=None):
       try:
           # Vérification des paramètres
           if not user or not phone_number or not amount:
               raise ValueError("Missing required parameters")

           # Détermination de la raison de transaction
           if service_type == 'coach_subscription' and coach_name:
               transaction_reason = f"Abonnement Coach {coach_name}"
           else:
               transaction_reason = "Abonnement Premium XP Trading"

           # Création du payload
           payload = {
               "transaction_amount": int(amount),
               "transaction_currency": "XAF", 
               "transaction_reason": transaction_reason,
               "app_transaction_ref": f"sub_{uuid.uuid4().hex[:10]}", 
               "customer_phone_number": phone_number,
               "customer_name": user.get_full_name() or user.email,
               "customer_email": user.email,
               "customer_lang": language
           }

           # Configuration des headers
           headers = {
               'Content-Type': 'application/json',
               'Accept': 'application/json'
           }

           print(f"Preparing payment request for {user.email}")
           print(f"Sending request to My CoolPay: {payload}")
           
           # Envoi de la requête à My CoolPay
           response = requests.post(
               f"{cls.BASE_URL}/{cls.PUBLIC_KEY}/paylink",
               json=payload,
               headers=headers,
               timeout=30
           )
           
           print(f"Response status: {response.status_code}")
           print(f"Response content: {response.text}")
           
           response.raise_for_status()
           response_data = response.json()

           if response.status_code == 201 or response.status_code == 200:
               # Utiliser la bonne clé 'transaction_ref' de la réponse
               transaction_ref = response_data.get('transaction_ref')
               if not transaction_ref:
                   # Si la clé n'existe pas, vérifier si elle est dans un autre format
                   transaction_ref = response_data.get('app_transaction_ref', payload['app_transaction_ref'])
               
               # S'assurer que payment_url est présent
               if 'payment_url' not in response_data:
                   print(f"[WARNING] payment_url manquant dans la réponse: {response_data}")
                   response_data['payment_url'] = ''
               
               return response_data, transaction_ref
           
           raise Exception(f"Unexpected response: {response.status_code}")

       except requests.exceptions.RequestException as e:
           print(f"Payment service error: {str(e)}")
           raise Exception(f"Error communicating with payment service: {str(e)}")
       except ValueError as e:
           print(f"Validation error: {str(e)}")
           raise
       except Exception as e:
           print(f"Unexpected error: {str(e)}")
           raise Exception(f"Payment initialization failed: {str(e)}")