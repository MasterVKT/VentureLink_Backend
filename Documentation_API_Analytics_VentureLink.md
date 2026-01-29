# Documentation API Analytics VentureLink

## Vue d'ensemble

L'application **Analytics** de VentureLink fournit des métriques et statistiques détaillées pour les utilisateurs, projets et l'ensemble de la plateforme. Elle permet de suivre l'engagement, les performances et les tendances au niveau individuel et global.

### Base URL
- **Développement:** `https://api-dev.venturelink.com/api/v1/analytics/`
- **Production:** `https://api.venturelink.com/api/v1/analytics/`

### Authentification
Tous les endpoints nécessitent une authentification JWT via l'en-tête:
```
Authorization: Bearer {token}
```

---

## Modèles de données

### UserMetrics
Métriques cumulatives associées à un utilisateur:
- `projects_created_count`: Nombre de projets créés
- `projects_published_count`: Nombre de projets publiés
- `total_project_views`: Nombre total de vues sur les projets
- `total_project_interests`: Nombre total d'intérêts exprimés
- `total_comments_received`: Nombre total de commentaires reçus
- `investments_made_count`: Nombre d'investissements réalisés
- `total_investment_amount`: Montant total investi
- `messages_sent_count`: Nombre de messages envoyés
- `messages_received_count`: Nombre de messages reçus
- `login_count`: Nombre de connexions
- `last_login`: Dernière connexion

### ProjectMetrics
Métriques cumulatives associées à un projet:
- `view_count`: Nombre de vues
- `interest_count`: Nombre d'intérêts exprimés
- `favorite_count`: Nombre de favoris
- `comment_count`: Nombre de commentaires
- `share_count`: Nombre de partages
- `investment_count`: Nombre d'investissements
- `total_investment_amount`: Montant total investi
- `view_to_interest_rate`: Taux de conversion vues/intérêts (%)
- `interest_to_investment_rate`: Taux de conversion intérêts/investissements (%)

### EventLog
Journal des événements individuels:
- Types d'événements: `PROJECT_VIEW`, `PROJECT_INTEREST`, `PROJECT_FAVORITE`, `PROJECT_COMMENT`, `PROJECT_SHARE`, `USER_LOGIN`, `USER_REGISTRATION`, `INVESTMENT_MADE`, `MESSAGE_SENT`, `SUBSCRIPTION_STARTED`, `SUBSCRIPTION_RENEWED`, `SUBSCRIPTION_CANCELED`

---

## Endpoints API

### 1. GET /analytics/user/

**Description:** Récupère les métriques de l'utilisateur connecté

**Authentification:** Requise (utilisateur connecté)

**Paramètres de requête:**
- `currency` (optionnel): Code devise pour la conversion (défaut: EUR)
  - Valeurs possibles: EUR, USD, GBP, etc.

**Réponse (200 OK):**
```json
{
  "projects_created_count": 5,
  "projects_published_count": 3,
  "total_project_views": 1250,
  "total_project_interests": 45,
  "total_comments_received": 23,
  "investments_made_count": 8,
  "total_investment_amount": 15000.00,
  "total_investment_currency": "EUR",
  "messages_sent_count": 127,
  "messages_received_count": 134,
  "login_count": 89,
  "last_login": "2024-01-15T14:30:00Z"
}
```

**Codes d'erreur:**
- `401`: Non authentifié
- `500`: Erreur serveur

---

### 2. GET /analytics/project/{project_id}/

**Description:** Récupère les métriques détaillées d'un projet spécifique

**Authentification:** Requise (propriétaire du projet ou administrateur)

**Paramètres URL:**
- `project_id` (UUID): Identifiant du projet

**Paramètres de requête:**
- `currency` (optionnel): Code devise pour la conversion (défaut: EUR)

