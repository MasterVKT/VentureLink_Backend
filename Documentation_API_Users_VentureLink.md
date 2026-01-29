# Documentation API Users VentureLink

## Vue d'ensemble

L'application **Users** de VentureLink gère l'authentification, les profils utilisateurs, les abonnements premium et toutes les fonctionnalités liées aux comptes utilisateurs. Elle constitue le cœur du système d'identité de la plateforme.

### Base URL
- **Développement:** `https://api-dev.venturelink.com/api/v1/`
- **Production:** `https://api.venturelink.com/api/v1/`

### Authentification
La plupart des endpoints nécessitent une authentification JWT via l'en-tête:
```
Authorization: Bearer {token}
```

---

## Modèles de données

### User (Utilisateur)
Modèle utilisateur personnalisé avec les champs suivants:
- **Types d'utilisateur:** `INVESTOR`, `PROJECT_OWNER`, `BOTH`, `ADMIN`
- **Types de compte:** `PERSONAL`, `BUSINESS`
- **Langues:** `fr`, `en`
- **Champs:** email, prénom, nom, téléphone, localisation, devise préférée, statut vérifié/premium

### Profile (Profil utilisateur)
Informations détaillées du profil:
- Photos de profil et de couverture
- Informations professionnelles (bio, titre, site web)
- Réseaux sociaux (LinkedIn, Twitter, Facebook)
- Statistiques (vues, note moyenne, niveau de vérification)

### CompanyProfile (Profil entreprise)
Pour les comptes business:
- Informations entreprise (nom, raison sociale, secteur)
- Logo et description
- Taille et stade de l'entreprise
- Informations financières (CA, financement)
- Statut de vérification

### Subscription (Abonnement)
Gestion des abonnements premium:
- **Plans:** `FREE`, `PREMIUM_MONTHLY`, `PREMIUM_YEARLY`
- **Statuts:** `ACTIVE`, `CANCELLED`, `EXPIRED`, `TRIAL`
- Dates de début/fin, renouvellement automatique

---

## Endpoints d'authentification

### Base URL: `/api/v1/auth/`

#### 1. POST /auth/register
**Description:** Inscription d'un nouvel utilisateur

**Authentification:** Non requise

**Requête:**
```json
{
  "email": "user@example.com",
  "password": "MotDePasse123!",
  "password_confirmation": "MotDePasse123!",
  "first_name": "Jean",
  "last_name": "Dupont",
  "account_type": "PERSONAL",
  "user_type": "BOTH",
  "terms_accepted": true
}
```

**Réponse (201 Created):**
```json
{
  "message": "Inscription réussie. Veuillez vérifier votre adresse e-mail pour activer votre compte."
}
```

#### 2. POST /auth/register/business
**Description:** Inscription d'un utilisateur entreprise

**Authentification:** Non requise

**Requête:**
```json
{
  "email": "company@example.com",
  "password": "MotDePasse123!",
  "password_confirmation": "MotDePasse123!",
  "first_name": "Marie",
  "last_name": "Martin",
  "user_type": "PROJECT_OWNER",
  "terms_accepted": true,
  "company_name": "TechStartup SAS",
  "company_industry": "Technologie",
  "company_size": "STARTUP"
}
```

**Réponse (201 Created):**
```json
{
  "message": "Inscription entreprise réussie...",
  "user": {
    "id": "uuid",
    "email": "company@example.com",
    "first_name": "Marie",
    "last_name": "Martin",
    "account_type": "BUSINESS",
    "user_type": "PROJECT_OWNER",
    "is_verified": false,
    "is_premium": false
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "company_profile": {
    "id": "uuid",
    "company_name": "TechStartup SAS",
    "industry": "Technologie",
    "company_size": "STARTUP"
  }
}
```

#### 3. POST /auth/token/
**Description:** Connexion avec email/mot de passe

**Authentification:** Non requise

