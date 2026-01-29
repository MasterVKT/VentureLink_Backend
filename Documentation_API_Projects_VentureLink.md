# Documentation API Projects VentureLink

## Vue d'ensemble

L'application **Projects** de VentureLink constitue le cœur métier de la plateforme. Elle gère tous les aspects liés aux projets entrepreneuriaux : création, gestion, publication, interactions, médias, besoins et recherche avancée.

### Base URL
- **Développement:** `https://api-dev.venturelink.com/api/v1/projects/`
- **Production:** `https://api.venturelink.com/api/v1/projects/`

### Authentification
La plupart des endpoints nécessitent une authentification JWT via l'en-tête:
```
Authorization: Bearer {token}
```

---

## Modèles de données

### Project (Projet principal)
Modèle central représentant un projet entrepreneurial:
- **Stades:** `IDEA`, `PROTOTYPE`, `DEVELOPMENT`, `GROWTH`
- **Statuts:** `ACTIVE`, `INACTIVE`, `FUNDED`, `ARCHIVED`
- **Champs principaux:** Titre, descriptions, catégorie, financement, localisation
- **Fonctionnalités:** Draft/Publication, Premium, Vérification, Statistiques

### ProjectCategory (Catégorie)
Classification des projets avec support multilingue (FR/EN):
- Nom, description, icône par langue
- Statut actif/inactif

### ProjectTag (Tag)
Étiquettes pour identifier les projets par mots-clés:
- Nom multilingue (FR/EN)
- Association many-to-many avec les projets

### ProjectMedia (Médias)
Gestion des fichiers multimédias des projets:
- **Types:** `IMAGE`, `VIDEO`, `DOCUMENT`
- Image principale, ordre d'affichage
- Titre et description pour chaque média

### ProjectInteraction (Interactions)
Gestion des interactions utilisateur:
- **ProjectInterest:** Intérêts avec message et montant d'investissement
- **ProjectFavorite:** Projets favoris avec notes personnelles
- **ProjectQuestion/Answer:** Système de Q&A public/privé

### ProjectNeeds (Besoins)
Besoins du projet en ressources:
- **Types:** `INVESTMENT`, `LOAN`, `PARTNERSHIP`, `EXPERTISE`, `MATERIAL`
- Montant, caractère critique, échéance
- **ProjectSkillsNeeded:** Compétences spécifiques avec niveau requis

---

## Endpoints principaux

### Base URL: `/api/v1/projects/`

## 1. Gestion des projets

### 1.1 GET /projects/
**Description:** Liste les projets avec filtres avancés

**Authentification:** Non requise (projets publics) / Requise (projets personnels)

**Paramètres de requête:**
- `category` (UUID): Filtrer par catégorie
- `stage` (string): Filtrer par stade (`IDEA`, `PROTOTYPE`, etc.)
- `tags` (string): Liste d'IDs de tags séparés par virgules
- `location_country` (string): Filtrer par pays
- `location_city` (string): Filtrer par ville
- `funding_min` (decimal): Financement minimum
- `funding_max` (decimal): Financement maximum
- `funding_currency` (string): Devise pour conversion (défaut: EUR)
- `search` (string): Recherche textuelle
- `is_premium` (boolean): Projets premium uniquement
- `is_featured` (boolean): Projets mis en avant
- `is_verified` (boolean): Projets vérifiés
- `ordering` (string): Tri (`-created_at`, `views_count`, `interests_count`, etc.)
- `page` (integer): Numéro de page
- `page_size` (integer): Taille de page (max 50)

