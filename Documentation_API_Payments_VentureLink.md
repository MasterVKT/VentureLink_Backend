# Documentation API Payments VentureLink

## Vue d'ensemble

L'application **Payments** de VentureLink gère l'intégralité du système de paiement de la plateforme, intégrée avec l'API **My-CoolPay** pour les paiements en Afrique. Elle couvre les abonnements premium, les investissements, et tous les types de transactions financières.

### Base URL
- **Développement:** `https://api-dev.venturelink.com/api/v1/payments/`
- **Production:** `https://api.venturelink.com/api/v1/payments/`

### Authentification
Tous les endpoints nécessitent une authentification JWT via l'en-tête:
```
Authorization: Bearer {token}
```

### Intégration My-CoolPay
- **Sandbox:** `https://sandbox.my-coolpay.com/api/v1`
- **Production:** `https://api.my-coolpay.com/api/v1`
- **Devises supportées:** XAF, EUR, USD, XOF
- **Opérateurs mobiles:** Orange Money, MTN Mobile Money, Moov Money, Express Union

---

## Modèles de données

### SubscriptionPlan (Plan d'abonnement unifié)
Plans d'abonnement avec prix multi-devises:
- **Prix:** EUR, XAF, USD pour chaque plan
- **Fonctionnalités:** Projets max, investissements max, IA matching, support prioritaire
- **Configuration:** Durée, essai gratuit, popularité
- **Intégration:** ID My-CoolPay pour synchronisation

### UserSubscription (Abonnement utilisateur)
Abonnements actifs des utilisateurs:
- **Statuts:** `ACTIVE`, `PENDING`, `EXPIRED`, `CANCELLED`, `TRIAL`, `SUSPENDED`
- **Gestion:** Dates de début/fin, renouvellement automatique, devise de facturation
- **Suivi:** Historique des paiements, métadonnées

### Payment (Paiement)
Transactions financières via My-CoolPay:
- **Statuts:** `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `REFUNDED`, `CANCELLED`
- **Types:** `SUBSCRIPTION`, `INVESTMENT`, `TIP`, `SERVICE_FEE`, `OTHER`
- **Relation générique:** Peut être lié à n'importe quel objet (projet, abonnement, etc.)

### PaymentMethod (Méthodes de paiement)
Méthodes disponibles via My-CoolPay:
- **Types:** Mobile Money, Carte bancaire, Virement, Espèces
- **Opérateurs:** Orange, MTN, Moov, Express Union
- **Configuration:** Frais, limites, devises supportées

### Refund (Remboursement)
Gestion des remboursements:
- **Statuts:** `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
- **Montants:** Remboursement partiel ou total
- **Traçabilité:** Raisons, notes administratives

---

## Endpoints principaux

### Base URL: `/api/v1/payments/`

## 1. Gestion des plans d'abonnement

### 1.1 GET /plans/
**Description:** Liste les plans d'abonnement disponibles

**Authentification:** Requise

**Réponse (200 OK):**
```json
[
  {
    "id": "basic_monthly",
    "name": "Plan Basic Mensuel",
    "description": "Plan de base pour entrepreneurs débutants",
    "price_eur": "9.99",
    "price_xaf": "6500.00",
    "price_usd": "10.99",
    "duration_days": 30,
    "features": [
      "Création de 2 projets",
      "Messagerie de base",
      "Support standard"
    ],
    "max_projects": 2,
    "max_investments": 5,
    "max_messages": 50,
    "ai_matching": false,
    "priority_support": false,
    "advanced_analytics": false,
    "custom_branding": false,
    "is_active": true,
    "is_popular": false,
    "is_free": false,
    "trial_days": 7,
    "mycoolpay_plan_id": "plan_basic_monthly_001",
    "sort_order": 1
  },
  {
    "id": "premium_yearly",
    "name": "Plan Premium Annuel",
    "description": "Plan complet pour entrepreneurs confirmés",
    "price_eur": "99.99",
    "price_xaf": "65000.00",
    "price_usd": "109.99",
    "duration_days": 365,
    "features": [
      "Projets illimités",
      "IA Matching avancé",
      "Analytics détaillées",
      "Support prioritaire",
      "Personnalisation"
    ],
    "max_projects": 0,
    "max_investments": 0,
    "max_messages": 0,
    "ai_matching": true,
    "priority_support": true,
    "advanced_analytics": true,
    "custom_branding": true,
    "is_active": true,
    "is_popular": true,
    "is_free": false,
    "trial_days": 14,
    "sort_order": 3
  }
]
```

