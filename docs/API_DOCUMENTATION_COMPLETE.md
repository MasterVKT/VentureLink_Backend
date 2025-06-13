# Documentation API VentureLink

## Introduction

Cette documentation décrit en détail l'API REST de VentureLink, plateforme connectant entrepreneurs et investisseurs. Elle est conçue pour permettre l'implémentation automatisée des fonctionnalités dans le frontend.

## Informations générales

- **URL de base Production**: `https://api.venturelink.com/api/v1`
- **URL de base Développement**: `http://localhost:8000/api/v1`
- **Format de données**: JSON
- **Encodage de caractères**: UTF-8
- **Authentification**: JWT (JSON Web Tokens)

## Authentification

### Mécanisme d'authentification

VentureLink utilise JWT avec un système de token d'accès (1 heure) et de token de rafraîchissement (14 jours). Tous les endpoints protégés nécessitent le header d'authentification suivant:

```
Authorization: Bearer <access_token>
```

### Endpoints d'authentification

#### Inscription
- **URL**: `POST /auth/register/`
- **Description**: Création d'un nouveau compte utilisateur
- **Corps de requête**:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "BOTH",
  "password": "SecurePassword123",
  "password_confirmation": "SecurePassword123",
  "terms_accepted": true
}
```
- **Réponse** (201 Created):
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
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

#### Connexion
- **URL**: `POST /auth/token/`
- **Description**: Authentification et obtention des tokens
- **Corps de requête**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```
- **Réponse** (200 OK):
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "BOTH"
  }
}
```

#### Rafraîchissement du token
- **URL**: `POST /auth/token/refresh/`
- **Description**: Obtention d'un nouveau token d'accès
- **Corps de requête**:
```json
{
  "refresh": "jwt_refresh_token"
}
```
- **Réponse** (200 OK):
```json
{
  "access": "new_jwt_access_token",
  "refresh": "new_jwt_refresh_token"
}
```

#### Rafraîchissement du token personnalisé
- **URL**: `POST /auth/token/custom-refresh/`
- **Description**: Rafraîchissement personnalisé avec services additionnels
- **Corps de requête**:
```json
{
  "refresh": "jwt_refresh_token"
}
```
- **Réponse** (200 OK):
```json
{
  "access": "new_jwt_access_token",
  "refresh": "new_jwt_refresh_token",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "BOTH"
  }
}
```

#### Vérification du token
- **URL**: `POST /auth/token/verify/`
- **Description**: Vérification de la validité d'un token
- **Corps de requête**:
```json
{
  "token": "jwt_access_token"
}
```
- **Réponse** (200 OK) si valide, sinon 401 Unauthorized

#### Déconnexion
- **URL**: `POST /auth/logout/`
- **Description**: Déconnexion de l'utilisateur
- **Authentification**: Requise
- **Réponse** (204 No Content)

#### Authentification Firebase
- **URL**: `POST /auth/firebase/`
- **Description**: Authentification via Firebase
- **Corps de requête**:
```json
{
  "id_token": "firebase_id_token"
}
```
- **Réponse** (200 OK):
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "is_new_user": false
}
```

#### Authentification Google
- **URL**: `POST /auth/google/`
- **Description**: Authentification via Google
- **Corps de requête**:
```json
{
  "access_token": "google_access_token"
}
```
- **Réponse** (200 OK): Similaire à Firebase

#### Authentification Facebook
- **URL**: `POST /auth/facebook/`
- **Description**: Authentification via Facebook
- **Corps de requête**:
```json
{
  "access_token": "facebook_access_token"
}
```
- **Réponse** (200 OK): Similaire à Firebase

#### Réinitialisation du mot de passe
- **URL**: `POST /auth/password-reset/`
- **Description**: Demande de réinitialisation du mot de passe
- **Corps de requête**:
```json
{
  "email": "user@example.com"
}
```
- **Réponse** (200 OK):
```json
{
  "message": "Un email de réinitialisation a été envoyé."
}
```

#### Confirmation de réinitialisation du mot de passe
- **URL**: `POST /auth/password-reset/confirm/`
- **Description**: Confirmation de la réinitialisation avec le nouveau mot de passe
- **Corps de requête**:
```json
{
  "token": "reset_token",
  "password": "NewSecurePassword123",
  "password_confirmation": "NewSecurePassword123"
}
```
- **Réponse** (200 OK):
```json
{
  "message": "Mot de passe réinitialisé avec succès."
}
```

#### Vérification du compte
- **URL**: `GET /auth/verify-account/<str:token>/`
- **Description**: Vérification du compte utilisateur via un token envoyé par email
- **Réponse** (200 OK):
```json
{
  "message": "Compte vérifié avec succès."
}
```