**Réponse (200 OK):**
```json
{
  "count": 156,
  "next": "https://api.venturelink.com/api/v1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Application de gestion écologique",
      "short_description": "App mobile pour réduire l'empreinte carbone",
      "category": {
        "id": "uuid",
        "name_fr": "Technologie",
        "name_en": "Technology",
        "icon": "tech"
      },
      "tags": [
        {
          "id": "uuid",
          "name_fr": "Écologie",
          "name_en": "Ecology"
        }
      ],
      "stage": "PROTOTYPE",
      "funding_min": 50000.00,
      "funding_max": 200000.00,
      "funding_currency": "EUR",
      "location_country": "France",
      "location_city": "Paris",
      "creator_name": "Marie Dupont",
      "primary_image_url": "https://example.com/media/projects/image.jpg",
      "media_urls": [
        {
          "id": "uuid",
          "url": "https://example.com/media/projects/image1.jpg",
          "type": "IMAGE",
          "title": "Interface principale",
          "description": "Vue d'ensemble de l'application",
          "is_primary": true,
          "order": 1
        }
      ],
      "views_count": 1245,
      "interests_count": 23,
      "favorites_count": 45,
      "is_premium": true,
      "is_featured": false,
      "is_verified": true,
      "verified_at": "2024-01-20T10:00:00Z",
      "verification_status_display": "Vérifié",
      "published_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### 1.2 GET /projects/{id}/
**Description:** Récupère les détails complets d'un projet

**Authentification:** Non requise (projets publics) / Requise (brouillons)

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "title": "Application de gestion écologique",
  "short_description": "App mobile pour réduire l'empreinte carbone",
  "full_description": "Description complète du projet avec tous les détails techniques, business model, équipe, etc.",
  "category": {
    "id": "uuid",
    "name_fr": "Technologie",
    "name_en": "Technology",
    "icon": "tech"
  },
  "tags": [
    {
      "id": "uuid",
      "name_fr": "Écologie",
      "name_en": "Ecology"
    }
  ],
  "stage": "PROTOTYPE",
  "funding_min": 50000.00,
  "funding_max": 200000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Paris",
  "creator_id": "uuid",
  "creator_name": "Marie Dupont",
  "creator_profile_picture": "https://example.com/media/profiles/marie.jpg",
  "views_count": 1245,
  "interests_count": 23,
  "favorites_count": 45,
  "is_premium": true,
  "is_featured": false,
  "is_verified": true,
  "verified_at": "2024-01-20T10:00:00Z",
  "verification_status_display": "Vérifié",
  "is_draft": false,
  "status": "ACTIVE",
  "published_at": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z",
  "video_url": "https://youtube.com/watch?v=example"
}
```

### 1.3 POST /projects/
**Description:** Crée un nouveau projet

**Authentification:** Requise

**Requête:**
```json
{
  "title": "Application de gestion écologique",
  "short_description": "App mobile pour réduire l'empreinte carbone",
  "full_description": "Description complète du projet...",
  "category": "uuid",
  "stage": "PROTOTYPE",
  "funding_min": 50000.00,
  "funding_max": 200000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Paris",
  "tags": ["uuid1", "uuid2"],
  "is_draft": true,
  "video_url": "https://youtube.com/watch?v=example"
}
```

**Réponse (201 Created):** Même format que GET /projects/{id}/

### 1.4 PUT /projects/{id}/
**Description:** Met à jour un projet

**Authentification:** Requise (créateur uniquement)

**Requête:** Même format que POST

**Réponse (200 OK):** Projet mis à jour

### 1.5 DELETE /projects/{id}/
**Description:** Supprime un projet

**Authentification:** Requise (créateur uniquement)

**Réponse (204 No Content)**

---

## 2. Actions spéciales sur les projets

### 2.1 POST /projects/{id}/publish/
**Description:** Publie un projet (sort du mode brouillon)

**Authentification:** Requise (créateur)

**Requête:**
```json
{
  "is_draft": false
}
```

**Réponse (200 OK):**
```json
{
  "message": "Projet publié avec succès",
  "published_at": "2024-01-20T15:30:00Z"
}
```

### 2.2 POST /projects/{id}/verify/
**Description:** Vérifie un projet (administrateurs uniquement)

**Authentification:** Requise (administrateur)

**Requête:**
```json
{
  "is_verified": true,
  "verification_notes": "Projet validé après vérification complète"
}
```

### 2.3 POST /projects/{id}/toggle-favorite/
**Description:** Ajoute/retire un projet des favoris

**Authentification:** Requise

**Requête:**
```json
{
  "notes": "Notes personnelles sur ce projet"
}
```

**Réponse (200 OK):**
```json
{
  "is_favorite": true,
  "message": "Projet ajouté aux favoris"
}
```

### 2.4 POST /projects/{id}/toggle-interest/
**Description:** Exprime/retire un intérêt pour un projet

**Authentification:** Requise