**Requête:**
```json
{
  "email": "user@example.com",
  "password": "MotDePasse123!"
}
```

**Réponse (200 OK):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

#### 4. POST /auth/token/refresh/
**Description:** Rafraîchissement du token d'accès

**Authentification:** Non requise

**Requête:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Réponse (200 OK):**
```json
{
  "access": "new_jwt_access_token"
}
```

#### 5. POST /auth/firebase/
**Description:** Authentification via Firebase

**Authentification:** Non requise

**Requête:**
```json
{
  "firebase_token": "firebase_id_token",
  "profile_data": {
    "phone_number": "+33123456789",
    "location": "Paris, France"
  }
}
```

**Réponse (200 OK):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@gmail.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "account_type": "PERSONAL",
    "user_type": "BOTH",
    "is_verified": false,
    "is_premium": false
  },
  "is_new_user": true
}
```

#### 6. POST /auth/logout/
**Description:** Déconnexion (invalidation du token)

**Authentification:** Requise

**Requête:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Réponse (200 OK):**
```json
{
  "message": "Déconnexion réussie."
}
```

#### 7. POST /auth/password-reset/
**Description:** Demande de réinitialisation de mot de passe

**Authentification:** Non requise

**Requête:**
```json
{
  "email": "user@example.com"
}
```

**Réponse (200 OK):**
```json
{
  "message": "Si cette adresse email est associée à un compte, un email de réinitialisation a été envoyé."
}
```

---

## Endpoints utilisateurs

### Base URL: `/api/v1/users/`

#### 1. GET /users/me/
**Description:** Récupère les informations de l'utilisateur connecté

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "account_type": "PERSONAL",
  "user_type": "BOTH",
  "phone_number": "+33123456789",
  "location": "Paris, France",
  "language": "fr",
  "preferred_currency": "EUR",
  "is_verified": true,
  "is_premium": false,
  "fcm_token": "firebase_token",
  "date_joined": "2024-01-15T10:00:00Z"
}
```

#### 2. PUT /users/me/
**Description:** Met à jour les informations de l'utilisateur connecté

**Authentification:** Requise