#### Demande de vérification d'email
- **URL**: `POST /auth/request-email-verification/`
- **Description**: Demande d'envoi d'un email de vérification
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "message": "Email de vérification envoyé."
}
```

## Gestion des utilisateurs

### Profil utilisateur

#### Récupérer le profil actuel
- **URL**: `GET /users/me/`
- **Description**: Obtention des informations du profil de l'utilisateur connecté
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
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
  "date_joined": "2024-01-01T12:00:00Z",
  "profile": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "profile_picture": "http://example.com/media/profile.jpg",
    "bio_short": "Entrepreneur passionné",
    "title": "CEO & Founder",
    "website": "https://johndoe.com",
    "social_linkedin": "https://linkedin.com/in/johndoe",
    "social_twitter": "https://twitter.com/johndoe",
    "social_facebook": "https://facebook.com/johndoe",
    "views_count": 150,
    "avg_rating": 4.5,
    "rating_count": 10
  }
}
```

#### Mettre à jour le profil
- **URL**: `PATCH /users/me/`
- **Description**: Mise à jour partielle du profil utilisateur
- **Authentification**: Requise
- **Corps de requête** (exemple):
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "phone_number": "+33987654321",
  "preferred_currency": "USD"
}
```
- **Réponse** (200 OK): Profil mis à jour

#### Liste des utilisateurs (admin)
- **URL**: `GET /users/`
- **Description**: Récupérer la liste des utilisateurs
- **Authentification**: Requise (Admin)
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `search`: Recherche par nom ou email
- **Réponse** (200 OK): Liste paginée des utilisateurs

#### Détail d'un utilisateur (admin)
- **URL**: `GET /users/{id}/`
- **Description**: Détails d'un utilisateur spécifique
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Détails de l'utilisateur

### Gestion des profils

#### Liste des profils publics
- **URL**: `GET /profiles/`
- **Description**: Liste des profils publics d'utilisateurs
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `search`: Recherche par nom
  - `user_type`: Type d'utilisateur (`ENTREPRENEUR`, `INVESTOR`, `BOTH`)
  - `order_by`: Champ de tri
- **Réponse** (200 OK): Liste paginée des profils

#### Détail d'un profil
- **URL**: `GET /profiles/{id}/`
- **Description**: Détails d'un profil spécifique
- **Réponse** (200 OK): Détails du profil

### Gestion des abonnements

#### Liste des plans d'abonnement
- **URL**: `GET /payments/plans/`
- **Description**: Liste des plans d'abonnement disponibles
- **Réponse** (200 OK):
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Premium Mensuel",
      "description": "Accès premium pendant un mois",
      "price": 9.99,
      "currency": "EUR",
      "interval": "MONTH",
      "interval_count": 1,
      "is_active": true,
      "features": ["Projet en vedette", "Accès aux investisseurs premium"]
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Premium Annuel",
      "description": "Accès premium pendant un an",
      "price": 99.99,
      "currency": "EUR",
      "interval": "YEAR",
      "interval_count": 1,
      "is_active": true,
      "features": ["Projet en vedette", "Accès aux investisseurs premium", "Réduction de 17%"]
    }
  ]
}
```

#### Abonnement actuel de l'utilisateur
- **URL**: `GET /payments/subscription/`
- **Description**: Détails de l'abonnement actuel de l'utilisateur
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "plan": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Premium Mensuel",
    "price": 9.99,
    "currency": "EUR"
  },
  "status": "ACTIVE",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-02-01T00:00:00Z",
  "is_auto_renew": true,
  "payment_method": "CARD"
}
```

#### Créer un abonnement
- **URL**: `POST /payments/subscription/create/`
- **Description**: Création d'un nouvel abonnement
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "plan_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
- **Réponse** (201 Created):
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "checkout_url": "https://mycoolpay.com/checkout/abc123"
}
```

#### Annuler un abonnement
- **URL**: `POST /payments/subscription/cancel/`
- **Description**: Annulation de l'abonnement actuel
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "message": "Abonnement annulé avec succès",
  "end_date": "2024-02-01T00:00:00Z"
}
```

### Tokens d'appareil

#### Enregistrer un token d'appareil
- **URL**: `POST /device-tokens/`
- **Description**: Enregistrement d'un token pour les notifications push
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "token": "device_token_from_fcm",
  "platform": "ANDROID" // ou "IOS", "WEB"
}
```
- **Réponse** (201 Created): Token enregistré

#### Supprimer un token d'appareil
- **URL**: `DELETE /device-tokens/{id}/`
- **Description**: Suppression d'un token d'appareil
- **Authentification**: Requise
- **Réponse** (204 No Content)

## Devises

#### Liste des devises
- **URL**: `GET /currencies/`
- **Description**: Liste des devises supportées par la plateforme
- **Réponse** (200 OK):
```json
{
  "count": 3,
  "results": [
    {
      "code": "EUR",
      "name": "Euro",
      "symbol": "€",
      "rate_to_base": 1.0
    },
    {
      "code": "USD",
      "name": "US Dollar",
      "symbol": "$",
      "rate_to_base": 1.09
    },
    {
      "code": "GBP",
      "name": "British Pound",
      "symbol": "£",
      "rate_to_base": 0.86
    }
  ]
}
```

## Gestion des projets

### Projets

