# Contrat d'API VentureLink

## Vue d'ensemble

Cette documentation décrit l'API REST de VentureLink, une plateforme reliant entrepreneurs et investisseurs. L'API utilise Django REST Framework avec l'authentification JWT.

### URLs de base
- **Base URL Production**: `https://api.venturelink.com`
- **Base URL Développement**: `http://localhost:8000`
- **Version API**: `v1`
- **Préfixe API**: `/api/v1/`

### Documentation interactive
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`

## Authentification

### JWT (JSON Web Tokens)
L'API utilise l'authentification JWT avec les tokens d'accès et de rafraîchissement.

#### Configuration des tokens
```json
{
  "access_token_lifetime": "1 heure",
  "refresh_token_lifetime": "14 jours",
  "algorithm": "HS256",
  "auth_header_type": "Bearer"
}
```

#### Headers requis
```
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

## Endpoints d'authentification

### Inscription
```
POST /api/v1/auth/register/
```

**Corps de la requête:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "BOTH", // "INVESTOR", "PROJECT_OWNER", "BOTH"
  "password": "SecurePassword123",
  "password_confirmation": "SecurePassword123",
  "terms_accepted": true
}
```

**Réponse (201 Created):**
```json
{
  "user": {
    "id": "uuid4",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "BOTH",
    "is_verified": false,
    "is_premium": false,
    "date_joined": "2024-01-01T12:00:00Z"
  },
  "tokens": {
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
  }
}
```

### Connexion
```
POST /api/v1/auth/token/
```

**Corps de la requête:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Réponse (200 OK):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid4",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "BOTH"
  }
}
```

### Rafraîchissement du token
```
POST /api/v1/auth/token/refresh/
```

**Corps de la requête:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Réponse (200 OK):**
```json
{
  "access": "new_jwt_access_token",
  "refresh": "new_jwt_refresh_token" // si rotation activée
}
```

### Vérification du token
```
POST /api/v1/auth/token/verify/
```

### Authentification sociale
```
POST /api/v1/auth/firebase/
POST /api/v1/auth/google/
POST /api/v1/auth/facebook/
```

### Déconnexion
```
POST /api/v1/auth/logout/
```

### Réinitialisation du mot de passe
```
POST /api/v1/auth/password-reset/
POST /api/v1/auth/password-reset/confirm/
```

### Vérification du compte
```
GET /api/v1/auth/verify-account/<token>/
POST /api/v1/auth/request-email-verification/
```

## Gestion des utilisateurs

### Profil utilisateur actuel
```
GET /api/v1/users/me/
PUT /api/v1/users/me/
PATCH /api/v1/users/me/
```

**Réponse GET (200 OK):**
```json
{
  "id": "uuid4",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "BOTH",
  "phone_number": "+33123456789",
  "location": "Paris, France",
  "language": "fr",
  "preferred_currency": "EUR",
  "is_verified": true,
  "is_premium": false,
  "fcm_token": "firebase_token",
  "date_joined": "2024-01-01T12:00:00Z",
  "profile": {
    "id": "uuid4",
    "profile_picture": "http://example.com/media/profile.jpg",
    "cover_picture": "http://example.com/media/cover.jpg",
    "bio_short": "Entrepreneur passionné",
    "title": "CEO & Founder",
    "website": "https://johndoe.com",
    "social_linkedin": "https://linkedin.com/in/johndoe",
    "social_twitter": "https://twitter.com/johndoe",
    "social_facebook": "https://facebook.com/johndoe",
    "views_count": 150,
    "avg_rating": 4.5,
    "rating_count": 10,
    "verification_level": "VERIFIED"
  }
}
```

### Changement de mot de passe
```
POST /api/v1/users/change-password/
```