**Requête:**
```json
{
  "message": "Je suis intéressé par ce projet pour un investissement",
  "investment_amount": 75000.00,
  "investment_currency": "EUR",
  "is_anonymous": false
}
```

**Réponse (200 OK):**
```json
{
  "has_interest": true,
  "interest_id": "uuid",
  "message": "Intérêt exprimé avec succès"
}
```

---

## 3. Collections spéciales

### 3.1 GET /projects/my-projects/
**Description:** Récupère les projets de l'utilisateur connecté

**Authentification:** Requise

**Paramètres:** Mêmes filtres que GET /projects/

### 3.2 GET /projects/trending/
**Description:** Projets tendance (plus consultés récemment)

**Authentification:** Non requise

**Paramètres:**
- `days` (integer): Période en jours (défaut: 7)
- `limit` (integer): Nombre de projets (défaut: 10, max: 50)

### 3.3 GET /projects/featured/
**Description:** Projets mis en avant

**Authentification:** Non requise

**Paramètres:**
- `limit` (integer): Nombre de projets (défaut: 10)

### 3.4 GET /projects/verified/
**Description:** Projets vérifiés

**Authentification:** Non requise

### 3.5 GET /projects/{id}/related/
**Description:** Projets similaires/liés

**Authentification:** Non requise

**Paramètres:**
- `limit` (integer): Nombre de projets (défaut: 5)

### 3.6 GET /projects/favorites/
**Description:** Projets favoris de l'utilisateur

**Authentification:** Requise

### 3.7 GET /projects/interests/
**Description:** Projets pour lesquels l'utilisateur a exprimé un intérêt

**Authentification:** Requise

---

## 4. Recherche avancée

### 4.1 GET /projects/search/
**Description:** Recherche avancée avec filtres complexes

**Authentification:** Non requise

**Paramètres étendus:**
- Tous les paramètres de GET /projects/
- `min_funding_range` / `max_funding_range`: Plages de financement
- `creation_date_from` / `creation_date_to`: Plage de dates
- `has_video` (boolean): Projets avec vidéo
- `has_business_plan` (boolean): Projets avec business plan
- `min_views`, `max_views`: Plage de vues
- `min_interests`, `max_interests`: Plage d'intérêts

### 4.2 GET /projects/filter-options/
**Description:** Options disponibles pour les filtres

**Authentification:** Non requise

**Réponse (200 OK):**
```json
{
  "categories": [
    {
      "id": "uuid",
      "name_fr": "Technologie",
      "name_en": "Technology",
      "project_count": 45
    }
  ],
  "tags": [
    {
      "id": "uuid",
      "name_fr": "IA",
      "name_en": "AI",
      "project_count": 12
    }
  ],
  "stages": [
    {
      "value": "IDEA",
      "label": "Idée",
      "project_count": 23
    }
  ],
  "countries": [
    {
      "name": "France",
      "project_count": 67
    }
  ],
  "funding_ranges": {
    "min": 1000,
    "max": 5000000,
    "average": 125000
  }
}
```

---

## 5. Gestion des médias

### Base URL: `/api/v1/projects/{project_id}/media/`

### 5.1 GET /projects/{project_id}/media/
**Description:** Liste les médias d'un projet

**Authentification:** Non requise (projet public)

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "file": "https://example.com/media/projects/image.jpg",
    "media_type": "IMAGE",
    "title": "Interface principale",
    "description": "Vue d'ensemble de l'application",
    "is_primary": true,
    "order": 1,
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

### 5.2 POST /projects/{project_id}/media/
**Description:** Ajoute un média au projet

**Authentification:** Requise (créateur)

**Requête:** Form-data
- `file` (fichier): Fichier image/vidéo/document
- `media_type` (string): `IMAGE`, `VIDEO`, `DOCUMENT`
- `title` (string): Titre du média
- `description` (string): Description
- `is_primary` (boolean): Image principale
- `order` (integer): Ordre d'affichage

### 5.3 PUT /projects/{project_id}/media/{media_id}/
**Description:** Met à jour un média

**Authentification:** Requise (créateur)

### 5.4 DELETE /projects/{project_id}/media/{media_id}/
**Description:** Supprime un média

**Authentification:** Requise (créateur)

---