#### Liste des projets
- **URL**: `GET /projects/`
- **Description**: Récupération de la liste des projets avec filtrage et pagination
- **Authentification**: Optionnelle
- **Paramètres de requête**:
  - `page`: Numéro de page (défaut: 1)
  - `page_size`: Taille de la page (défaut: 20, max: 100)
  - `search`: Recherche textuelle
  - `category`: ID de catégorie
  - `stage`: Stade (`IDEA`, `PROTOTYPE`, `DEVELOPMENT`, `GROWTH`)
  - `status`: Statut (`ACTIVE`, `INACTIVE`, `FUNDED`, `ARCHIVED`)
  - `funding_min`: Montant minimum de financement
  - `funding_max`: Montant maximum de financement
  - `location_country`: Pays
  - `tags`: IDs des tags (séparés par virgules)
  - `ordering`: Champ de tri (préfixer par `-` pour décroissant)
- **Réponse** (200 OK):
```json
{
  "count": 150,
  "next": "http://api.venturelink.com/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Application IA révolutionnaire",
      "short_description": "Une application qui révolutionne l'IA",
      "category": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
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
      "published_at": "2024-01-02T10:00:00Z",
      "creator": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "full_name": "John Doe",
        "profile_picture": "http://example.com/media/profile.jpg"
      },
      "is_favorite": false,
      "has_expressed_interest": false,
      "featured_media": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_url": "http://example.com/media/project.jpg",
        "type": "IMAGE"
      }
    }
  ]
}
```

#### Créer un projet
- **URL**: `POST /projects/`
- **Description**: Création d'un nouveau projet
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "title": "Application IA révolutionnaire",
  "short_description": "Une application qui révolutionne l'IA",
  "full_description": "Description complète du projet...",
  "category": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "PROTOTYPE",
  "funding_min": 50000.00,
  "funding_max": 200000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Paris",
  "is_draft": true,
  "tags": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
}
```
- **Réponse** (201 Created): Projet créé avec ses détails

#### Détail d'un projet
- **URL**: `GET /projects/{id}/`
- **Description**: Récupération des détails complets d'un projet
- **Authentification**: Optionnelle
- **Réponse** (200 OK): Détails complets du projet

#### Mettre à jour un projet
- **URL**: `PUT /projects/{id}/`
- **Description**: Mise à jour d'un projet existant
- **Authentification**: Requise (propriétaire du projet)
- **Corps de requête**: Similaire à la création
- **Réponse** (200 OK): Projet mis à jour

#### Supprimer un projet
- **URL**: `DELETE /projects/{id}/`
- **Description**: Suppression d'un projet
- **Authentification**: Requise (propriétaire du projet)
- **Réponse** (204 No Content)

#### Recherche avancée de projets
- **URL**: `GET /search/`
- **Description**: Recherche avancée avec filtres multiples
- **Paramètres de requête**: Similaires à la liste des projets avec options additionnelles
- **Réponse** (200 OK): Liste paginée des projets correspondants

#### Projets tendance
- **URL**: `GET /trending/`
- **Description**: Liste des projets les plus populaires
- **Paramètres de requête**:
  - `limit`: Nombre de projets à retourner (défaut: 10)
  - `period`: Période (`DAY`, `WEEK`, `MONTH`)
- **Réponse** (200 OK): Liste des projets tendance

### Catégories de projets

#### Liste des catégories
- **URL**: `GET /categories/`
- **Description**: Liste des catégories de projets
- **Réponse** (200 OK):
```json
{
  "count": 10,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name_fr": "Intelligence Artificielle",
      "name_en": "Artificial Intelligence",
      "icon": "ai-icon",
      "projects_count": 45
    }
  ]
}
```

### Tags de projets

#### Liste des tags
- **URL**: `GET /tags/`
- **Description**: Liste des tags pour les projets
- **Réponse** (200 OK): Liste paginée des tags

### Médias de projets

#### Liste des médias d'un projet
- **URL**: `GET /projects/{project_id}/media/`
- **Description**: Liste des médias associés à un projet
- **Authentification**: Optionnelle
- **Réponse** (200 OK):
```json
{
  "count": 3,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_url": "http://example.com/media/project1.jpg",
      "thumbnail_url": "http://example.com/media/project1_thumb.jpg",
      "type": "IMAGE",
      "order": 1,
      "title": "Aperçu du produit"
    }
  ]
}
```

#### Ajouter un média à un projet
- **URL**: `POST /projects/{project_id}/media/`
- **Description**: Ajout d'un nouveau média
- **Authentification**: Requise (propriétaire du projet)
- **Corps de requête** (multipart/form-data):
  - `file`: Fichier média
  - `type`: Type de média (`IMAGE`, `VIDEO`, `DOCUMENT`)
  - `title`: Titre (optionnel)
  - `order`: Position d'affichage
- **Réponse** (201 Created): Média créé

#### Supprimer un média
- **URL**: `DELETE /projects/{project_id}/media/{id}/`
- **Description**: Suppression d'un média
- **Authentification**: Requise (propriétaire du projet)
- **Réponse** (204 No Content)

### Besoins de projets

#### Liste des besoins d'un projet
- **URL**: `GET /projects/{project_id}/needs/`
- **Description**: Liste des besoins associés à un projet
- **Authentification**: Optionnelle
- **Réponse** (200 OK): Liste des besoins

#### Ajouter un besoin à un projet
- **URL**: `POST /projects/{project_id}/needs/`
- **Description**: Ajout d'un nouveau besoin
- **Authentification**: Requise (propriétaire du projet)
- **Corps de requête**:
```json
{
  "title": "Investissement en fonds propres",
  "description": "Recherche d'investisseurs pour une prise de participation",
  "type": "FUNDING",
  "amount": 50000.00,
  "currency": "EUR"
}
```
- **Réponse** (201 Created): Besoin créé

### Compétences requises

#### Liste des compétences requises
- **URL**: `GET /projects/{project_id}/skills/`
- **Description**: Liste des compétences requises pour un projet
- **Authentification**: Optionnelle
- **Réponse** (200 OK): Liste des compétences

#### Ajouter une compétence requise
- **URL**: `POST /projects/{project_id}/skills/`
- **Description**: Ajout d'une nouvelle compétence requise
- **Authentification**: Requise (propriétaire du projet)
- **Corps de requête**:
```json
{
  "name": "Développement Python",
  "level": "EXPERT",
  "description": "Développeur Python avec expérience en AI"
}
```
- **Réponse** (201 Created): Compétence créée

### Intérêts pour un projet

#### Liste des intérêts
- **URL**: `GET /interests/`
- **Description**: Liste des marques d'intérêt (pour un admin)
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Liste paginée des intérêts

#### Exprimer un intérêt
- **URL**: `POST /interests/`
- **Description**: Exprimer un intérêt pour un projet
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Je suis intéressé par votre projet et souhaite en discuter",
  "interest_type": "INVESTMENT"
}
```
- **Réponse** (201 Created): Intérêt créé