**Corps de la requête:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewSecurePassword123"
}
```

### Profil détaillé
```
GET /api/v1/users/{user_id}/profile/
```

### Gestion des expertises
```
GET /api/v1/users/me/profile/expertise/
POST /api/v1/users/me/profile/expertise/
PUT /api/v1/users/me/profile/expertise/{expertise_id}/
DELETE /api/v1/users/me/profile/expertise/{expertise_id}/
```

**Corps de la requête POST/PUT:**
```json
{
  "name": "Intelligence Artificielle",
  "years_experience": 5,
  "level": "EXPERT" // "BEGINNER", "INTERMEDIATE", "EXPERT"
}
```

### Gestion de l'éducation
```
GET /api/v1/users/me/profile/education/
POST /api/v1/users/me/profile/education/
PUT /api/v1/users/me/profile/education/{education_id}/
DELETE /api/v1/users/me/profile/education/{education_id}/
```

### Gestion de l'expérience
```
GET /api/v1/users/me/profile/experience/
POST /api/v1/users/me/profile/experience/
PUT /api/v1/users/me/profile/experience/{experience_id}/
DELETE /api/v1/users/me/profile/experience/{experience_id}/
```

## Gestion des projets

### Liste des projets
```
GET /api/v1/projects/
```

**Paramètres de requête:**
- `page`: Numéro de page (défaut: 1)
- `page_size`: Taille de la page (défaut: 20, max: 100)
- `category`: ID de catégorie
- `stage`: Stade du projet (`IDEA`, `PROTOTYPE`, `DEVELOPMENT`, `GROWTH`)
- `status`: Statut (`ACTIVE`, `INACTIVE`, `FUNDED`, `ARCHIVED`)
- `funding_min`: Montant minimum de financement
- `funding_max`: Montant maximum de financement
- `location_country`: Pays
- `search`: Recherche textuelle
- `tags`: IDs des tags (séparés par des virgules)
- `is_featured`: Projets mis en avant (true/false)
- `ordering`: Tri (`-created_at`, `title`, `funding_min`, etc.)

**Réponse (200 OK):**
```json
{
  "count": 150,
  "next": "http://api.venturelink.com/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid4",
      "title": "Application IA révolutionnaire",
      "short_description": "Une application qui révolutionne l'IA",
      "category": {
        "id": "uuid4",
        "name_fr": "Intelligence Artificielle",
        "name_en": "Artificial Intelligence",
        "icon": "ai-icon"
      },
      "stage": "PROTOTYPE",
      "status": "ACTIVE",
      "funding_min": 50000.00,
      "funding_max": 200000.00,
      "funding_currency": "EUR",
      "location_country": "France",
      "location_city": "Paris",
      "is_premium": false,
      "is_featured": true,
      "views_count": 1500,
      "interests_count": 25,
      "favorites_count": 8,
      "creator": {
        "id": "uuid4",
        "email": "creator@example.com",
        "full_name": "John Doe",
        "user_type": "PROJECT_OWNER"
      },
      "primary_image": "http://example.com/media/project_image.jpg",
      "tags": [
        {
          "id": "uuid4",
          "name_fr": "IA",
          "name_en": "AI"
        }
      ],
      "created_at": "2024-01-01T12:00:00Z",
      "published_at": "2024-01-02T10:00:00Z"
    }
  ]
}
```

### Détail d'un projet
```
GET /api/v1/projects/{project_id}/
```

**Réponse (200 OK):**
```json
{
  "id": "uuid4",
  "title": "Application IA révolutionnaire",
  "short_description": "Une application qui révolutionne l'IA",
  "full_description": "Description complète du projet...",
  "category": {
    "id": "uuid4",
    "name_fr": "Intelligence Artificielle",
    "description_fr": "Projets liés à l'IA"
  },
  "stage": "PROTOTYPE",
  "status": "ACTIVE",
  "funding_min": 50000.00,
  "funding_max": 200000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Paris",
  "business_plan": "http://example.com/media/business_plan.pdf",
  "video_url": "https://youtube.com/watch?v=xxx",
  "is_premium": false,
  "is_featured": true,
  "is_draft": false,
  "views_count": 1500,
  "interests_count": 25,
  "favorites_count": 8,
  "creator": {
    "id": "uuid4",
    "email": "creator@example.com",
    "full_name": "John Doe",
    "user_type": "PROJECT_OWNER"
  },
  "media": [
    {
      "id": "uuid4",
      "file": "http://example.com/media/image1.jpg",
      "media_type": "IMAGE",
      "title": "Screenshot principal",
      "description": "Interface utilisateur principale",
      "order": 1
    }
  ],
  "tags": [
    {
      "id": "uuid4",
      "name_fr": "IA",
      "name_en": "AI"
    }
  ],
  "needs": [
    {
      "id": "uuid4",
      "need_type": "FUNDING",
      "amount": 100000.00,
      "currency": "EUR",
      "description": "Pour le développement MVP"
    }
  ],
  "skills_needed": [
    {
      "id": "uuid4",
      "skill_name": "Développement Mobile",
      "experience_level": "SENIOR",
      "is_required": true,
      "description": "Développeur React Native expérimenté"
    }
  ],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z",
  "published_at": "2024-01-02T10:00:00Z"
}
```

### Créer un projet
```
POST /api/v1/projects/
```

**Corps de la requête:**
```json
{
  "title": "Mon nouveau projet",
  "short_description": "Description courte du projet",
  "full_description": "Description détaillée...",
  "category": "uuid4",
  "stage": "IDEA",
  "funding_min": 10000.00,
  "funding_max": 50000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Lyon",
  "tags": ["uuid4", "uuid5"],
  "is_draft": true
}
```

### Modifier un projet
```
PUT /api/v1/projects/{project_id}/
PATCH /api/v1/projects/{project_id}/
```

### Supprimer un projet
```
DELETE /api/v1/projects/{project_id}/
```

### Actions sur les projets

#### Marquer comme favori
```
POST /api/v1/projects/{project_id}/toggle_favorite/
```

#### Exprimer un intérêt
```
POST /api/v1/projects/{project_id}/toggle_interest/
```

#### Publier un projet
```
POST /api/v1/projects/{project_id}/publish/
```

### Médias du projet
```
GET /api/v1/projects/{project_id}/media/
POST /api/v1/projects/{project_id}/media/
PUT /api/v1/projects/{project_id}/media/{media_id}/
DELETE /api/v1/projects/{project_id}/media/{media_id}/
```

### Catégories et tags
```
GET /api/v1/categories/
GET /api/v1/tags/
```

## Gestion des investissements

### Liste des investissements
```
GET /api/v1/investments/
```

**Paramètres de requête:**
- `investor`: ID de l'investisseur
- `project`: ID du projet
- `status`: Statut (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`, `COMPLETED`)
- `investment_type`: Type (`EQUITY`, `LOAN`, `DONATION`, `CONVERTIBLE_NOTE`)
- `amount_min`: Montant minimum
- `amount_max`: Montant maximum

