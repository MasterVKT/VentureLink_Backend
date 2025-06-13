# Implémentation de l'intégration avec My-CoolPay pour VentureLink

## Introduction

Ce document explique l'architecture et les détails de l'implémentation de l'intégration avec l'API de paiement My-CoolPay dans l'application VentureLink. Cette intégration permet de gérer les paiements, les remboursements et les webhooks pour les diverses transactions financières de la plateforme.

## Architecture

L'intégration de My-CoolPay est structurée en plusieurs couches :

1. **Modèles de données** : Stockent les informations sur les paiements et les remboursements
2. **Service d'intégration** : Gère les interactions directes avec l'API My-CoolPay
3. **Service de paiement** : Coordonne les opérations internes de paiement avec l'API externe
4. **API REST** : Expose les fonctionnalités de paiement au frontend
5. **Webhooks** : Traite les callbacks asynchrones de My-CoolPay

## Modèles de données

Deux modèles principaux ont été créés :

### Payment (Paiement)

Stocke les informations sur les paiements :

- Lien avec l'utilisateur qui effectue le paiement
- Montant et devise
- Statut (en attente, complété, échoué, remboursé, etc.)
- Type de paiement (abonnement, investissement, pourboire, etc.)
- Identifiants externes pour My-CoolPay
- Métadonnées associées au paiement
- Relation générique vers l'objet concerné par le paiement

### Refund (Remboursement)

Stocke les informations sur les remboursements :

- Lien avec le paiement remboursé
- Montant et devise du remboursement
- Statut (en attente, complété, échoué)
- Identifiant externe pour My-CoolPay
- Raison du remboursement

## Services

### MyCoolPayService

Service de bas niveau qui gère les interactions directes avec l'API My-CoolPay :

- Création de paiements
- Vérification du statut des paiements
- Traitement des remboursements
- Vérification des signatures de webhook

Ce service encapsule les détails techniques de l'API (headers, authentification, formats de données, etc.).

### PaymentService

Service de haut niveau qui coordonne les opérations internes avec l'API externe :

- Création de paiement avec enregistrement en base de données
- Mise à jour du statut des paiements
- Gestion des remboursements
- Traitement des événements webhook
- Conversion de devises pour les montants

## API REST

L'API expose plusieurs endpoints pour interagir avec les paiements :

- `POST /api/v1/payments/` : Création d'un nouveau paiement
- `GET /api/v1/payments/` : Liste des paiements de l'utilisateur
- `GET /api/v1/payments/{id}/` : Détails d'un paiement spécifique
- `POST /api/v1/payments/{id}/refund/` : Remboursement d'un paiement
- `POST /api/v1/payments/{id}/check_status/` : Vérification du statut d'un paiement
- `POST /api/v1/webhooks/mycoolpay/` : Endpoint pour les webhooks de My-CoolPay

## Webhook

Le système de webhook est conçu pour :

- Vérifier la signature des événements pour la sécurité
- Traiter les événements selon leur type (paiement complété, remboursement, etc.)
- Mettre à jour les enregistrements en base de données
- Déclencher des actions secondaires si nécessaire (notifications, etc.)

### Configuration du Webhook

Pour configurer les webhooks My-CoolPay dans votre environnement, suivez ces étapes :

1. Créez un endpoint webhook dans votre application (déjà configuré à `/api/v1/payments/mycoolpay/webhook/`)
2. Configurez le webhook dans votre compte My-CoolPay avec cette URL
3. Notez le secret webhook fourni par My-CoolPay
4. Ajoutez ce secret dans votre fichier `.env` (différents secrets pour sandbox et production)
5. Ajoutez les adresses IP de My-CoolPay dans la liste des IPs autorisées

### Types d'événements supportés

Le service WebhookService traite les types d'événements suivants :

- `payment.success`: Paiement réussi
- `payment.failed`: Échec de paiement
- `payment.refunded`: Remboursement effectué
- `subscription.created`: Abonnement créé
- `subscription.cancelled`: Abonnement annulé
- `subscription.renewed`: Abonnement renouvelé

### Structure d'un événement webhook

```json
{
  "event_type": "payment.success",
  "transaction_ref": "tx_123456789",
  "app_transaction_ref": "payment_uuid",
  "transaction_date": "2023-10-15T14:30:00Z",
  "transaction_details": {
    "amount": 100.00,
    "currency": "EUR",
    "payment_method": "card"
  }
}
```

### Vérification de sécurité

Chaque webhook est vérifié à l'aide d'une signature HMAC SHA-256. Le processus est le suivant :

1. My-CoolPay envoie les données du webhook avec un en-tête `X-MyCoolPay-Signature`
2. Notre application calcule la signature attendue en utilisant le secret webhook
3. Les signatures sont comparées pour vérifier l'authenticité de la requête
4. Si la vérification échoue, la requête est rejetée

### Implémentation manuelle

Si vous souhaitez implémenter manuellement la vérification de signature :

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected_signature = hmac.new(
        key=secret.encode(),
        msg=payload.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
```

### Tests et débogage

Pour tester les webhooks en développement, vous pouvez :

1. Utiliser un service comme ngrok pour exposer votre environnement local
2. Configurer temporairement le webhook My-CoolPay pour pointer vers l'URL ngrok
3. Déclencher des événements dans l'interface sandbox de My-CoolPay
4. Vérifier les logs de votre application pour confirmer la réception et le traitement

Vous pouvez également utiliser les commandes de test pour simuler des événements webhook :

```bash
# Simuler un webhook de paiement réussi
python manage.py test_webhook payment.success

# Simuler un webhook de remboursement
python manage.py test_webhook payment.refunded
```

## Conversions de devise

Le système prend en charge plusieurs devises :

- Stockage des montants dans la devise d'origine
- Conversion automatique des montants à l'affichage
- Prise en compte des taux de change actuels

## Sécurité

Plusieurs mesures de sécurité ont été mises en place :

- Utilisation de HTTPS pour toutes les communications
- Vérification des signatures pour les webhooks
- Validation stricte des entrées utilisateur
- Gestion des idempotents pour éviter les paiements dupliqués

## Configuration par environnement

L'intégration prend en charge différents environnements :

- Mode bac à sable (sandbox) pour le développement et les tests
- Mode production pour l'environnement réel
- Clés API et secrets différents selon l'environnement

## Tests

Des tests unitaires et d'intégration couvrent :

- La création et la gestion des paiements
- Les remboursements
- Le traitement des webhooks
- Les cas d'erreur et exceptions

## Internationalisation

L'intégration prend en charge :

- Plusieurs devises (EUR, USD, GBP, etc.)
- Messages d'erreur et notifications traduits
- Formats de montant adaptés selon les conventions locales 