#### Intérêts pour un projet spécifique
- **URL**: `GET /projects/{project_id}/interests/`
- **Description**: Liste des intérêts exprimés pour un projet
- **Authentification**: Requise (propriétaire du projet)
- **Réponse** (200 OK): Liste des intérêts

### Favoris

#### Liste des favoris
- **URL**: `GET /favorites/`
- **Description**: Liste des projets favoris de l'utilisateur connecté
- **Authentification**: Requise
- **Réponse** (200 OK): Liste paginée des projets favoris

#### Ajouter un favori
- **URL**: `POST /favorites/`
- **Description**: Ajouter un projet aux favoris
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000"
}
```
- **Réponse** (201 Created): Favori créé

#### Supprimer un favori
- **URL**: `DELETE /favorites/{id}/`
- **Description**: Supprimer un projet des favoris
- **Authentification**: Requise
- **Réponse** (204 No Content)

### Questions et réponses

#### Liste des questions
- **URL**: `GET /questions/`
- **Description**: Liste des questions (pour un admin)
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Liste paginée des questions

#### Poser une question sur un projet
- **URL**: `POST /projects/{project_id}/questions/`
- **Description**: Poser une question sur un projet
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "content": "Comment comptez-vous monétiser ce service?"
}
```
- **Réponse** (201 Created): Question créée

#### Liste des questions d'un projet
- **URL**: `GET /projects/{project_id}/questions/`
- **Description**: Liste des questions posées sur un projet
- **Authentification**: Optionnelle
- **Réponse** (200 OK): Liste des questions

#### Répondre à une question
- **URL**: `POST /questions/{question_id}/answers/`
- **Description**: Répondre à une question
- **Authentification**: Requise (propriétaire du projet)
- **Corps de requête**:
```json
{
  "content": "Nous prévoyons un modèle freemium avec des fonctionnalités premium."
}
```
- **Réponse** (201 Created): Réponse créée

## Messagerie

### Conversations

#### Liste des conversations
- **URL**: `GET /conversations/`
- **Description**: Liste des conversations de l'utilisateur
- **Authentification**: Requise
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `unread_only`: Filtre les conversations non lues (true/false)
- **Réponse** (200 OK):
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Discussion projet IA",
      "participants": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "full_name": "John Doe",
          "profile_picture": "http://example.com/media/profile.jpg"
        },
        {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "full_name": "Jane Smith",
          "profile_picture": "http://example.com/media/profile2.jpg"
        }
      ],
      "last_message": {
        "content": "Bonjour, je suis intéressé par votre projet",
        "created_at": "2024-01-10T14:30:00Z",
        "sender_name": "Jane Smith"
      },
      "unread_count": 2,
      "created_at": "2024-01-10T14:00:00Z",
      "updated_at": "2024-01-10T14:30:00Z"
    }
  ]
}
```

#### Créer une conversation
- **URL**: `POST /conversations/`
- **Description**: Création d'une nouvelle conversation
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "title": "Discussion projet IA",
  "participants": ["550e8400-e29b-41d4-a716-446655440001"],
  "first_message": "Bonjour, je suis intéressé par votre projet"
}
```
- **Réponse** (201 Created): Conversation créée

#### Détail d'une conversation
- **URL**: `GET /conversations/{id}/`
- **Description**: Détails d'une conversation spécifique
- **Authentification**: Requise (participant)
- **Réponse** (200 OK): Détails de la conversation

#### Marquer comme lue
- **URL**: `PUT /conversations/{id}/read/`
- **Description**: Marquer tous les messages d'une conversation comme lus
- **Authentification**: Requise (participant)
- **Réponse** (200 OK):
```json
{
  "success": true,
  "unread_count": 0
}
```