**Réponse (200 OK):**
```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid4",
      "investor": {
        "id": "uuid4",
        "email": "investor@example.com",
        "full_name": "Jane Smith"
      },
      "project": {
        "id": "uuid4",
        "title": "Application IA révolutionnaire"
      },
      "amount": 25000.00,
      "currency": "EUR",
      "investment_type": "EQUITY",
      "equity_percentage": 5.0,
      "status": "APPROVED",
      "description": "Investissement stratégique",
      "approved_at": "2024-01-15T10:00:00Z",
      "created_at": "2024-01-10T12:00:00Z"
    }
  ]
}
```

### Créer un investissement
```
POST /api/v1/investments/
```

**Corps de la requête:**
```json
{
  "project": "uuid4",
  "amount": 25000.00,
  "currency": "EUR",
  "investment_type": "EQUITY",
  "equity_percentage": 5.0,
  "description": "Investissement stratégique dans l'IA"
}
```

### Détail d'un investissement
```
GET /api/v1/investments/{investment_id}/
```

### Modifier le statut d'un investissement
```
PATCH /api/v1/investments/{investment_id}/
```

**Corps de la requête:**
```json
{
  "status": "APPROVED",
  "notes": "Investissement approuvé après due diligence"
}
```

### Historique d'un investissement
```
GET /api/v1/investments/{investment_id}/history/
```

### Paiements d'un investissement
```
GET /api/v1/investments/{investment_id}/payments/
POST /api/v1/investments/{investment_id}/payments/
```

## Système de messagerie

### Conversations
```
GET /api/v1/conversations/
POST /api/v1/conversations/
GET /api/v1/conversations/{conversation_id}/
PUT /api/v1/conversations/{conversation_id}/
DELETE /api/v1/conversations/{conversation_id}/
```

**Réponse GET conversations (200 OK):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "uuid4",
      "title": "Discussion sur le projet IA",
      "conversation_type": "PROJECT",
      "status": "ACTIVE",
      "project": {
        "id": "uuid4",
        "title": "Application IA révolutionnaire"
      },
      "participants": [
        {
          "id": "uuid4",
          "user": {
            "id": "uuid4",
            "email": "user1@example.com",
            "full_name": "John Doe"
          },
          "is_admin": true,
          "last_read_at": "2024-01-15T14:30:00Z"
        }
      ],
      "last_message_at": "2024-01-15T14:35:00Z",
      "unread_count": 2,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### Messages
```
GET /api/v1/conversations/{conversation_id}/messages/
POST /api/v1/conversations/{conversation_id}/messages/
GET /api/v1/messages/{message_id}/
PUT /api/v1/messages/{message_id}/
DELETE /api/v1/messages/{message_id}/
```

**Corps de la requête POST message:**
```json
{
  "content": "Bonjour, je suis intéressé par votre projet",
  "message_type": "TEXT", // "TEXT", "IMAGE", "FILE", "AUDIO", "VIDEO"
  "attachment": null // fichier si applicable
}
```

### Marquer les messages comme lus
```
POST /api/v1/conversations/{conversation_id}/mark_read/
```

## Système de notifications

### Liste des notifications
```
GET /api/v1/notifications/
```

**Paramètres de requête:**
- `category`: Catégorie (`GENERAL`, `PROJECT`, `INVESTMENT`, `MESSAGE`, `PAYMENT`)
- `status`: Statut (`UNREAD`, `READ`, `ARCHIVED`)
- `priority`: Priorité (`LOW`, `NORMAL`, `HIGH`, `URGENT`)

