# Documentation de l'Application Core - VentureLink

## Vue d'ensemble

L'application **Core** de VentureLink constitue la fondation technique de la plateforme, fournissant tous les composants transversaux, utilitaires et services partagés utilisés par les autres applications. Elle inclut l'authentification Firebase, la gestion des devises, les middlewares personnalisés, les permissions, les exceptions et les tâches de maintenance.

## Architecture du système

### Modèles de base abstraits

#### 1. TimeStampedModel
Modèle abstrait fournissant des champs de suivi temporel automatiques.

**Champs :**
- `created_at` : Date de création (auto_now_add=True)
- `updated_at` : Date de modification (auto_now=True)

**Usage :**
```python
class MonModele(TimeStampedModel):
    # Hérite automatiquement des champs created_at et updated_at
    nom = models.CharField(max_length=100)
```

#### 2. UUIDModel
Modèle abstrait utilisant UUID comme clé primaire.

**Champs :**
- `id` : UUID v4 comme clé primaire

**Usage :**
```python
class MonModele(UUIDModel, TimeStampedModel):
    # Hérite d'un ID UUID et des timestamps
    nom = models.CharField(max_length=100)
```

#### 3. MoneyField
Champ personnalisé pour les valeurs monétaires.

**Caractéristiques :**
- 14 chiffres maximum, 2 décimales
- Validation automatique (valeur >= 0)
- Support des devises multiples

### Services principaux

#### CurrencyService
Service complet de gestion des devises et conversions.

**Fonctionnalités :**
- Récupération des taux de change via API externe
- Conversion automatique entre devises
- Cache des taux (24h par défaut)
- Support de 20+ devises principales
- Formatage localisé des montants

**Méthodes principales :**
- `get_exchange_rates(base_currency)` : Récupère les taux de change
- `convert_currency(amount, from_currency, to_currency)` : Convertit un montant
- `get_available_currencies()` : Liste des devises supportées
- `format_currency(amount, currency)` : Formate un montant avec symbole

#### MyCoolPayService
Service d'intégration avec l'API de paiement My-CoolPay.

**Fonctionnalités :**
- Support sandbox et production
- Création et gestion des paiements
- Vérification des statuts de paiement
- Gestion des remboursements
- Validation des webhooks
- Sécurité et authentification API

**Méthodes principales :**
- `create_payment()` : Crée un nouveau paiement
- `get_payment_status()` : Vérifie le statut d'un paiement
- `refund_payment()` : Effectue un remboursement
- `verify_webhook_signature()` : Valide les webhooks

### Middlewares personnalisés

#### 1. FirebaseAuthenticationMiddleware
Authentification automatique via tokens Firebase JWT.

**Fonctionnalités :**
- Vérification des tokens Firebase dans l'en-tête Authorization
- Authentification transparente des utilisateurs
- Support du mode développement avec vérification basique
- Logging détaillé des authentifications

#### 2. CurrencyConversionMiddleware
Conversion automatique des valeurs monétaires dans les réponses API.

**Fonctionnalités :**
- Détection automatique des champs monétaires
- Conversion selon les préférences utilisateur
- Support des paramètres de requête pour la devise
- Conservation des valeurs originales pour référence

#### 3. RequestLoggingMiddleware
Logging détaillé des requêtes HTTP.

**Fonctionnalités :**
- Enregistrement des temps de réponse
- Logging des adresses IP clients
- Métriques de performance
- Détection des erreurs

### Système de permissions

#### Permissions de base
- `IsOwner` : Propriétaire uniquement
- `IsOwnerOrAdmin` : Propriétaire ou administrateur
- `IsOwnerOrReadOnly` : Propriétaire pour modification, lecture pour tous
- `IsAdminUser` : Administrateurs uniquement
- `ReadOnly` : Lecture seule

#### Permissions métier
- `IsProjectOwner` : Créateur du projet
- `IsInvestorOrProjectCreator` : Investisseur ou créateur du projet
- `IsPremiumUser` : Utilisateurs premium uniquement
- `IsVerifiedUser` : Utilisateurs vérifiés uniquement

### Gestion des exceptions