---

## 2. Gestion des abonnements utilisateur

### 2.1 GET /subscription/
**Description:** Récupère l'abonnement actuel de l'utilisateur

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Jean",
    "last_name": "Dupont"
  },
  "plan": {
    "id": "premium_yearly",
    "name": "Plan Premium Annuel",
    "price_eur": "99.99",
    "duration_days": 365
  },
  "status": "ACTIVE",
  "started_at": "2024-01-15T10:00:00Z",
  "expires_at": "2025-01-15T10:00:00Z",
  "trial_ends_at": null,
  "cancelled_at": null,
  "suspended_at": null,
  "auto_renew": true,
  "next_billing_date": "2025-01-15T10:00:00Z",
  "billing_currency": "EUR",
  "last_payment_date": "2024-01-15T10:00:00Z",
  "last_payment_amount": "99.99",
  "mycoolpay_subscription_id": "sub_premium_001",
  "days_remaining": 335,
  "is_active": true,
  "is_in_trial": false,
  "is_expired": false,
  "current_period_price": "99.99",
  "formatted_current_price": "99.99 €"
}
```

### 2.2 POST /subscription/create/
**Description:** Crée un nouvel abonnement avec paiement

**Authentification:** Requise

**Requête:**
```json
{
  "plan_id": "premium_yearly",
  "billing_currency": "EUR",
  "payment_method": "CM_OM",
  "phone_number": "+237123456789",
  "return_url": "https://app.venturelink.com/subscription/success",
  "cancel_url": "https://app.venturelink.com/subscription/cancel"
}
```

**Réponse (201 Created):**
```json
{
  "subscription": {
    "id": "uuid",
    "plan": {
      "id": "premium_yearly",
      "name": "Plan Premium Annuel"
    },
    "status": "PENDING",
    "billing_currency": "EUR"
  },
  "payment": {
    "id": "uuid",
    "amount": "99.99",
    "currency": "EUR",
    "status": "PENDING",
    "external_payment_id": "pay_001",
    "external_checkout_url": "https://checkout.my-coolpay.com/pay/001"
  },
  "checkout_url": "https://checkout.my-coolpay.com/pay/001",
  "next_action": "REDIRECT_TO_CHECKOUT"
}
```

### 2.3 POST /subscription/cancel/
**Description:** Annule l'abonnement de l'utilisateur

**Authentification:** Requise

**Requête:**
```json
{
  "reason": "Plus besoin du service",
  "immediate": false
}
```

**Réponse (200 OK):**
```json
{
  "message": "Abonnement annulé avec succès",
  "subscription": {
    "id": "uuid",
    "status": "CANCELLED",
    "cancelled_at": "2024-01-20T15:30:00Z",
    "expires_at": "2025-01-15T10:00:00Z"
  },
  "access_until": "2025-01-15T10:00:00Z"
}
```

---

## 3. Gestion des paiements

### 3.1 GET /payments/
**Description:** Liste les paiements de l'utilisateur

**Authentification:** Requise

**Paramètres de requête:**
- `status` (string): Filtrer par statut
- `payment_type` (string): Filtrer par type
- `is_test` (boolean): Paiements de test uniquement
- `ordering` (string): Tri (`-created_at`, `amount`, etc.)

**Réponse (200 OK):**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "amount": "99.99",
      "currency": "EUR",
      "status": "COMPLETED",
      "payment_type": "SUBSCRIPTION",
      "description": "Abonnement Premium Annuel",
      "external_payment_id": "pay_001",
      "completed_at": "2024-01-15T10:05:00Z",
      "is_test": false,
      "created_at": "2024-01-15T10:00:00Z",
      "related_object": {
        "type": "UserSubscription",
        "id": "uuid"
      }
    }
  ]
}
```