**Réponse (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid4",
      "title": "Nouvel investissement reçu",
      "content": "Vous avez reçu un investissement de 25 000€",
      "category": "INVESTMENT",
      "priority": "HIGH",
      "status": "UNREAD",
      "read_at": null,
      "icon": "investment-icon",
      "action_url": "/investments/uuid4",
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### Marquer comme lu
```
POST /api/v1/notifications/{notification_id}/mark_as_read/
```

### Marquer toutes comme lues
```
POST /api/v1/notifications/mark_all_read/
```

### Nombre de notifications non lues
```
GET /api/v1/notifications/unread_count/
```

### Préférences de notifications
```
GET /api/v1/notification-preferences/
PUT /api/v1/notification-preferences/
```

## Système de paiements

### Traitements de paiement
```
GET /api/v1/payments/
POST /api/v1/payments/
GET /api/v1/payments/{payment_id}/
```

### Webhooks de paiement
```
POST /api/v1/payments/webhook/
```

## Codes d'erreur

### Codes de statut HTTP standard
- `200 OK`: Succès
- `201 Created`: Ressource créée
- `204 No Content`: Succès sans contenu
- `400 Bad Request`: Erreur de validation
- `401 Unauthorized`: Non authentifié
- `403 Forbidden`: Non autorisé
- `404 Not Found`: Ressource non trouvée
- `429 Too Many Requests`: Limite de taux dépassée
- `500 Internal Server Error`: Erreur serveur

### Format des erreurs
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Les données fournies ne sont pas valides",
    "details": {
      "email": ["Cette adresse email est déjà utilisée"],
      "password": ["Le mot de passe doit contenir au moins 8 caractères"]
    }
  }
}
```

### Codes d'erreur spécifiques
- `INVALID_TOKEN`: Token JWT invalide
- `TOKEN_EXPIRED`: Token JWT expiré
- `VALIDATION_ERROR`: Erreur de validation des données
- `PERMISSION_DENIED`: Permission refusée
- `RESOURCE_NOT_FOUND`: Ressource non trouvée
- `DUPLICATE_RESOURCE`: Ressource déjà existante
- `RATE_LIMIT_EXCEEDED`: Limite de taux dépassée

## Pagination

### Format de pagination
```json
{
  "count": 150,
  "next": "http://api.venturelink.com/api/v1/projects/?page=3",
  "previous": "http://api.venturelink.com/api/v1/projects/?page=1",
  "results": []
}
```

### Paramètres de pagination
- `page`: Numéro de page (défaut: 1)
- `page_size`: Taille de la page (défaut: 20, max: 100)

## Filtrage et recherche

### Paramètres de recherche
- `search`: Recherche textuelle globale
- `ordering`: Tri (préfixer par `-` pour ordre décroissant)

### Exemples de tri
- `?ordering=created_at`: Par date de création (ascendant)
- `?ordering=-created_at`: Par date de création (descendant)
- `?ordering=title,-created_at`: Par titre puis date (mixte)

## Upload de fichiers

### Format multipart/form-data
```
POST /api/v1/projects/{project_id}/media/
Content-Type: multipart/form-data

file: [fichier binaire]
title: "Titre du média"
description: "Description du média"
media_type: "IMAGE"
```

### Types de médias supportés
- **Images**: JPG, PNG, GIF (max 5MB)
- **Documents**: PDF (max 10MB)
- **Vidéos**: MP4, MOV (max 50MB)

## Versioning

### Stratégie de versioning
- Version courante: `v1`
- URL: `/api/v1/`
- Headers de version: `Accept: application/vnd.venturelink.v1+json`

## Limites de taux

### Limitations par défaut
- **Authentifié**: 1000 requêtes/heure
- **Non authentifié**: 100 requêtes/heure
- **Upload**: 10 uploads/minute

### Headers de limitation
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Internationalisation

### Langues supportées
- `fr`: Français (défaut)
- `en`: Anglais

### Header de langue
```
Accept-Language: fr
```

### Devises supportées
- EUR, USD, GBP, JPY, CAD, AUD, CHF, CNY, HKD

## Webhooks

### Événements disponibles
- `project.created`
- `project.updated` 
- `investment.created`
- `investment.status_changed`
- `payment.completed`
- `payment.failed`

### Format des webhooks
```json
{
  "event": "investment.created",
  "data": {
    "id": "uuid4",
    "investor": "uuid4",
    "project": "uuid4",
    "amount": 25000.00
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

## Environnements

### Développement
- Base URL: `http://localhost:8000`
- Mode sandbox pour les paiements

### Production
- Base URL: `https://api.venturelink.com`
- SSL/TLS requis
- Authentification renforcée 