#### Exceptions personnalisées
- `VentureLinkException` : Exception de base
- `AuthenticationError` : Erreurs d'authentification
- `InvalidCredentialsError` : Identifiants invalides
- `TokenError` : Tokens invalides/expirés
- `PermissionDeniedError` : Permissions insuffisantes
- `ResourceNotFoundError` : Ressource introuvable
- `ValidationError` : Erreurs de validation
- `RateLimitExceededError` : Limite de requêtes dépassée
- `SubscriptionRequiredError` : Abonnement requis
- `PaymentError` : Erreurs de paiement

#### Gestionnaire d'exceptions personnalisé
Formatage standardisé des erreurs API :
```json
{
  "error": {
    "status_code": 400,
    "error_code": "VALIDATION_ERROR",
    "message": "Les données fournies sont invalides",
    "details": [
      {
        "field": "email",
        "message": "Ce champ est requis"
      }
    ]
  }
}
```

### Utilitaires Firebase

#### Fonctionnalités
- Vérification des tokens ID Firebase
- Récupération des informations utilisateur
- Création de tokens personnalisés
- Envoi de notifications push
- Mode développement avec vérification basique

#### Méthodes principales
- `verify_firebase_token(id_token)` : Vérifie un token Firebase
- `get_firebase_user(uid)` : Récupère un utilisateur par UID
- `create_firebase_custom_token(uid, claims)` : Crée un token personnalisé
- `send_firebase_notification(token, title, body, data)` : Envoie une notification

### Tâches Celery

#### Tâches d'analytics
- `update_daily_analytics()` : Métriques quotidiennes
- `generate_user_engagement_report()` : Rapport d'engagement
- `generate_financial_analytics()` : Analytics financières
- `generate_weekly_summary_report()` : Rapport hebdomadaire

#### Tâches de maintenance
- `cleanup_old_analytics_data()` : Nettoyage des anciennes données
- `send_analytics_to_external_service()` : Envoi vers services externes
- `send_weekly_report_email()` : Envoi des rapports par email

## Endpoints de l'API

### 1. Gestion des devises

#### GET /api/core/currencies/
**Description :** Liste des devises disponibles avec leurs symboles

**Permissions :** Aucune (AllowAny)

**Réponse :**
```json
{
  "currencies": [
    {
      "code": "EUR",
      "name": "Euro",
      "symbol": "€"
    },
    {
      "code": "USD",
      "name": "Dollar américain",
      "symbol": "$"
    },
    {
      "code": "GBP",
      "name": "Livre sterling",
      "symbol": "£"
    }
  ],
  "default_currency": "EUR"
}
```

### 2. Test et monitoring

#### GET /api/core/test-sentry/
**Description :** Endpoint de test pour Sentry (génère une exception intentionnelle)

**Permissions :** Aucune (AllowAny)

**Usage :** Uniquement pour tester l'intégration Sentry

## Configuration et intégration

### Variables d'environnement requises

#### Firebase
```env
# Configuration Firebase (optionnelle en développement)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
```

#### My-CoolPay
```env
# Mode sandbox (développement)
PAYMENT_SANDBOX_MODE=True
MYCOOLPAY_SANDBOX_API_KEY=your-sandbox-api-key
MYCOOLPAY_SANDBOX_WEBHOOK_SECRET=your-sandbox-webhook-secret

# Mode production
MYCOOLPAY_PRODUCTION_API_KEY=your-production-api-key
MYCOOLPAY_PRODUCTION_WEBHOOK_SECRET=your-production-webhook-secret
```

#### Devises
```env
# API de taux de change
EXCHANGE_RATE_API_KEY=your-exchange-rate-api-key
EXCHANGE_RATE_API_URL=https://api.exchangerate-api.com/v4/latest/
DEFAULT_CURRENCY=EUR
```

#### Analytics
```env
# Webhook pour analytics externes (optionnel)
ANALYTICS_WEBHOOK_URL=https://your-analytics-service.com/webhook
```

### Configuration Django

#### settings.py
```python
# Middleware personnalisés
MIDDLEWARE = [
    # ... autres middlewares
    'apps.core.middleware.FirebaseAuthenticationMiddleware',
    'apps.core.middleware.CurrencyConversionMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
]

# Gestionnaire d'exceptions personnalisé
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    # ... autres configurations
}

# Configuration des devises
DEFAULT_CURRENCY = 'EUR'
SUPPORTED_CURRENCIES = ['EUR', 'USD', 'GBP', 'CAD', 'CHF']

# Configuration Firebase
FIREBASE_CONFIG = {
    'projectId': 'your-project-id',
    'apiKey': 'your-api-key',
    # ... autres configurations
}
```