### Messages

#### Liste des messages d'une conversation
- **URL**: `GET /conversations/{conversation_id}/messages/`
- **Description**: Liste des messages d'une conversation
- **Authentification**: Requise (participant)
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `before`: Timestamp pour pagination (messages avant cette date)
  - `after`: Timestamp pour pagination (messages après cette date)
- **Réponse** (200 OK):
```json
{
  "count": 10,
  "next": "http://api.venturelink.com/api/v1/conversations/id/messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "Bonjour, je suis intéressé par votre projet",
      "sender": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "full_name": "Jane Smith",
        "profile_picture": "http://example.com/media/profile2.jpg"
      },
      "created_at": "2024-01-10T14:30:00Z",
      "attachments_count": 0,
      "is_read": true
    }
  ]
}
```

#### Envoyer un message
- **URL**: `POST /conversations/{conversation_id}/messages/`
- **Description**: Envoi d'un nouveau message dans une conversation
- **Authentification**: Requise (participant)
- **Corps de requête**:
```json
{
  "content": "Merci pour votre intérêt, discutons-en plus en détail"
}
```
- **Réponse** (201 Created): Message créé

#### Supprimer un message
- **URL**: `DELETE /conversations/{conversation_id}/messages/{id}/`
- **Description**: Suppression d'un message (soft delete)
- **Authentification**: Requise (expéditeur du message)
- **Réponse** (204 No Content)

### Pièces jointes

#### Liste des pièces jointes d'un message
- **URL**: `GET /conversations/{conversation_id}/messages/{message_id}/attachments/`
- **Description**: Liste des pièces jointes d'un message
- **Authentification**: Requise (participant)
- **Réponse** (200 OK): Liste des pièces jointes

#### Ajouter une pièce jointe
- **URL**: `POST /conversations/{conversation_id}/messages/{message_id}/attachments/`
- **Description**: Ajout d'une pièce jointe à un message
- **Authentification**: Requise (expéditeur du message)
- **Corps de requête** (multipart/form-data):
  - `file`: Fichier à joindre
  - `type`: Type de fichier (`IMAGE`, `DOCUMENT`, `OTHER`)
- **Réponse** (201 Created): Pièce jointe créée

#### Supprimer une pièce jointe
- **URL**: `DELETE /conversations/{conversation_id}/messages/{message_id}/attachments/{id}/`
- **Description**: Suppression d'une pièce jointe
- **Authentification**: Requise (expéditeur du message)
- **Réponse** (204 No Content)

## Investissements

### Investissements

#### Liste des investissements
- **URL**: `GET /investments/`
- **Description**: Liste des investissements de l'utilisateur
- **Authentification**: Requise
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `status`: Statut (`PENDING`, `ACTIVE`, `COMPLETED`, `CANCELLED`)
  - `project`: ID du projet
- **Réponse** (200 OK):
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "project": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Application IA révolutionnaire",
        "featured_media": {
          "file_url": "http://example.com/media/project.jpg"
        }
      },
      "amount": 5000.00,
      "currency": "EUR",
      "equity_percentage": 2.5,
      "status": "ACTIVE",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "investment_date": "2024-01-15T10:00:00Z",
      "contract_file": "http://example.com/media/contract.pdf"
    }
  ]
}
```

#### Créer un investissement
- **URL**: `POST /investments/`
- **Description**: Création d'un nouvel investissement
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 5000.00,
  "currency": "EUR",
  "equity_percentage": 2.5,
  "notes": "Investissement initial"
}
```
- **Réponse** (201 Created): Investissement créé