### 3.2 GET /payments/{id}/
**Description:** Récupère les détails d'un paiement

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  },
  "amount": "99.99",
  "currency": "EUR",
  "status": "COMPLETED",
  "payment_type": "SUBSCRIPTION",
  "description": "Abonnement Premium Annuel",
  "external_payment_id": "pay_001",
  "external_checkout_url": null,
  "metadata": {
    "plan_id": "premium_yearly",
    "billing_cycle": "yearly"
  },
  "completed_at": "2024-01-15T10:05:00Z",
  "is_test": false,
  "is_completed": true,
  "is_refunded": false,
  "can_be_refunded": true,
  "created_at": "2024-01-15T10:00:00Z",
  "related_object": {
    "type": "UserSubscription",
    "id": "uuid"
  }
}
```

### 3.3 POST /payments/create_payment/
**Description:** Crée un nouveau paiement

**Authentification:** Requise

**Requête:**
```json
{
  "amount": "50.00",
  "currency": "EUR",
  "payment_type": "INVESTMENT",
  "description": "Investissement dans le projet EcoApp",
  "metadata": {
    "project_id": "uuid",
    "investment_type": "equity"
  },
  "success_url": "https://app.venturelink.com/payments/success",
  "cancel_url": "https://app.venturelink.com/payments/cancel"
}
```

**Réponse (201 Created):**
```json
{
  "payment": {
    "id": "uuid",
    "amount": "50.00",
    "currency": "EUR",
    "status": "PENDING",
    "payment_type": "INVESTMENT",
    "external_payment_id": "pay_002"
  },
  "checkout_url": "https://checkout.my-coolpay.com/pay/002"
}
```

### 3.4 POST /payments/{id}/refund/
**Description:** Rembourse un paiement

**Authentification:** Requise (propriétaire ou admin)

**Requête:**
```json
{
  "amount": "25.00",
  "reason": "Remboursement partiel demandé par l'utilisateur",
  "notes": "Remboursement approuvé par le support"
}
```

**Réponse (200 OK):**
```json
{
  "payment": {
    "id": "uuid",
    "status": "PARTIALLY_REFUNDED",
    "amount": "50.00"
  },
  "refund": {
    "id": "uuid",
    "amount": "25.00",
    "currency": "EUR",
    "status": "COMPLETED",
    "reason": "Remboursement partiel demandé par l'utilisateur",
    "external_refund_id": "ref_001",
    "completed_at": "2024-01-20T14:30:00Z"
  }
}
```

### 3.5 POST /payments/{id}/check_status/
**Description:** Met à jour et retourne le statut d'un paiement

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "completed_at": "2024-01-15T10:05:00Z",
  "external_payment_id": "pay_001"
}
```

---

## 4. Paiements directs My-CoolPay

### 4.1 POST /payin/
**Description:** Initie un paiement direct avec opérateur spécifique

**Authentification:** Requise

**Requête:**
```json
{
  "amount": "10000",
  "currency": "XAF",
  "phone_number": "+237123456789",
  "operator": "CM_OM",
  "description": "Abonnement Premium",
  "customer_name": "Jean Dupont",
  "customer_email": "jean@example.com"
}
```

**Réponse (200 OK):**
```json
{
  "success": true,
  "transaction_ref": "TXN_001",
  "status": "REQUIRE_OTP",
  "message": "Code OTP envoyé au +237123456789",
  "next_action": "AUTHORIZE_WITH_OTP"
}
```

### 4.2 POST /authorize/
**Description:** Autorise un paiement avec le code OTP

**Authentification:** Requise

**Requête:**
```json
{
  "transaction_ref": "TXN_001",
  "otp_code": "123456"
}
```

**Réponse (200 OK):**
```json
{
  "success": true,
  "transaction_ref": "TXN_001",
  "status": "COMPLETED",
  "message": "Paiement autorisé avec succès",
  "payment_id": "uuid"
}
```

### 4.3 GET /{payment_id}/status/
**Description:** Vérifie le statut d'un paiement

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "payment_id": "uuid",
  "status": "COMPLETED",
  "transaction_ref": "TXN_001",
  "amount": "10000",
  "currency": "XAF",
  "completed_at": "2024-01-20T15:30:00Z"
}
```

---

## 5. Méthodes de paiement

### 5.1 GET /methods/
**Description:** Liste les méthodes de paiement disponibles

**Authentification:** Requise

**Paramètres:**
- `currency` (string): Filtrer par devise supportée
- `country` (string): Filtrer par pays

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "name": "Orange Money Cameroun",
    "type": "MOBILE_MONEY",
    "operator": "ORANGE",
    "is_active": true,
    "supported_currencies": ["XAF"],
    "fee_percentage": "1.50",
    "fee_fixed": "0.00",
    "min_amount": "100.00",
    "max_amount": "500000.00",
    "logo_url": "https://example.com/logos/orange.png"
  },
  {
    "id": "uuid",
    "name": "Carte Bancaire Européenne",
    "type": "BANK_CARD",
    "operator": null,
    "is_active": true,
    "supported_currencies": ["EUR", "USD"],
    "fee_percentage": "2.90",
    "fee_fixed": "0.30",
    "min_amount": "1.00",
    "max_amount": "10000.00"
  }
]
```