## Intégration Frontend (Flutter/Dart)

### Service de devises

```dart
class CurrencyService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Récupérer les devises disponibles
  static Future<List<Currency>> getAvailableCurrencies() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/core/currencies/'),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['currencies'] as List)
          .map((json) => Currency.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement devises');
  }
  
  // Convertir un montant (côté client pour affichage)
  static double convertAmount(
    double amount,
    String fromCurrency,
    String toCurrency,
    Map<String, double> exchangeRates,
  ) {
    if (fromCurrency == toCurrency) return amount;
    
    final fromRate = exchangeRates[fromCurrency] ?? 1.0;
    final toRate = exchangeRates[toCurrency] ?? 1.0;
    
    // Convertir vers EUR puis vers la devise cible
    final eurAmount = amount / fromRate;
    return eurAmount * toRate;
  }
  
  // Formater un montant avec symbole de devise
  static String formatCurrency(double amount, String currency) {
    final formatter = NumberFormat.currency(
      symbol: getCurrencySymbol(currency),
      decimalDigits: 2,
    );
    return formatter.format(amount);
  }
  
  static String getCurrencySymbol(String currency) {
    const symbols = {
      'EUR': '€',
      'USD': '\$',
      'GBP': '£',
      'JPY': '¥',
      'CAD': 'CA\$',
      'AUD': 'A\$',
      'CHF': 'CHF',
    };
    return symbols[currency] ?? currency;
  }
}

class Currency {
  final String code;
  final String name;
  final String symbol;
  
  Currency({
    required this.code,
    required this.name,
    required this.symbol,
  });
  
  factory Currency.fromJson(Map<String, dynamic> json) {
    return Currency(
      code: json['code'],
      name: json['name'],
      symbol: json['symbol'],
    );
  }
  
  @override
  String toString() => '$name ($code)';
}
```

### Gestion des erreurs

```dart
class ApiException implements Exception {
  final int statusCode;
  final String errorCode;
  final String message;
  final List<FieldError>? details;
  
  ApiException({
    required this.statusCode,
    required this.errorCode,
    required this.message,
    this.details,
  });
  
  factory ApiException.fromJson(Map<String, dynamic> json) {
    final error = json['error'];
    return ApiException(
      statusCode: error['status_code'],
      errorCode: error['error_code'],
      message: error['message'],
      details: error['details'] != null
          ? (error['details'] as List)
              .map((detail) => FieldError.fromJson(detail))
              .toList()
          : null,
    );
  }
  
  @override
  String toString() => message;
}

class FieldError {
  final String field;
  final String message;
  
  FieldError({
    required this.field,
    required this.message,
  });
  
  factory FieldError.fromJson(Map<String, dynamic> json) {
    return FieldError(
      field: json['field'],
      message: json['message'],
    );
  }
}

// Intercepteur HTTP pour gérer les erreurs standardisées
class ApiErrorInterceptor extends Interceptor {
  @override
  void onError(DioError err, ErrorInterceptorHandler handler) {
    if (err.response?.data != null && err.response?.data['error'] != null) {
      final apiException = ApiException.fromJson(err.response!.data);
      handler.reject(DioError(
        requestOptions: err.requestOptions,
        error: apiException,
        response: err.response,
        type: err.type,
      ));
    } else {
      handler.next(err);
    }
  }
}
```

### Authentification Firebase

```dart
class FirebaseAuthService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Obtenir les en-têtes d'authentification avec token Firebase
  static Future<Map<String, String>> getAuthHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw Exception('Utilisateur non authentifié');
    }
    
    final idToken = await user.getIdToken();
    
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Firebase $idToken',
    };
  }
  
  // Vérifier si l'utilisateur est authentifié
  static bool get isAuthenticated {
    return FirebaseAuth.instance.currentUser != null;
  }
  
  // Écouter les changements d'état d'authentification
  static Stream<User?> get authStateChanges {
    return FirebaseAuth.instance.authStateChanges();
  }
  
  // Se connecter avec email/mot de passe
  static Future<UserCredential> signInWithEmailAndPassword(
    String email,
    String password,
  ) async {
    try {
      return await FirebaseAuth.instance.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
    } on FirebaseAuthException catch (e) {
      throw _handleFirebaseAuthException(e);
    }
  }
  
  // S'inscrire avec email/mot de passe
  static Future<UserCredential> createUserWithEmailAndPassword(
    String email,
    String password,
  ) async {
    try {
      return await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
    } on FirebaseAuthException catch (e) {
      throw _handleFirebaseAuthException(e);
    }
  }
  
  // Se déconnecter
  static Future<void> signOut() async {
    await FirebaseAuth.instance.signOut();
  }
  
  // Gérer les exceptions Firebase Auth
  static Exception _handleFirebaseAuthException(FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
        return Exception('Aucun utilisateur trouvé avec cet email');
      case 'wrong-password':
        return Exception('Mot de passe incorrect');
      case 'email-already-in-use':
        return Exception('Un compte existe déjà avec cet email');
      case 'weak-password':
        return Exception('Le mot de passe est trop faible');
      case 'invalid-email':
        return Exception('Adresse email invalide');
      default:
        return Exception('Erreur d\'authentification: ${e.message}');
    }
  }
}
```