#### Détail d'un investissement
- **URL**: `GET /investments/{id}/`
- **Description**: Détails d'un investissement spécifique
- **Authentification**: Requise (participant à l'investissement)
- **Réponse** (200 OK): Détails de l'investissement

#### Mettre à jour un investissement
- **URL**: `PATCH /investments/{id}/`
- **Description**: Mise à jour partielle d'un investissement
- **Authentification**: Requise (participant à l'investissement)
- **Corps de requête**: Champs à mettre à jour
- **Réponse** (200 OK): Investissement mis à jour

### Paiements d'investissement

#### Liste des paiements d'un investissement
- **URL**: `GET /investments/{investment_id}/payments/`
- **Description**: Liste des paiements liés à un investissement
- **Authentification**: Requise (participant à l'investissement)
- **Réponse** (200 OK):
```json
{
  "count": 1,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "amount": 5000.00,
      "currency": "EUR",
      "status": "COMPLETED",
      "payment_date": "2024-01-15T10:30:00Z",
      "payment_method": "BANK_TRANSFER",
      "transaction_reference": "INV-12345"
    }
  ]
}
```

#### Créer un paiement
- **URL**: `POST /investments/{investment_id}/payments/`
- **Description**: Enregistrement d'un nouveau paiement
- **Authentification**: Requise (investisseur ou admin)
- **Corps de requête**:
```json
{
  "amount": 5000.00,
  "currency": "EUR",
  "payment_method": "BANK_TRANSFER",
  "transaction_reference": "INV-12345"
}
```
- **Réponse** (201 Created): Paiement créé

### Remboursements

#### Liste des remboursements
- **URL**: `GET /repayments/`
- **Description**: Liste des remboursements (admin)
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Liste paginée des remboursements

#### Liste des remboursements d'un investissement
- **URL**: `GET /investments/{investment_id}/repayments/`
- **Description**: Liste des remboursements liés à un investissement
- **Authentification**: Requise (participant à l'investissement)
- **Réponse** (200 OK):
```json
{
  "count": 1,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "amount": 500.00,
      "currency": "EUR",
      "status": "COMPLETED",
      "due_date": "2024-02-15T00:00:00Z",
      "payment_date": "2024-02-14T10:30:00Z"
    }
  ]
}
```

#### Créer un remboursement
- **URL**: `POST /investments/{investment_id}/repayments/`
- **Description**: Enregistrement d'un nouveau remboursement
- **Authentification**: Requise (entrepreneur ou admin)
- **Corps de requête**:
```json
{
  "amount": 500.00,
  "currency": "EUR",
  "due_date": "2024-02-15T00:00:00Z"
}
```
- **Réponse** (201 Created): Remboursement créé

### Échéanciers de remboursement

#### Liste des échéanciers
- **URL**: `GET /schedules/`
- **Description**: Liste des échéanciers (admin)
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Liste paginée des échéanciers

#### Échéancier d'un investissement
- **URL**: `GET /investments/{investment_id}/schedules/`
- **Description**: Échéancier de remboursement d'un investissement
- **Authentification**: Requise (participant à l'investissement)
- **Réponse** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "investment": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2025-02-01T00:00:00Z",
  "frequency": "MONTHLY",
  "total_payments": 12,
  "completed_payments": 1,
  "amount_per_payment": 500.00,
  "currency": "EUR",
  "payments": [
    {
      "due_date": "2024-02-15T00:00:00Z",
      "amount": 500.00,
      "status": "COMPLETED"
    },
    {
      "due_date": "2024-03-15T00:00:00Z",
      "amount": 500.00,
      "status": "PENDING"
    }
  ]
}
```

#### Créer un échéancier
- **URL**: `POST /investments/{investment_id}/schedules/`
- **Description**: Création d'un échéancier de remboursement
- **Authentification**: Requise (entrepreneur ou admin)
- **Corps de requête**:
```json
{
  "start_date": "2024-02-01T00:00:00Z",
  "frequency": "MONTHLY",
  "total_payments": 12,
  "amount_per_payment": 500.00,
  "currency": "EUR"
}
```
- **Réponse** (201 Created): Échéancier créé

## Notifications

### Notifications

#### Liste des notifications
- **URL**: `GET /notifications/`
- **Description**: Liste des notifications de l'utilisateur
- **Authentification**: Requise
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `read`: Filtre les notifications lues (true/false)
- **Réponse** (200 OK):
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Nouveau message",
      "message": "Vous avez reçu un nouveau message de John Doe",
      "type": "MESSAGE",
      "read": false,
      "created_at": "2024-01-20T10:00:00Z",
      "data": {
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
        "sender_id": "550e8400-e29b-41d4-a716-446655440001"
      }
    }
  ]
}
```

#### Marquer une notification comme lue
- **URL**: `PUT /notifications/{id}/read/`
- **Description**: Marquer une notification comme lue
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "success": true
}
```

#### Marquer toutes les notifications comme lues
- **URL**: `PUT /notifications/read-all/`
- **Description**: Marquer toutes les notifications comme lues
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "success": true,
  "count": 5
}
```

### Templates de notification

#### Liste des templates (admin)
- **URL**: `GET /notification-templates/`
- **Description**: Liste des templates de notification
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Liste des templates

#### Détail d'un template (admin)
- **URL**: `GET /notification-templates/{id}/`
- **Description**: Détails d'un template spécifique
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK): Détails du template

### Préférences de notification

#### Récupérer les préférences
- **URL**: `GET /notification-preferences/`
- **Description**: Récupération des préférences de notification de l'utilisateur
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "email_notifications": true,
  "push_notifications": true,
  "preferences": [
    {
      "type": "MESSAGE",
      "email": true,
      "push": true,
      "in_app": true
    },
    {
      "type": "PROJECT_INTEREST",
      "email": true,
      "push": false,
      "in_app": true
    }
  ]
}
```

#### Mettre à jour les préférences
- **URL**: `PUT /notification-preferences/`
- **Description**: Mise à jour des préférences de notification
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "email_notifications": true,
  "push_notifications": false,
  "preferences": [
    {
      "type": "MESSAGE",
      "email": true,
      "push": false,
      "in_app": true
    }
  ]
}
```
- **Réponse** (200 OK): Préférences mises à jour

## Analytics

### Métriques utilisateur
- **URL**: `GET /analytics/user/`
- **Description**: Statistiques et métriques concernant l'utilisateur
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "profile_views": 150,
  "project_views_total": 2500,
  "projects_count": 3,
  "interests_received_count": 25,
  "messages_received_count": 45,
  "investments_total": 2,
  "investments_value": 15000.00,
  "activity_history": [
    {
      "date": "2024-01",
      "profile_views": 30,
      "project_views": 500
    },
    {
      "date": "2024-02",
      "profile_views": 45,
      "project_views": 650
    }
  ]
}
```

### Métriques projet
- **URL**: `GET /analytics/project/{project_id}/`
- **Description**: Statistiques et métriques concernant un projet spécifique
- **Authentification**: Requise (propriétaire du projet)
- **Réponse** (200 OK):
```json
{
  "views_total": 1500,
  "views_unique": 850,
  "interests_count": 25,
  "favorites_count": 12,
  "questions_count": 8,
  "conversion_rate": 2.94,
  "demographics": {
    "countries": [
      {"name": "France", "count": 500},
      {"name": "Belgique", "count": 200}
    ],
    "sources": [
      {"name": "direct", "count": 700},
      {"name": "search", "count": 450}
    ]
  },
  "views_history": [
    {"date": "2024-01-01", "views": 50},
    {"date": "2024-01-02", "views": 65}
  ]
}
```

### Métriques tableau de bord
- **URL**: `GET /analytics/dashboard/`
- **Description**: Vue d'ensemble des métriques pour le tableau de bord
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "summary": {
    "projects_count": 3,
    "total_views": 2500,
    "total_interests": 25,
    "total_investments": 15000.00
  },
  "recent_activity": [
    {
      "type": "VIEW",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "project_title": "Application IA révolutionnaire",
      "count": 150,
      "date": "2024-01-20"
    },
    {
      "type": "INTEREST",
      "project_id": "550e8400-e29b-41d4-a716-446655440000",
      "project_title": "Application IA révolutionnaire",
      "count": 5,
      "date": "2024-01-19"
    }
  ],
  "performance_trends": {
    "views": [
      {"date": "2024-01-14", "count": 100},
      {"date": "2024-01-15", "count": 120}
    ],
    "interests": [
      {"date": "2024-01-14", "count": 2},
      {"date": "2024-01-15", "count": 4}
    ]
  }
}
```