---

## 6. Historique et statistiques

### 6.1 GET /history/
**Description:** Historique complet des paiements de l'utilisateur

**Authentification:** Requise

**Paramètres:**
- `start_date` (date): Date de début
- `end_date` (date): Date de fin
- `status` (string): Filtrer par statut
- `payment_type` (string): Filtrer par type

**Réponse (200 OK):**
```json
{
  "count": 25,
  "total_amount": "549.95",
  "currency": "EUR",
  "results": [
    {
      "id": "uuid",
      "amount": "99.99",
      "currency": "EUR",
      "status": "COMPLETED",
      "payment_type": "SUBSCRIPTION",
      "description": "Abonnement Premium",
      "completed_at": "2024-01-15T10:05:00Z"
    }
  ],
  "summary": {
    "total_subscriptions": "199.98",
    "total_investments": "300.00",
    "total_tips": "49.97",
    "successful_payments": 23,
    "failed_payments": 2
  }
}
```

### 6.2 GET /balance/
**Description:** Solde du compte My-CoolPay (administrateurs uniquement)

**Authentification:** Requise (admin)

**Réponse (200 OK):**
```json
{
  "balances": [
    {
      "currency": "XAF",
      "available": "1250000.00",
      "pending": "50000.00",
      "total": "1300000.00"
    },
    {
      "currency": "EUR",
      "available": "1850.50",
      "pending": "150.00",
      "total": "2000.50"
    }
  ],
  "last_updated": "2024-01-20T16:00:00Z"
}
```

---

## 7. Webhooks et callbacks

### 7.1 POST /mycoolpay/callback/
**Description:** Callback My-CoolPay pour les paiements (usage interne)

**Authentification:** Non requise (IP whitelistée)

**Note:** Endpoint utilisé par My-CoolPay pour notifier les changements de statut

### 7.2 POST /mycoolpay/webhook/
**Description:** Webhook My-CoolPay pour les événements (usage interne)

**Authentification:** Non requise (signature vérifiée)

**Note:** Endpoint pour les événements webhook de My-CoolPay

---

## Devises et conversions

### Devises supportées:
```json
{
  "XAF": {
    "name": "Franc CFA",
    "symbol": "FCFA",
    "decimal_places": 0
  },
  "EUR": {
    "name": "Euro",
    "symbol": "€",
    "decimal_places": 2
  },
  "USD": {
    "name": "Dollar US",
    "symbol": "$",
    "decimal_places": 2
  },
  "XOF": {
    "name": "Franc CFA Ouest",
    "symbol": "FCFA",
    "decimal_places": 0
  }
}
```

### Taux de change (indicatifs):
- 1 EUR ≈ 655 XAF
- 1 USD ≈ 600 XAF
- 1 EUR ≈ 1.10 USD

---

## Opérateurs de paiement mobile

### Cameroun:
- **CM_OM:** Orange Money Cameroun
- **CM_MOMO:** MTN Mobile Money Cameroun

### Sénégal:
- **SN_OM:** Orange Money Sénégal

### Côte d'Ivoire:
- **CI_OM:** Orange Money Côte d'Ivoire

### International:
- **EU_CARD:** Cartes bancaires européennes

---

## Gestion des erreurs

### Codes d'erreur spécifiques:
- `PAYMENT_001`: Montant invalide
- `PAYMENT_002`: Devise non supportée
- `PAYMENT_003`: Méthode de paiement indisponible
- `PAYMENT_004`: Solde insuffisant
- `PAYMENT_005`: Limite de transaction dépassée
- `PAYMENT_006`: OTP invalide ou expiré
- `PAYMENT_007`: Transaction déjà traitée
- `PAYMENT_008`: Opérateur temporairement indisponible

### Exemple d'erreur:
```json
{
  "error": {
    "code": "PAYMENT_004",
    "message": "Solde insuffisant pour effectuer cette transaction",
    "details": {
      "required_amount": "10000",
      "available_balance": "5000",
      "currency": "XAF"
    },
    "retry_after": 3600
  }
}
```

---

## Intégration frontend