### Widget de sélection de devise

```dart
class CurrencySelector extends StatefulWidget {
  final String selectedCurrency;
  final Function(String) onCurrencyChanged;
  final List<Currency> availableCurrencies;
  
  const CurrencySelector({
    Key? key,
    required this.selectedCurrency,
    required this.onCurrencyChanged,
    required this.availableCurrencies,
  }) : super(key: key);
  
  @override
  _CurrencySelectorState createState() => _CurrencySelectorState();
}

class _CurrencySelectorState extends State<CurrencySelector> {
  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: widget.selectedCurrency,
      decoration: InputDecoration(
        labelText: 'Devise',
        prefixIcon: Icon(Icons.attach_money),
        border: OutlineInputBorder(),
      ),
      items: widget.availableCurrencies.map((currency) {
        return DropdownMenuItem<String>(
          value: currency.code,
          child: Row(
            children: [
              Text(
                currency.symbol,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
              SizedBox(width: 8),
              Text(currency.name),
              Spacer(),
              Text(
                currency.code,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        );
      }).toList(),
      onChanged: (String? newValue) {
        if (newValue != null) {
          widget.onCurrencyChanged(newValue);
        }
      },
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Veuillez sélectionner une devise';
        }
        return null;
      },
    );
  }
}
```

## Commandes de gestion Django

### Vérification de l'environnement

```bash
# Vérifier le statut de l'environnement
python manage.py env_status
```

Cette commande vérifie :
- Configuration Firebase
- Configuration My-CoolPay
- Configuration des devises
- Connectivité aux services externes
- État des tâches Celery

## Monitoring et logs

### Logs disponibles
- Authentifications Firebase (succès/échecs)
- Conversions de devises
- Requêtes API My-CoolPay
- Erreurs de middleware
- Métriques de performance

### Métriques recommandées
- Temps de réponse des APIs
- Taux d'erreur par endpoint
- Utilisation des devises
- Volume des conversions
- Performance des tâches Celery

## Sécurité

### Bonnes pratiques implémentées
- Validation stricte des tokens Firebase
- Chiffrement des communications API
- Gestion sécurisée des clés API
- Limitation des tentatives d'authentification
- Logging des accès sensibles
- Validation des webhooks

### Configuration de sécurité
```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## Performance et optimisation

### Cache
- Taux de change mis en cache (24h)
- Tokens Firebase validés mis en cache
- Métriques d'analytics mises en cache

### Optimisations
- Requêtes API asynchrones
- Compression des réponses
- Pagination automatique
- Indexation des champs de recherche

## Tests et qualité

### Tests unitaires
```python
# Exemple de test pour CurrencyService
class CurrencyServiceTest(TestCase):
    def setUp(self):
        self.service = CurrencyService()
    
    def test_currency_conversion(self):
        # Test de conversion EUR -> USD
        result = self.service.convert_currency(100, 'EUR', 'USD')
        self.assertIsInstance(result, (int, float, Decimal))
        self.assertGreater(result, 0)
    
    def test_same_currency_conversion(self):
        # Test de conversion même devise
        result = self.service.convert_currency(100, 'EUR', 'EUR')
        self.assertEqual(result, 100)
```

### Tests d'intégration
- Tests des middlewares
- Tests des permissions
- Tests des exceptions
- Tests Firebase (mode mock)

---

**Documentation mise à jour le :** 2024-01-15  
**Version de l'API :** 1.0  
**Contact technique :** dev@venturelink.com