### Projets les plus performants
- **URL**: `GET /analytics/top-projects/`
- **Description**: Liste des projets les plus performants sur la plateforme
- **Authentification**: Requise (admin)
- **Paramètres de requête**:
  - `limit`: Nombre de projets à retourner (défaut: 10)
  - `metric`: Métrique de tri (`VIEWS`, `INTERESTS`, `INVESTMENTS`)
  - `period`: Période (`WEEK`, `MONTH`, `YEAR`, `ALL`)
- **Réponse** (200 OK):
```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Application IA révolutionnaire",
      "creator": "John Doe",
      "views_count": 1500,
      "interests_count": 25,
      "investments_count": 2,
      "investments_value": 15000.00,
      "conversion_rate": 1.67
    }
  ]
}
```

## Système de paiements

### Paiements

#### Initier un paiement
- **URL**: `POST /payments/`
- **Description**: Création d'une nouvelle transaction de paiement
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "amount": 100.00,
  "currency": "EUR",
  "payment_type": "SUBSCRIPTION",
  "object_type": "PLAN",
  "object_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "plan_name": "Premium Mensuel",
    "duration_months": 1
  }
}
```
- **Réponse** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 100.00,
  "currency": "EUR",
  "payment_type": "SUBSCRIPTION",
  "status": "PENDING",
  "checkout_url": "https://mycoolpay.com/checkout/abc123",
  "created_at": "2024-01-15T14:30:00Z"
}
```

#### Liste des paiements
- **URL**: `GET /payments/`
- **Description**: Liste des paiements de l'utilisateur
- **Authentification**: Requise
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `status`: Statut (`PENDING`, `COMPLETED`, `FAILED`, `REFUNDED`)
  - `payment_type`: Type de paiement (`SUBSCRIPTION`, `INVESTMENT`, `CREDIT`)
- **Réponse** (200 OK): Liste paginée des paiements

#### Détail d'un paiement
- **URL**: `GET /payments/{id}/`
- **Description**: Détails d'un paiement spécifique
- **Authentification**: Requise
- **Réponse** (200 OK): Détails du paiement

#### Paiement direct
- **URL**: `POST /payments/payin/`
- **Description**: Initiation d'un paiement direct
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "amount": 100.00,
  "currency": "EUR",
  "payment_method": "CARD",
  "return_url": "https://venturelink.com/payment/success",
  "description": "Achat de crédits"
}
```
- **Réponse** (200 OK):
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "checkout_url": "https://mycoolpay.com/checkout/abc123"
}
```

#### Autorisation par OTP
- **URL**: `POST /payments/authorize/`
- **Description**: Autorisation d'un paiement par code OTP
- **Authentification**: Requise
- **Corps de requête**:
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "otp_code": "123456"
}
```
- **Réponse** (200 OK):
```json
{
  "status": "COMPLETED",
  "message": "Paiement autorisé avec succès"
}
```

#### Vérifier le statut d'un paiement
- **URL**: `GET /payments/{payment_id}/status/`
- **Description**: Vérification du statut d'un paiement
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "amount": 100.00,
  "currency": "EUR",
  "payment_method": "CARD",
  "transaction_reference": "PAY-12345",
  "completed_at": "2024-01-15T14:35:00Z"
}
```