**Requête:**
```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "phone_number": "+33123456789",
  "location": "Lyon, France",
  "language": "fr",
  "preferred_currency": "EUR",
  "fcm_token": "new_firebase_token"
}
```

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "account_type": "PERSONAL",
  "user_type": "BOTH",
  "phone_number": "+33123456789",
  "location": "Lyon, France",
  "language": "fr",
  "preferred_currency": "EUR",
  "is_verified": true,
  "is_premium": false,
  "fcm_token": "new_firebase_token",
  "date_joined": "2024-01-15T10:00:00Z"
}
```

#### 3. POST /users/me/change_password/
**Description:** Change le mot de passe de l'utilisateur

**Authentification:** Requise

**Requête:**
```json
{
  "current_password": "AncienMotDePasse123!",
  "new_password": "NouveauMotDePasse123!"
}
```

**Réponse (200 OK):**
```json
{
  "message": "Mot de passe modifié avec succès."
}
```

---

## Endpoints profils

### Base URL: `/api/v1/profiles/`

#### 1. GET /profiles/me/
**Description:** Récupère le profil de l'utilisateur connecté

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
  "profile_picture": "https://example.com/media/profile_pictures/image.jpg",
  "cover_picture": "https://example.com/media/cover_pictures/cover.jpg",
  "bio_short": "Entrepreneur passionné par l'innovation",
  "title": "CEO & Founder",
  "website": "https://www.monsite.com",
  "social_linkedin": "https://linkedin.com/in/jeandupont",
  "social_twitter": "https://twitter.com/jeandupont",
  "social_facebook": "https://facebook.com/jeandupont",
  "views_count": 1250,
  "avg_rating": 4.5,
  "rating_count": 12,
  "verification_level": "VERIFIED",
  "domain_expertise": [
    {
      "id": "uuid",
      "name": "Développement Web",
      "years_experience": 8,
      "level": "EXPERT"
    }
  ],
  "project_interests": [
    {
      "id": "uuid",
      "name": "Intelligence Artificielle",
      "level": "HIGH"
    }
  ],
  "education": [
    {
      "id": "uuid",
      "institution": "École Polytechnique",
      "degree": "Master en Informatique",
      "field_of_study": "Intelligence Artificielle",
      "start_year": "2018",
      "end_year": "2020",
      "description": "Spécialisation en machine learning"
    }
  ],
  "experience": [
    {
      "id": "uuid",
      "company": "TechCorp",
      "title": "Lead Developer",
      "location": "Paris, France",
      "current": true,
      "start_date": "2020-03",
      "end_date": null,
      "description": "Direction de l'équipe de développement"
    }
  ],
  "badges": [
    {
      "id": "uuid",
      "badge": {
        "id": "uuid",
        "name": "Verified Entrepreneur",
        "description": "Entrepreneur vérifié par VentureLink",
        "badge_type": "VERIFICATION",
        "color": "#42B72A",
        "icon": "verified"
      },
      "earned_at": "2024-01-15T10:00:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

#### 2. PUT /profiles/me/
**Description:** Met à jour le profil de l'utilisateur

**Authentification:** Requise

**Requête:**
```json
{
  "bio_short": "Entrepreneur passionné par l'innovation tech",
  "title": "CEO & Founder",
  "website": "https://www.monsite.com",
  "social_linkedin": "https://linkedin.com/in/jeandupont",
  "social_twitter": "https://twitter.com/jeandupont"
}
```

#### 3. POST /profiles/me/upload_profile_picture/
**Description:** Télécharge une photo de profil

**Authentification:** Requise

**Requête:** Form-data avec champ `profile_picture` (fichier image)

**Réponse (200 OK):**
```json
{
  "message": "Photo de profil mise à jour avec succès."
}
```

#### 4. POST /profiles/me/upload_cover_picture/
**Description:** Télécharge une photo de couverture

**Authentification:** Requise

**Requête:** Form-data avec champ `cover_picture` (fichier image)

#### 5. GET /profiles/me/expertise/
**Description:** Récupère les domaines d'expertise

**Authentification:** Requise

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "name": "Développement Web",
    "years_experience": 8,
    "level": "EXPERT",
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

#### 6. POST /profiles/me/add_expertise/
**Description:** Ajoute un domaine d'expertise

**Authentification:** Requise

**Requête:**
```json
{
  "name": "Machine Learning",
  "years_experience": 3,
  "level": "INTERMEDIATE"
}
```

---

## Endpoints abonnements

### Base URL: `/api/v1/subscriptions/`

#### 1. GET /subscriptions/plans/
**Description:** Liste les plans d'abonnement disponibles

**Authentification:** Non requise

**Réponse (200 OK):**
```json
{
  "plans": [
    {
      "id": "FREE",
      "name": "Gratuit",
      "price": 0,
      "currency": "EUR",
      "billing_cycle": "NONE",
      "features": [
        {
          "name": "Création de projets",
          "description": "Nombre de projets pouvant être créés",
          "included": true,
          "limit": 2
        },
        {
          "name": "Messages",
          "description": "Nombre de messages pouvant être envoyés par jour",
          "included": true,
          "limit": 10
        }
      ]
    },
    {
      "id": "PREMIUM_MONTHLY",
      "name": "Premium Mensuel",
      "price": 9.99,
      "currency": "EUR",
      "billing_cycle": "MONTHLY",
      "features": [
        {
          "name": "Création de projets",
          "description": "Nombre de projets pouvant être créés",
          "included": true,
          "limit": 10
        },
        {
          "name": "Messages",
          "description": "Nombre de messages pouvant être envoyés par jour",
          "included": true,
          "limit": 100
        }
      ]
    }
  ]
}
```

#### 2. GET /subscriptions/me/
**Description:** Récupère l'abonnement de l'utilisateur connecté

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "plan": "PREMIUM_MONTHLY",
  "status": "ACTIVE",
  "start_date": "2024-01-15T10:00:00Z",
  "end_date": "2024-02-15T10:00:00Z",
  "auto_renew": true,
  "payment_provider": "stripe",
  "payment_id": "sub_1234567890",
  "transactions": [
    {
      "id": "uuid",
      "amount": 9.99,
      "currency": "EUR",
      "transaction_id": "tx_1234567890",
      "payment_method": "card",
      "status": "COMPLETED",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### 3. POST /subscriptions/checkout/
**Description:** Initie le processus de souscription à un plan premium

**Authentification:** Requise

**Requête:**
```json
{
  "plan": "PREMIUM_MONTHLY",
  "payment_method": "card",
  "success_url": "https://app.venturelink.com/subscription/success",
  "cancel_url": "https://app.venturelink.com/subscription/cancel"
}
```

**Réponse (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_1234567890",
  "checkout_session_id": "cs_1234567890"
}
```