### Exemple de création d'abonnement:
```dart
// Création d'un abonnement avec paiement
Future<SubscriptionResult> createSubscription({
  required String planId,
  required String currency,
  required String paymentMethod,
  required String phoneNumber,
}) async {
  final response = await http.post(
    Uri.parse('${baseUrl}/payments/subscription/create/'),
    headers: {...authHeaders, 'Content-Type': 'application/json'},
    body: json.encode({
      'plan_id': planId,
      'billing_currency': currency,
      'payment_method': paymentMethod,
      'phone_number': phoneNumber,
      'return_url': '${appUrl}/subscription/success',
      'cancel_url': '${appUrl}/subscription/cancel',
    }),
  );
  
  if (response.statusCode == 201) {
    final data = json.decode(response.body);
    return SubscriptionResult.fromJson(data);
  }
  throw Exception('Failed to create subscription');
}
```

### Exemple de paiement direct:
```dart
// Paiement direct avec OTP
Future<PaymentResult> initiateDirectPayment({
  required double amount,
  required String currency,
  required String phoneNumber,
  required String operator,
  required String description,
}) async {
  // 1. Initier le paiement
  final initiateResponse = await http.post(
    Uri.parse('${baseUrl}/payments/payin/'),
    headers: {...authHeaders, 'Content-Type': 'application/json'},
    body: json.encode({
      'amount': amount.toString(),
      'currency': currency,
      'phone_number': phoneNumber,
      'operator': operator,
      'description': description,
      'customer_name': currentUser.fullName,
      'customer_email': currentUser.email,
    }),
  );
  
  if (initiateResponse.statusCode == 200) {
    final data = json.decode(initiateResponse.body);
    
    if (data['status'] == 'REQUIRE_OTP') {
      // 2. Demander le code OTP à l'utilisateur
      final otpCode = await showOtpDialog();
      
      // 3. Autoriser avec OTP
      final authorizeResponse = await http.post(
        Uri.parse('${baseUrl}/payments/authorize/'),
        headers: {...authHeaders, 'Content-Type': 'application/json'},
        body: json.encode({
          'transaction_ref': data['transaction_ref'],
          'otp_code': otpCode,
        }),
      );
      
      if (authorizeResponse.statusCode == 200) {
        return PaymentResult.fromJson(json.decode(authorizeResponse.body));
      }
    }
  }
  
  throw Exception('Payment failed');
}
```

### Gestion des webhooks:
```dart
// Écouter les mises à jour de paiement via WebSocket ou polling
class PaymentStatusMonitor {
  Timer? _statusTimer;
  
  void startMonitoring(String paymentId) {
    _statusTimer = Timer.periodic(Duration(seconds: 5), (timer) async {
      try {
        final status = await checkPaymentStatus(paymentId);
        
        if (status.isCompleted || status.isFailed) {
          timer.cancel();
          onPaymentStatusChanged(status);
        }
      } catch (e) {
        // Gérer les erreurs de réseau
      }
    });
  }
  
  Future<PaymentStatus> checkPaymentStatus(String paymentId) async {
    final response = await http.get(
      Uri.parse('${baseUrl}/payments/$paymentId/status/'),
      headers: authHeaders,
    );
    
    if (response.statusCode == 200) {
      return PaymentStatus.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to check payment status');
  }
}
```

---

## Sécurité et conformité

### Mesures de sécurité:
1. **Chiffrement:** Toutes les communications via HTTPS/TLS
2. **Authentification:** JWT tokens avec expiration
3. **Validation:** Vérification des signatures webhook
4. **Audit:** Logs complets de toutes les transactions
5. **PCI DSS:** Conformité pour les données de carte

### Données sensibles:
- **Jamais stockées:** Numéros de carte, codes PIN, OTP
- **Chiffrées:** Informations personnelles, métadonnées
- **Tokenisées:** Références de paiement externes

### Limites de sécurité:
- **Tentatives OTP:** Maximum 3 par transaction
- **Montants:** Limites par méthode de paiement
- **Fréquence:** Rate limiting sur les API
- **Géolocalisation:** Restrictions par pays si nécessaire

---

## Notes importantes

1. **Environnement:** Utilisez le sandbox pour le développement
2. **Webhooks:** Configurez les URLs de callback correctement
3. **Devises:** Respectez les décimales (XAF sans décimales, EUR/USD avec 2 décimales)
4. **OTP:** Codes valides pendant 5 minutes maximum
5. **Retry:** Implémentez une logique de retry pour les échecs temporaires
6. **Monitoring:** Surveillez les statuts de paiement en temps réel
7. **Support:** Logs détaillés pour le debugging et le support client
8. **Conformité:** Respectez les réglementations locales sur les paiements