#### Historique des paiements
- **URL**: `GET /payments/history/`
- **Description**: Historique complet des paiements de l'utilisateur
- **Authentification**: Requise
- **Paramètres de requête**:
  - `page`: Numéro de page
  - `page_size`: Taille de la page
  - `start_date`: Date de début (format: YYYY-MM-DD)
  - `end_date`: Date de fin (format: YYYY-MM-DD)
- **Réponse** (200 OK): Liste paginée de l'historique des paiements

#### Méthodes de paiement
- **URL**: `GET /payments/methods/`
- **Description**: Liste des méthodes de paiement disponibles
- **Authentification**: Requise
- **Réponse** (200 OK):
```json
{
  "methods": [
    {
      "id": "CARD",
      "name": "Carte bancaire",
      "is_available": true,
      "currencies": ["EUR", "USD", "GBP"],
      "icon_url": "https://assets.venturelink.com/payment/card.png"
    },
    {
      "id": "BANK_TRANSFER",
      "name": "Virement bancaire",
      "is_available": true,
      "currencies": ["EUR"],
      "icon_url": "https://assets.venturelink.com/payment/bank.png"
    }
  ]
}
```

#### Balance du compte
- **URL**: `GET /payments/balance/`
- **Description**: Balance du compte My-CoolPay (admin uniquement)
- **Authentification**: Requise (Admin)
- **Réponse** (200 OK):
```json
{
  "balance": 25000.00,
  "currency": "EUR",
  "pending_balance": 1500.00,
  "last_updated": "2024-01-20T10:00:00Z"
}
```

#### Callback My-CoolPay
- **URL**: `GET /payments/mycoolpay/callback/`
- **Description**: URL de retour après paiement sur My-CoolPay
- **Paramètres de requête**:
  - `transaction_id`: ID de la transaction
  - `status`: Statut du paiement
  - `reference`: Référence interne
- **Réponse**: Redirection vers l'application avec statut

#### Traitement des webhooks
- **URL**: `POST /payments/mycoolpay/webhook/`
- **Description**: Endpoint pour les callbacks de My-CoolPay
- **Authentification**: Non requise (vérification par signature)
- **Headers**:
  - `X-MyCoolPay-Signature`: Signature HMAC SHA-256
- **Corps de requête** (exemple):
```json
{
  "event_type": "payment.success",
  "transaction_ref": "tx_123456789",
  "app_transaction_ref": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_date": "2024-01-15T14:35:00Z",
  "transaction_details": {
    "amount": 100.00,
    "currency": "EUR",
    "payment_method": "card"
  }
}
```
- **Réponse** (200 OK): Confirmation de traitement

## Formats et conventions

### Formats des données
- **Dates**: Format ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **Identifiants**: UUID4
- **Montants**: Décimal avec 2 décimales
- **Devises**: Code ISO à 3 lettres (EUR, USD, etc.)
- **Images**: URLs complètes

### Codes d'erreur HTTP
- **400 Bad Request**: Données invalides
- **401 Unauthorized**: Authentification requise
- **403 Forbidden**: Permissions insuffisantes
- **404 Not Found**: Ressource introuvable
- **409 Conflict**: Conflit (ex: ressource déjà existante)
- **422 Unprocessable Entity**: Validation échouée
- **429 Too Many Requests**: Limite de taux dépassée
- **500 Internal Server Error**: Erreur serveur

### Structure des messages d'erreur
```json
{
  "error": {
    "code": "validation_error",
    "message": "Des erreurs de validation sont présentes.",
    "details": {
      "email": ["Ce champ est obligatoire."],
      "password": ["Le mot de passe doit contenir au moins 8 caractères."]
    }
  }
}
```

## Recommandations d'implémentation

1. **Gestion des tokens**: Stocker le token d'accès en mémoire et le token de rafraîchissement de manière sécurisée.
2. **Rafraîchissement automatique**: Intercepter les erreurs 401 pour tenter un rafraîchissement automatique du token.
3. **Validation côté client**: Implémenter une validation préliminaire côté client avant d'envoyer les requêtes.
4. **Cache**: Mettre en cache les données fréquemment accédées et peu modifiées (catégories, tags).
5. **Gestion hors ligne**: Implémenter un système de file d'attente pour les actions effectuées hors ligne.
6. **Internationalisation**: Supporter les préférences linguistiques de l'utilisateur.
7. **Gestion des devises**: Convertir automatiquement les montants selon la devise préférée de l'utilisateur.

## Webhooks et intégration My-CoolPay

Pour l'intégration des paiements, l'application utilise My-CoolPay comme processeur de paiement. Les étapes clés sont:

1. Créer une transaction via l'API `/payments/`
2. Rediriger l'utilisateur vers l'URL de paiement (`checkout_url`)
3. Attendre la notification par webhook
4. Vérifier la signature du webhook pour sécuriser la transaction
5. Mettre à jour le statut du paiement et des ressources associées

La documentation complète de l'API My-CoolPay et de son intégration est disponible dans le document "My-CoolPay API Docs.pdf".

Cette documentation fournit toutes les informations nécessaires pour une implémentation complète et efficace de l'API VentureLink dans votre application frontend. 