#### 4. POST /subscriptions/me/cancel/
**Description:** Annule l'abonnement de l'utilisateur

**Authentification:** Requise

**Requête:**
```json
{
  "reason": "Too expensive",
  "feedback": "Optional feedback"
}
```

**Réponse (200 OK):**
```json
{
  "message": "Abonnement annulé avec succès. Il restera actif jusqu'au 2024-02-15."
}
```

---

## Endpoints profils d'entreprise

### Base URL: `/api/v1/companies/`

#### 1. GET /my-company/
**Description:** Récupère le profil entreprise de l'utilisateur connecté

**Authentification:** Requise (compte business uniquement)

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "email": "company@example.com",
    "first_name": "Marie",
    "last_name": "Martin"
  },
  "company_name": "TechStartup SAS",
  "legal_name": "TechStartup Société par Actions Simplifiée",
  "registration_number": "12345678901234",
  "vat_number": "FR12345678901",
  "legal_form": "SAS",
  "logo": "https://example.com/media/company_logos/logo.png",
  "description": "Startup spécialisée dans les solutions IA",
  "mission_statement": "Démocratiser l'intelligence artificielle",
  "industry": "Technologie",
  "specialties": "IA, Machine Learning, Automatisation",
  "company_size": "STARTUP",
  "employee_count": 8,
  "company_stage": "EARLY_STAGE",
  "founded_year": 2023,
  "headquarters_address": "123 Rue de la Tech, 75001 Paris",
  "website": "https://www.techstartup.com",
  "linkedin_company": "https://linkedin.com/company/techstartup",
  "twitter_company": "https://twitter.com/techstartup",
  "facebook_company": "https://facebook.com/techstartup",
  "annual_revenue": 500000.00,
  "funding_stage": "Série A",
  "total_funding": 2000000.00,
  "is_verified": true,
  "members": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "first_name": "Marie",
        "last_name": "Martin"
      },
      "role": "CEO",
      "title": "Chief Executive Officer",
      "status": "ACTIVE",
      "is_admin": true,
      "start_date": "2023-01-01"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

#### 2. PUT /my-company/
**Description:** Met à jour le profil entreprise

**Authentification:** Requise (compte business)

**Requête:**
```json
{
  "company_name": "TechStartup SAS",
  "description": "Startup spécialisée dans les solutions IA avancées",
  "industry": "Intelligence Artificielle",
  "company_size": "SMALL",
  "employee_count": 15,
  "website": "https://www.techstartup.com"
}
```

---

## Gestion des erreurs

### Codes d'erreur standardisés

#### Erreurs d'authentification (400-401)
```json
{
  "error": "Token d'authentification manquant ou invalide"
}
```

#### Erreurs de validation (400)
```json
{
  "error": {
    "email": ["Un utilisateur avec cette adresse email existe déjà."],
    "password": ["Le mot de passe doit contenir au moins 8 caractères."]
  }
}
```

