# Référence des Endpoints - VentureLink API

## Vue d'ensemble

Ce document fournit une référence complète de tous les endpoints disponibles dans l'API VentureLink, organisés par module fonctionnel.

## Base URL
- **Développement**: `http://localhost:8000/api/v1`
- **Production**: `https://api.venturelink.com/api/v1`

## Authentification

### Endpoints d'authentification

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/auth/register/` | Inscription d'un nouvel utilisateur | Non |
| POST | `/auth/token/` | Connexion et obtention des tokens | Non |
| POST | `/auth/token/refresh/` | Rafraîchissement du token d'accès | Non |
| POST | `/auth/token/verify/` | Vérification de la validité d'un token | Non |
| POST | `/auth/logout/` | Déconnexion de l'utilisateur | Oui |
| POST | `/auth/firebase/` | Authentification via Firebase | Non |
| POST | `/auth/google/` | Authentification via Google | Non |
| POST | `/auth/facebook/` | Authentification via Facebook | Non |
| POST | `/auth/password-reset/` | Demande de réinitialisation de mot de passe | Non |
| POST | `/auth/password-reset/confirm/` | Confirmation de réinitialisation | Non |
| GET | `/auth/verify-account/<token>/` | Vérification du compte par email | Non |
| POST | `/auth/request-email-verification/` | Demande de vérification email | Oui |

## Gestion des utilisateurs

### Endpoints utilisateurs

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/users/me/` | Profil de l'utilisateur connecté | Oui |
| PUT | `/users/me/` | Mise à jour complète du profil | Oui |
| PATCH | `/users/me/` | Mise à jour partielle du profil | Oui |
| POST | `/users/change-password/` | Changement de mot de passe | Oui |
| GET | `/users/{user_id}/profile/` | Profil public d'un utilisateur | Optionnel |

### Endpoints profil détaillé

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/users/me/profile/` | Profil détaillé de l'utilisateur | Oui |
| PUT | `/users/me/profile/` | Mise à jour du profil détaillé | Oui |
| PATCH | `/users/me/profile/` | Mise à jour partielle du profil | Oui |

### Endpoints expertises

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/users/me/profile/expertise/` | Liste des expertises | Oui |
| POST | `/users/me/profile/expertise/` | Ajouter une expertise | Oui |
| GET | `/users/me/profile/expertise/{id}/` | Détail d'une expertise | Oui |
| PUT | `/users/me/profile/expertise/{id}/` | Modifier une expertise | Oui |
| DELETE | `/users/me/profile/expertise/{id}/` | Supprimer une expertise | Oui |

### Endpoints éducation

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/users/me/profile/education/` | Liste des formations | Oui |
| POST | `/users/me/profile/education/` | Ajouter une formation | Oui |
| GET | `/users/me/profile/education/{id}/` | Détail d'une formation | Oui |
| PUT | `/users/me/profile/education/{id}/` | Modifier une formation | Oui |
| DELETE | `/users/me/profile/education/{id}/` | Supprimer une formation | Oui |

### Endpoints expérience

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/users/me/profile/experience/` | Liste des expériences | Oui |
| POST | `/users/me/profile/experience/` | Ajouter une expérience | Oui |
| GET | `/users/me/profile/experience/{id}/` | Détail d'une expérience | Oui |
| PUT | `/users/me/profile/experience/{id}/` | Modifier une expérience | Oui |
| DELETE | `/users/me/profile/experience/{id}/` | Supprimer une expérience | Oui |

## Gestion des projets

### Endpoints projets principaux

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/projects/` | Liste des projets avec filtres | Optionnel |
| POST | `/projects/` | Créer un nouveau projet | Oui |
| GET | `/projects/{id}/` | Détail d'un projet | Optionnel |
| PUT | `/projects/{id}/` | Modifier un projet (complet) | Oui |
| PATCH | `/projects/{id}/` | Modifier un projet (partiel) | Oui |
| DELETE | `/projects/{id}/` | Supprimer un projet | Oui |

### Actions sur les projets

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/projects/{id}/toggle_favorite/` | Basculer le statut favori | Oui |
| POST | `/projects/{id}/toggle_interest/` | Exprimer/retirer un intérêt | Oui |
| POST | `/projects/{id}/publish/` | Publier un projet | Oui |
| POST | `/projects/{id}/archive/` | Archiver un projet | Oui |
| POST | `/projects/{id}/duplicate/` | Dupliquer un projet | Oui |