## 6. Gestion des besoins

### Base URL: `/api/v1/projects/{project_id}/needs/`

### 6.1 GET /projects/{project_id}/needs/
**Description:** Liste les besoins d'un projet

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "resource_type": "INVESTMENT",
    "title": "Financement série A",
    "description": "Recherche d'investisseurs pour le développement",
    "amount": "250000.00",
    "amount_currency": "EUR",
    "is_critical": true,
    "deadline": "2024-06-30",
    "is_satisfied": false,
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

### 6.2 POST /projects/{project_id}/needs/
**Description:** Ajoute un besoin au projet

**Authentification:** Requise (créateur)

**Requête:**
```json
{
  "resource_type": "INVESTMENT",
  "title": "Financement série A",
  "description": "Recherche d'investisseurs pour le développement",
  "amount": "250000.00",
  "is_critical": true,
  "deadline": "2024-06-30"
}
```

---

## 7. Compétences requises

### Base URL: `/api/v1/projects/{project_id}/skills/`

### 7.1 GET /projects/{project_id}/skills/
**Description:** Liste les compétences requises

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "name": "Développement React Native",
    "description": "Développement d'applications mobiles",
    "priority": "HIGH",
    "required_level": 4,
    "is_satisfied": false,
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

### 7.2 POST /projects/{project_id}/skills/
**Description:** Ajoute une compétence requise

**Authentification:** Requise (créateur)

**Requête:**
```json
{
  "name": "Développement React Native",
  "description": "Développement d'applications mobiles",
  "priority": "HIGH",
  "required_level": 4
}
```

---

## 8. Interactions et questions

### 8.1 Intérêts - GET /interests/
**Description:** Liste les intérêts (admin) ou de l'utilisateur

**Authentification:** Requise

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "user": {
      "id": "uuid",
      "name": "Jean Dupont",
      "email": "jean@example.com"
    },
    "project": {
      "id": "uuid",
      "title": "Application écologique"
    },
    "message": "Je suis intéressé par ce projet",
    "status": "PENDING",
    "is_anonymous": false,
    "investment_amount": "75000.00",
    "investment_currency": "EUR",
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

### 8.2 Questions - GET /questions/
**Description:** Liste les questions publiques

**Authentification:** Non requise

**Paramètres:**
- `project` (UUID): Filtrer par projet
- `is_answered` (boolean): Questions répondues/non répondues

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "user": {
      "id": "uuid",
      "name": "Marie Martin"
    },
    "project": {
      "id": "uuid",
      "title": "Application écologique"
    },
    "question": "Quel est votre modèle économique ?",
    "is_public": true,
    "is_answered": true,
    "answer": {
      "id": "uuid",
      "answered_by": {
        "id": "uuid",
        "name": "Jean Dupont"
      },
      "answer": "Notre modèle repose sur un freemium avec abonnement premium",
      "created_at": "2024-01-16T10:00:00Z"
    },
    "created_at": "2024-01-15T14:30:00Z"
  }
]
```

### 8.3 POST /questions/
**Description:** Pose une question sur un projet

**Authentification:** Requise

**Requête:**
```json
{
  "project": "uuid",
  "question": "Quel est votre modèle économique ?",
  "is_public": true
}
```

---

## 9. Catégories et tags

### 9.1 GET /categories/
**Description:** Liste les catégories disponibles

**Authentification:** Non requise

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "name_fr": "Technologie",
    "name_en": "Technology",
    "icon": "tech",
    "description_fr": "Projets technologiques",
    "description_en": "Technology projects"
  }
]
```

### 9.2 GET /tags/
**Description:** Liste les tags disponibles

**Authentification:** Non requise

**Paramètres:**
- `search` (string): Recherche dans les noms de tags

---

## Support multi-devises

Tous les montants financiers supportent la conversion automatique via le paramètre `currency`:

### Devises supportées:
- EUR (Euro) - devise de base
- USD (Dollar américain)
- GBP (Livre sterling)
- CAD (Dollar canadien)
- CHF (Franc suisse)

### Utilisation:
```
GET /projects/?funding_min=10000&funding_max=100000&funding_currency=USD
```

---

## Permissions et limitations