**Réponse (200 OK):**
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "project_name": "Mon Super Projet",
  "view_count": 2450,
  "interest_count": 89,
  "favorite_count": 34,
  "comment_count": 12,
  "share_count": 67,
  "investment_count": 15,
  "total_investment_amount": 45000.00,
  "total_investment_currency": "EUR",
  "view_to_interest_rate": 3.63,
  "interest_to_investment_rate": 16.85
}
```

**Codes d'erreur:**
- `401`: Non authentifié
- `403`: Accès refusé (pas propriétaire du projet)
- `404`: Projet non trouvé
- `500`: Erreur serveur

---

### 3. GET /analytics/dashboard/

**Description:** Récupère les métriques globales de la plateforme pour le tableau de bord administrateur

**Authentification:** Requise (administrateur uniquement)

**Paramètres de requête:**
- `period` (optionnel): Période d'analyse (défaut: week)
  - Valeurs possibles: `day`, `week`, `month`, `year`, `custom`
- `start_date` (requis si period=custom): Date de début au format YYYY-MM-DD
- `currency` (optionnel): Code devise pour la conversion (défaut: EUR)

**Réponse (200 OK):**
```json
{
  "period_start": "2024-01-08",
  "period_end": "2024-01-14",
  "days_count": 7,
  "currency": "EUR",
  "new_users": 45,
  "active_users": 312,
  "new_projects": 23,
  "published_projects": 18,
  "total_views": 5678,
  "total_interests": 234,
  "total_investment": 125000.00,
  "new_subscriptions": 12,
  "subscription_revenue": 2400.00,
  "avg_new_users_per_day": 6.43,
  "avg_active_users_per_day": 44.57
}
```

**Codes d'erreur:**
- `400`: Paramètres invalides
- `401`: Non authentifié
- `403`: Accès refusé (pas administrateur)
- `500`: Erreur serveur

---

### 4. GET /analytics/top-projects/

**Description:** Récupère les projets les plus performants selon une métrique donnée

**Authentification:** Requise (administrateur uniquement)

**Paramètres de requête:**
- `metric` (optionnel): Métrique de tri (défaut: view_count)
  - Valeurs possibles: `view_count`, `interest_count`, `favorite_count`, `investment_count`, `total_investment_amount`
- `limit` (optionnel): Nombre de projets à retourner (défaut: 10, max: 50)
- `period_days` (optionnel): Période en jours (défaut: 30, max: 365)
- `currency` (optionnel): Code devise pour la conversion (défaut: EUR)

**Réponse (200 OK):**
```json
{
  "projects": [
    {
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "project_name": "Projet Innovation",
      "creator_name": "Jean Dupont",
      "view_count": 5420,
      "interest_count": 156,
      "favorite_count": 89,
      "investment_count": 34,
      "total_investment_amount": 87500.00,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "project_id": "456e7890-e89b-12d3-a456-426614174001",
      "project_name": "Tech Startup",
      "creator_name": "Marie Martin",
      "view_count": 4890,
      "interest_count": 142,
      "favorite_count": 76,
      "investment_count": 28,
      "total_investment_amount": 65000.00,
      "created_at": "2024-01-05T00:00:00Z"
    }
  ],
  "currency": "EUR",
  "metric": "view_count",
  "period_days": 30
}
```

**Codes d'erreur:**
- `400`: Paramètres invalides
- `401`: Non authentifié
- `403`: Accès refusé (pas administrateur)
- `500`: Erreur serveur

---

## Services et fonctionnalités

### MetricsService
Service principal pour calculer et récupérer les métriques:

**Méthodes principales:**
- `calculate_daily_metrics(date)`: Calcule les métriques quotidiennes
- `get_user_metrics(user)`: Récupère les métriques utilisateur
- `get_project_metrics(project)`: Récupère les métriques projet
- `recalculate_project_metrics(project)`: Recalcule toutes les métriques d'un projet
- `get_period_metrics(start_date, end_date)`: Métriques pour une période
- `get_top_projects(period_days, limit, metric)`: Projets les plus performants

### EventTrackingService
Service pour le suivi des événements:

**Méthodes principales:**
- `track_event()`: Enregistre un événement générique
- `track_project_view()`: Enregistre une vue de projet
- `track_login()`: Enregistre une connexion
- `track_referral()`: Enregistre une source de référencement

### Tâches Celery
**Tâches asynchrones:**
- `calculate_daily_metrics`: Calcule les métriques quotidiennes (planifiée)
- `recalculate_historical_metrics`: Recalcule l'historique des métriques

---

## Mise à jour automatique des métriques

Les métriques sont mises à jour automatiquement via des signaux Django:

### Événements tracés automatiquement:
- **Création d'utilisateur:** Création des métriques utilisateur + événement REGISTRATION
- **Création de projet:** Mise à jour métriques utilisateur + création métriques projet
- **Publication de projet:** Mise à jour compteur projets publiés
- **Intérêt pour projet:** Mise à jour métriques projet + utilisateur + événement INTEREST
- **Investissement:** Mise à jour métriques projet + investisseur + événement INVESTMENT
- **Paiement d'abonnement:** Événement SUBSCRIPTION_STARTED
- **Changement statut abonnement:** Événements SUBSCRIPTION_STARTED/CANCELED

### Métriques de vue de projet:
Les vues de projet doivent être tracées manuellement via:
```python
from apps.analytics.services.event_tracking_service import EventTrackingService