### Endpoints médias de projet

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/projects/{id}/media/` | Liste des médias d'un projet | Optionnel |
| POST | `/projects/{id}/media/` | Ajouter un média | Oui |
| GET | `/projects/{id}/media/{media_id}/` | Détail d'un média | Optionnel |
| PUT | `/projects/{id}/media/{media_id}/` | Modifier un média | Oui |
| DELETE | `/projects/{id}/media/{media_id}/` | Supprimer un média | Oui |

### Endpoints besoins de projet

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/projects/{id}/needs/` | Liste des besoins | Optionnel |
| POST | `/projects/{id}/needs/` | Ajouter un besoin | Oui |
| GET | `/projects/{id}/needs/{need_id}/` | Détail d'un besoin | Optionnel |
| PUT | `/projects/{id}/needs/{need_id}/` | Modifier un besoin | Oui |
| DELETE | `/projects/{id}/needs/{need_id}/` | Supprimer un besoin | Oui |

### Endpoints compétences recherchées

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/projects/{id}/skills/` | Liste des compétences recherchées | Optionnel |
| POST | `/projects/{id}/skills/` | Ajouter une compétence | Oui |
| GET | `/projects/{id}/skills/{skill_id}/` | Détail d'une compétence | Optionnel |
| PUT | `/projects/{id}/skills/{skill_id}/` | Modifier une compétence | Oui |
| DELETE | `/projects/{id}/skills/{skill_id}/` | Supprimer une compétence | Oui |

### Endpoints catégories et tags

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/categories/` | Liste des catégories | Non |
| GET | `/categories/{id}/` | Détail d'une catégorie | Non |
| GET | `/tags/` | Liste des tags | Non |
| GET | `/tags/{id}/` | Détail d'un tag | Non |

### Endpoints intérêts et favoris

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/interests/` | Liste des intérêts de l'utilisateur | Oui |
| GET | `/favorites/` | Liste des favoris de l'utilisateur | Oui |

## Gestion des investissements

### Endpoints investissements principaux

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/investments/` | Liste des investissements | Oui |
| POST | `/investments/` | Créer un investissement | Oui |
| GET | `/investments/{id}/` | Détail d'un investissement | Oui |
| PUT | `/investments/{id}/` | Modifier un investissement | Oui |
| PATCH | `/investments/{id}/` | Modification partielle | Oui |
| DELETE | `/investments/{id}/` | Supprimer un investissement | Oui |

### Actions sur les investissements

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/investments/{id}/approve/` | Approuver un investissement | Oui |
| POST | `/investments/{id}/reject/` | Rejeter un investissement | Oui |
| POST | `/investments/{id}/cancel/` | Annuler un investissement | Oui |
| POST | `/investments/{id}/complete/` | Finaliser un investissement | Oui |

### Endpoints historique et paiements

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/investments/{id}/history/` | Historique des changements | Oui |
| GET | `/investments/{id}/payments/` | Liste des paiements | Oui |
| POST | `/investments/{id}/payments/` | Ajouter un paiement | Oui |
| GET | `/investments/{id}/payments/{payment_id}/` | Détail d'un paiement | Oui |

## Système de messagerie

### Endpoints conversations

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/conversations/` | Liste des conversations | Oui |
| POST | `/conversations/` | Créer une conversation | Oui |
| GET | `/conversations/{id}/` | Détail d'une conversation | Oui |
| PUT | `/conversations/{id}/` | Modifier une conversation | Oui |
| DELETE | `/conversations/{id}/` | Supprimer une conversation | Oui |

### Actions sur les conversations

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/conversations/{id}/mark_read/` | Marquer comme lue | Oui |
| POST | `/conversations/{id}/archive/` | Archiver la conversation | Oui |
| POST | `/conversations/{id}/mute/` | Mettre en sourdine | Oui |
| POST | `/conversations/{id}/unmute/` | Retirer la sourdine | Oui |

### Endpoints messages

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/conversations/{id}/messages/` | Messages d'une conversation | Oui |
| POST | `/conversations/{id}/messages/` | Envoyer un message | Oui |
| GET | `/messages/{id}/` | Détail d'un message | Oui |
| PUT | `/messages/{id}/` | Modifier un message | Oui |
| DELETE | `/messages/{id}/` | Supprimer un message | Oui |

### Actions sur les messages

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/messages/{id}/react/` | Ajouter une réaction | Oui |
| DELETE | `/messages/{id}/react/` | Retirer une réaction | Oui |
| POST | `/messages/{id}/mark_read/` | Marquer comme lu | Oui |

## Système de notifications

### Endpoints notifications

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/notifications/` | Liste des notifications | Oui |
| GET | `/notifications/{id}/` | Détail d'une notification | Oui |
| DELETE | `/notifications/{id}/` | Supprimer une notification | Oui |

### Actions sur les notifications

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/notifications/{id}/mark_as_read/` | Marquer comme lue | Oui |
| POST | `/notifications/{id}/archive/` | Archiver la notification | Oui |
| POST | `/notifications/mark_all_read/` | Marquer toutes comme lues | Oui |
| GET | `/notifications/unread_count/` | Nombre de non lues | Oui |