#### Erreurs d'autorisation (403)
```json
{
  "error": "Vous n'êtes pas autorisé à effectuer cette action"
}
```

#### Ressource non trouvée (404)
```json
{
  "error": "Profil non trouvé"
}
```

---

## Fonctionnalités automatiques

### Signaux Django
L'application Users utilise des signaux pour automatiser certaines actions:

- **Création automatique de profil:** Un profil est créé automatiquement lors de l'inscription
- **Création automatique de profil entreprise:** Pour les comptes business
- **Mise à jour du statut premium:** Lors des changements d'abonnement

### Validation des données
- **Mots de passe:** Minimum 8 caractères, majuscule, chiffre
- **URLs réseaux sociaux:** Validation des formats LinkedIn, Twitter, Facebook
- **Dates:** Validation des formats et cohérence temporelle
- **Images:** Validation des formats et tailles

---

## Support multi-devises

L'application supporte plusieurs devises via le champ `preferred_currency`:
- EUR (Euro) - devise par défaut
- USD (Dollar américain)
- GBP (Livre sterling)
- CAD (Dollar canadien)
- CHF (Franc suisse)

---

## Limitations et permissions

### Plans gratuits vs Premium
| Fonctionnalité | Gratuit | Premium Mensuel | Premium Annuel |
|---|---|---|---|
| Projets créés | 2 | 10 | Illimité |
| Messages/jour | 10 | 100 | Illimité |
| Recherche avancée | ❌ | ✅ | ✅ |
| Mise en avant | ❌ | 1 projet | 3 projets |

### Permissions par type de compte
- **Personnel:** Accès aux fonctionnalités de base
- **Entreprise:** + Profil entreprise, gestion d'équipe
- **Administrateur:** Accès complet, gestion plateforme

---

## Intégration frontend

### Gestion de l'authentification
```dart
// Connexion
final response = await http.post(
  Uri.parse('${baseUrl}/auth/token/'),
  headers: {'Content-Type': 'application/json'},
  body: json.encode({
    'email': email,
    'password': password,
  }),
);

if (response.statusCode == 200) {
  final data = json.decode(response.body);
  // Stocker les tokens
  await storage.write(key: 'access_token', value: data['access']);
  await storage.write(key: 'refresh_token', value: data['refresh']);
}
```

### Rafraîchissement automatique des tokens
```dart
// Intercepteur pour rafraîchir automatiquement les tokens
class AuthInterceptor extends Interceptor {
  @override
  void onError(DioError err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token expiré, tenter de le rafraîchir
      final refreshed = await refreshToken();
      if (refreshed) {
        // Relancer la requête avec le nouveau token
        final response = await dio.fetch(err.requestOptions);
        handler.resolve(response);
        return;
      }
    }
    handler.next(err);
  }
}
```

### Gestion des profils
```dart
// Récupération du profil utilisateur
Future<UserProfile> getUserProfile() async {
  final response = await http.get(
    Uri.parse('${baseUrl}/profiles/me/'),
    headers: {
      'Authorization': 'Bearer $accessToken',
      'Content-Type': 'application/json',
    },
  );

  if (response.statusCode == 200) {
    return UserProfile.fromJson(json.decode(response.body));
  }
  throw Exception('Failed to load profile');
}
```

---

## Notes importantes

1. **Sécurité:** Tous les mots de passe sont hachés avec Django's PBKDF2
2. **Upload de fichiers:** Les images sont redimensionnées et optimisées automatiquement
3. **Cache:** Les profils sont mis en cache pour améliorer les performances
4. **Rate limiting:** Protection contre les attaques par force brute
5. **RGPD:** Conformité avec les réglementations sur la protection des données
6. **Internationalisation:** Support complet français/anglais
7. **Firebase Auth:** Intégration complète pour l'authentification sociale
8. **Webhooks:** Support des notifications de paiement en temps réel