### Permissions par action:
- **Lecture publique:** Projets publiés accessibles à tous
- **Lecture privée:** Brouillons accessibles au créateur uniquement
- **Création:** Utilisateurs authentifiés
- **Modification:** Créateur du projet uniquement
- **Vérification:** Administrateurs uniquement
- **Suppression:** Créateur ou administrateur

### Limitations par plan:
| Fonctionnalité | Gratuit | Premium Mensuel | Premium Annuel |
|---|---|---|---|
| Projets créés | 2 | 10 | Illimité |
| Médias par projet | 3 | 10 | Illimité |
| Business plan | ❌ | ✅ | ✅ |
| Mise en avant | ❌ | 1 projet | 3 projets |
| Analytics détaillées | ❌ | ✅ | ✅ |

---

## Codes d'erreur

### Erreurs communes:
- `400`: Données invalides
- `401`: Non authentifié
- `403`: Permissions insuffisantes
- `404`: Projet non trouvé
- `413`: Fichier trop volumineux
- `415`: Type de fichier non supporté

### Exemple d'erreur:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Les données fournies sont invalides",
    "details": {
      "funding_min": ["Le financement minimum ne peut pas être supérieur au maximum"],
      "title": ["Ce champ est obligatoire"]
    }
  }
}
```

---

## Fonctionnalités automatiques

### Signaux Django:
- **Création de projet:** Création automatique des métriques
- **Publication:** Mise à jour des compteurs et notifications
- **Intérêts/Favoris:** Mise à jour automatique des compteurs
- **Suppression:** Nettoyage automatique des fichiers

### Cache et performance:
- Cache des listes de projets (15 minutes)
- Optimisation des requêtes avec select_related/prefetch_related
- Pagination automatique pour les grandes collections

---

## Intégration frontend

### Exemple de récupération de projets:
```dart
// Récupération de projets avec filtres
Future<List<Project>> getProjects({
  String? category,
  String? search,
  List<String>? stages,
  double? fundingMin,
  double? fundingMax,
  String currency = 'EUR',
  int page = 1,
}) async {
  final params = <String, String>{
    'page': page.toString(),
    'currency': currency,
  };
  
  if (category != null) params['category'] = category;
  if (search != null) params['search'] = search;
  if (stages != null) params['stage'] = stages.join(',');
  if (fundingMin != null) params['funding_min'] = fundingMin.toString();
  if (fundingMax != null) params['funding_max'] = fundingMax.toString();
  
  final uri = Uri.parse('${baseUrl}/projects/').replace(queryParameters: params);
  final response = await http.get(uri, headers: authHeaders);
  
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    return (data['results'] as List)
        .map((json) => Project.fromJson(json))
        .toList();
  }
  throw Exception('Failed to load projects');
}
```

### Upload de médias:
```dart
// Upload d'image pour un projet
Future<ProjectMedia> uploadProjectMedia(
  String projectId,
  File file,
  ProjectMediaType type,
  {String? title, String? description, bool isPrimary = false}
) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('${baseUrl}/projects/$projectId/media/'),
  );
  
  request.headers.addAll(authHeaders);
  request.fields['media_type'] = type.name;
  request.fields['is_primary'] = isPrimary.toString();
  if (title != null) request.fields['title'] = title;
  if (description != null) request.fields['description'] = description;
  
  request.files.add(await http.MultipartFile.fromPath('file', file.path));
  
  final response = await request.send();
  if (response.statusCode == 201) {
    final responseData = await response.stream.bytesToString();
    return ProjectMedia.fromJson(json.decode(responseData));
  }
  throw Exception('Failed to upload media');
}
```

---

## Notes importantes

1. **Performance:** Utilisez la pagination et les filtres pour optimiser les performances
2. **Cache:** Les listes publiques sont mises en cache côté serveur
3. **Médias:** Taille max 10MB par fichier, formats supportés: JPG, PNG, MP4, PDF
4. **Recherche:** La recherche textuelle utilise PostgreSQL full-text search
5. **Notifications:** Les intérêts et questions déclenchent des notifications automatiques
6. **Analytics:** Chaque vue de projet incrémente automatiquement le compteur
7. **Sécurité:** Validation stricte des permissions pour tous les endpoints
8. **Internationalisation:** Support complet français/anglais pour catégories et tags