### Endpoints préférences

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/notification-preferences/` | Préférences de notifications | Oui |
| PUT | `/notification-preferences/` | Modifier les préférences | Oui |
| PATCH | `/notification-preferences/` | Modification partielle | Oui |

## Système de paiements

### Endpoints paiements

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| GET | `/payments/` | Liste des paiements | Oui |
| POST | `/payments/` | Initier un paiement | Oui |
| GET | `/payments/{id}/` | Détail d'un paiement | Oui |
| POST | `/payments/{id}/cancel/` | Annuler un paiement | Oui |
| POST | `/payments/{id}/refund/` | Rembourser un paiement | Oui |

### Webhooks et callbacks

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| POST | `/payments/webhook/` | Webhook des processeurs | Non (signature) |
| GET | `/payments/{id}/status/` | Statut d'un paiement | Oui |

## Paramètres de requête communs

### Pagination
- `page`: Numéro de page (défaut: 1)
- `page_size`: Taille de la page (défaut: 20, max: 100)

### Tri
- `ordering`: Champ de tri (préfixer par `-` pour décroissant)
  - Exemples: `created_at`, `-created_at`, `title`, `-updated_at`

### Recherche
- `search`: Recherche textuelle globale

### Filtres projets
- `category`: ID de catégorie
- `stage`: Stade (`IDEA`, `PROTOTYPE`, `DEVELOPMENT`, `GROWTH`)
- `status`: Statut (`ACTIVE`, `INACTIVE`, `FUNDED`, `ARCHIVED`)
- `funding_min`: Montant minimum
- `funding_max`: Montant maximum
- `location_country`: Pays
- `tags`: IDs des tags (séparés par virgules)
- `is_featured`: Projets mis en avant (true/false)
- `is_premium`: Projets premium (true/false)

### Filtres investissements
- `investor`: ID de l'investisseur
- `project`: ID du projet
- `status`: Statut (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`, `COMPLETED`)
- `investment_type`: Type (`EQUITY`, `LOAN`, `DONATION`, `CONVERTIBLE_NOTE`)
- `amount_min`: Montant minimum
- `amount_max`: Montant maximum

### Filtres notifications
- `category`: Catégorie (`GENERAL`, `PROJECT`, `INVESTMENT`, `MESSAGE`, `PAYMENT`)
- `status`: Statut (`UNREAD`, `READ`, `ARCHIVED`)
- `priority`: Priorité (`LOW`, `NORMAL`, `HIGH`, `URGENT`)

### Filtres conversations
- `conversation_type`: Type (`DIRECT`, `PROJECT`, `GROUP`)
- `status`: Statut (`ACTIVE`, `ARCHIVED`, `DELETED`)
- `project`: ID du projet associé

## Codes de réponse HTTP

### Succès
- `200 OK`: Requête réussie
- `201 Created`: Ressource créée
- `204 No Content`: Succès sans contenu (suppression)

### Erreurs client
- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Non authentifié
- `403 Forbidden`: Non autorisé
- `404 Not Found`: Ressource non trouvée
- `409 Conflict`: Conflit (ressource déjà existante)
- `422 Unprocessable Entity`: Erreur de validation
- `429 Too Many Requests`: Limite de taux dépassée

### Erreurs serveur
- `500 Internal Server Error`: Erreur serveur
- `502 Bad Gateway`: Erreur de passerelle
- `503 Service Unavailable`: Service indisponible

## Headers de réponse

### Pagination
```
X-Total-Count: 150
X-Page-Count: 8
X-Current-Page: 1
X-Per-Page: 20
```

### Limitation de taux
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Cache
```
Cache-Control: public, max-age=300
ETag: "abc123"
Last-Modified: Wed, 21 Oct 2015 07:28:00 GMT
```

## Formats de données

### Dates
- Format ISO 8601: `2024-01-15T14:30:00Z`
- Timezone UTC par défaut

### Montants
- Format décimal avec 2 décimales: `25000.00`
- Devise en code ISO 3 lettres: `EUR`, `USD`

### Identifiants
- Format UUID4: `550e8400-e29b-41d4-a716-446655440000`

### Fichiers
- URLs complètes: `https://api.venturelink.com/media/projects/image.jpg`
- Types MIME supportés: `image/jpeg`, `image/png`, `application/pdf`

Cette référence couvre tous les endpoints principaux de l'API VentureLink avec leurs paramètres et comportements attendus. 