EventTrackingService.track_project_view(
    project=project,
    user=request.user if request.user.is_authenticated else None,
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT')
)
```

---

## Support multi-devises

Tous les montants financiers peuvent être convertis dans la devise demandée:

### Devises supportées:
- EUR (Euro) - devise de base
- USD (Dollar américain)
- GBP (Livre sterling)
- CAD (Dollar canadien)
- CHF (Franc suisse)
- Et autres selon la configuration CurrencyService

### Utilisation:
Ajoutez le paramètre `currency` à vos requêtes:
```
GET /analytics/user/?currency=USD
GET /analytics/project/123/?currency=GBP
```

---

## Limitations et permissions

### Permissions requises:
- **Métriques utilisateur:** Utilisateur connecté (ses propres métriques)
- **Métriques projet:** Propriétaire du projet ou administrateur
- **Tableau de bord:** Administrateur uniquement
- **Top projets:** Administrateur uniquement

### Limites:
- **Projets top:** Maximum 50 projets par requête
- **Période personnalisée:** Maximum 365 jours
- **Taux de requête:** Selon la configuration globale de l'API

---

## Codes d'erreur standardisés

### Erreurs communes:
- `400 Bad Request`: Paramètres invalides
- `401 Unauthorized`: Token manquant ou invalide
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource non trouvée
- `429 Too Many Requests`: Limite de taux dépassée
- `500 Internal Server Error`: Erreur serveur

### Format des erreurs:
```json
{
  "error": "Message d'erreur descriptif"
}
```

---

## Intégration frontend

### Étapes d'intégration:

1. **Authentification:** Assurez-vous d'inclure le token JWT dans tous les appels
2. **Gestion des erreurs:** Implémentez une gestion robuste des codes d'erreur
3. **Conversion de devises:** Utilisez le paramètre `currency` selon les préférences utilisateur
4. **Mise en cache:** Considérez la mise en cache des métriques pour améliorer les performances
5. **Actualisation:** Actualisez les métriques après des actions utilisateur (création projet, investissement, etc.)

### Exemple d'appel:
```dart
// Récupération des métriques utilisateur
final response = await http.get(
  Uri.parse('${baseUrl}/analytics/user/?currency=EUR'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json',
  },
);

if (response.statusCode == 200) {
  final metrics = json.decode(response.body);
  // Traiter les métriques
} else {
  // Gérer l'erreur
}
```

---

## Notes importantes

1. **Performance:** Les calculs de métriques complexes sont effectués de manière asynchrone
2. **Consistance:** Les métriques peuvent avoir un léger délai de mise à jour lors de forte charge
3. **Sécurité:** Les données sensibles ne sont accessibles qu'aux utilisateurs autorisés
4. **Évolutivité:** L'architecture permet l'ajout de nouvelles métriques sans rupture de compatibilité
5. **Conformité RGPD:** Les données analytiques respectent les réglementations sur la protection des données