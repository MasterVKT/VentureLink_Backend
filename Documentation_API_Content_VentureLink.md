# Documentation API Content VentureLink

## Vue d'ensemble

L'application **Content** de VentureLink gère le contenu éditorial de la plateforme : publications administratives, articles, actualités, tutoriels, ainsi que le système de commentaires génériques utilisé sur toute la plateforme.

### Base URL
- **Développement:** `https://api-dev.venturelink.com/api/v1/content/`
- **Production:** `https://api.venturelink.com/api/v1/content/`

### Authentification
La plupart des endpoints nécessitent une authentification JWT via l'en-tête:
```
Authorization: Bearer {token}
```

---

## Modèles de données

### Publication
Contenu éditorial créé par les administrateurs:
- **Types:** `EDUCATIONAL`, `ENTERTAINING`, `MOTIVATIONAL`, `INFORMATIONAL`, `TIPS`, `ADVERTISING`, `SPONSORED`, `NEWS`, `TUTORIAL`, `CASE_STUDY`
- **Domaines:** `PROJECT_MANAGEMENT`, `FINANCE_INVESTMENT`, `ENTREPRENEURSHIP`, `PERSONAL_DEVELOPMENT`, `MARKETING_COMMUNICATION`, `TECHNOLOGY`, `BUSINESS_STRATEGY`, `LEADERSHIP`, `INNOVATION`, `NETWORKING`
- **Statuts:** `DRAFT`, `PUBLISHED`, `ARCHIVED`, `SCHEDULED`
- **Fonctionnalités:** Mise en avant, épinglage, sponsoring, SEO, programmation

### PublicationMedia
Médias associés aux publications (max 3 par publication):
- **Types:** `IMAGE`, `VIDEO`, `DOCUMENT`, `AUDIO`
- Image de couverture, ordre d'affichage
- Métadonnées : titre, description, texte alternatif

### Comment (Système générique)
Commentaires hiérarchiques pour tous les contenus:
- Support des réponses (max 3 niveaux de profondeur)
- Système de likes et signalements
- Modération et soft delete

### CommentLike & PublicationLike
Système de likes pour publications et commentaires

---

## Endpoints principaux

### Base URL: `/api/v1/content/`

## 1. Gestion des publications

### 1.1 GET /publications/
**Description:** Liste les publications avec filtres

**Authentification:** Requise

**Paramètres de requête:**
- `publication_type` (string): Type de publication
- `domain` (string): Domaine de la publication
- `status` (string): Statut (`PUBLISHED` pour utilisateurs normaux)
- `is_featured` (boolean): Publications mises en avant
- `is_sponsored` (boolean): Contenu sponsorisé
- `author_id` (UUID): Filtrer par auteur
- `search` (string): Recherche dans titre, contenu, résumé, tags
- `ordering` (string): Tri (`-published_at`, `views_count`, `likes_count`, etc.)
- `page` (integer): Numéro de page
- `page_size` (integer): Taille de page

**Réponse (200 OK):**
```json
{
  "count": 45,
  "next": "https://api.venturelink.com/api/v1/content/publications/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "10 conseils pour réussir son pitch d'investisseur",
      "summary": "Découvrez les clés pour convaincre les investisseurs lors de votre présentation",
      "publication_type": "TIPS",
      "domain": "FINANCE_INVESTMENT",
      "author": {
        "id": "uuid",
        "first_name": "Marie",
        "last_name": "Admin",
        "email": "marie@venturelink.com"
      },
      "status": "PUBLISHED",
      "published_at": "2024-01-20T10:00:00Z",
      "views_count": 1250,
      "likes_count": 89,
      "comments_count": 23,
      "is_featured": true,
      "is_pinned": false,
      "is_sponsored": false,
      "sponsor_name": null,
      "featured_media": {
        "id": "uuid",
        "file": "https://example.com/media/publications/pitch-tips.jpg",
        "media_type": "IMAGE",
        "title": "Conseils pitch investisseur",
        "is_featured": true
      },
      "tags_list": ["pitch", "investissement", "conseils", "startup"],
      "user_has_liked": false,
      "slug": "10-conseils-reussir-pitch-investisseur"
    }
  ]
}
```

### 1.2 GET /publications/{id}/
**Description:** Récupère les détails complets d'une publication

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "id": "uuid",
  "title": "10 conseils pour réussir son pitch d'investisseur",
  "content": "Contenu complet de l'article avec tous les détails, conseils pratiques, exemples concrets...",
  "summary": "Découvrez les clés pour convaincre les investisseurs",
  "publication_type": "TIPS",
  "domain": "FINANCE_INVESTMENT",
  "tags": "pitch,investissement,conseils,startup",
  "tags_list": ["pitch", "investissement", "conseils", "startup"],
  "author": {
    "id": "uuid",
    "first_name": "Marie",
    "last_name": "Admin",
    "email": "marie@venturelink.com"
  },
  "status": "PUBLISHED",
  "published_at": "2024-01-20T10:00:00Z",
  "scheduled_for": null,
  "views_count": 1250,
  "likes_count": 89,
  "comments_count": 23,
  "shares_count": 15,
  "is_featured": true,
  "is_pinned": false,
  "allow_comments": true,
  "is_sponsored": false,
  "sponsor_name": null,
  "sponsor_url": null,
  "meta_description": "Guide complet pour réussir son pitch d'investisseur avec 10 conseils pratiques",
  "slug": "10-conseils-reussir-pitch-investisseur",
  "media": [
    {
      "id": "uuid",
      "file": "https://example.com/media/publications/pitch-tips.jpg",
      "media_type": "IMAGE",
      "title": "Conseils pitch investisseur",
      "description": "Infographie des 10 conseils essentiels",
      "alt_text": "Infographie pitch investisseur",
      "order": 0,
      "is_featured": true,
      "file_size": 245760,
      "created_at": "2024-01-20T09:30:00Z"
    }
  ],
  "likes": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "first_name": "Jean",
        "last_name": "Dupont"
      },
      "created_at": "2024-01-20T11:15:00Z"
    }
  ],
  "user_has_liked": false,
  "can_be_commented": true,
  "is_published": true,
  "created_at": "2024-01-19T15:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

### 1.3 POST /publications/
**Description:** Crée une nouvelle publication (administrateurs uniquement)

**Authentification:** Requise (administrateur)

**Requête:**
```json
{
  "title": "Guide complet du business plan",
  "content": "Contenu détaillé de l'article...",
  "summary": "Apprenez à rédiger un business plan efficace",
  "publication_type": "TUTORIAL",
  "domain": "BUSINESS_STRATEGY",
  "tags": "business plan,stratégie,guide,entrepreneur",
  "status": "DRAFT",
  "is_featured": false,
  "allow_comments": true,
  "meta_description": "Guide complet pour rédiger un business plan efficace",
  "media_files": ["file1.jpg", "file2.pdf"],
  "media_types": ["IMAGE", "DOCUMENT"],
  "media_titles": ["Exemple business plan", "Template business plan"]
}
```

**Réponse (201 Created):** Même format que GET /publications/{id}/

### 1.4 PUT /publications/{id}/
**Description:** Met à jour une publication

**Authentification:** Requise (auteur ou administrateur)

### 1.5 DELETE /publications/{id}/
**Description:** Supprime une publication

**Authentification:** Requise (auteur ou administrateur)

---

## 2. Actions spéciales sur les publications

### 2.1 GET /publications/featured/
**Description:** Récupère les publications mises en avant

**Authentification:** Requise

**Réponse (200 OK):** Liste des 10 publications featured

### 2.2 GET /publications/pinned/
**Description:** Récupère les publications épinglées

**Authentification:** Requise

### 2.3 GET /publications/by_type/
**Description:** Récupère les publications par type

**Authentification:** Requise

**Paramètres:**
- `type` (string): Type de publication requis

**Exemple:** `GET /publications/by_type/?type=TUTORIAL`

### 2.4 GET /publications/by_domain/
**Description:** Récupère les publications par domaine

**Authentification:** Requise

**Paramètres:**
- `domain` (string): Domaine requis

**Exemple:** `GET /publications/by_domain/?domain=ENTREPRENEURSHIP`

### 2.5 POST /publications/{id}/like/
**Description:** Ajoute/retire un like sur une publication

**Authentification:** Requise

**Réponse (200/201):**
```json
{
  "detail": "Publication likée.",
  "liked": true
}
```

### 2.6 POST /publications/{id}/share/
**Description:** Incrémente le compteur de partages

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "detail": "Publication partagée.",
  "shares_count": 16
}
```

### 2.7 GET /publications/admin_stats/
**Description:** Statistiques pour les administrateurs

**Authentification:** Requise (administrateur)

**Réponse (200 OK):**
```json
{
  "total_publications": 156,
  "published_count": 134,
  "draft_count": 18,
  "archived_count": 4,
  "total_views": 45230,
  "total_likes": 3421,
  "total_comments": 892,
  "by_type": {
    "EDUCATIONAL": 45,
    "TIPS": 32,
    "NEWS": 28,
    "TUTORIAL": 21
  },
  "by_domain": {
    "ENTREPRENEURSHIP": 67,
    "FINANCE_INVESTMENT": 34,
    "TECHNOLOGY": 28
  }
}
```

---

## 3. Gestion des médias de publication

### Base URL: `/api/v1/content/publication-media/`

### 3.1 GET /publication-media/
**Description:** Liste les médias de publications

**Authentification:** Requise

**Paramètres:**
- `publication` (UUID): Filtrer par publication

### 3.2 POST /publication-media/
**Description:** Ajoute un média à une publication

**Authentification:** Requise (auteur ou administrateur)

**Requête:** Form-data
- `publication` (UUID): ID de la publication
- `file` (fichier): Fichier média
- `media_type` (string): `IMAGE`, `VIDEO`, `DOCUMENT`, `AUDIO`
- `title` (string): Titre du média
- `description` (string): Description
- `alt_text` (string): Texte alternatif
- `order` (integer): Ordre (0, 1, 2)
- `is_featured` (boolean): Image de couverture

### 3.3 PUT /publication-media/{id}/
**Description:** Met à jour un média

**Authentification:** Requise (auteur ou administrateur)

### 3.4 DELETE /publication-media/{id}/
**Description:** Supprime un média

**Authentification:** Requise (auteur ou administrateur)

---

## 4. Système de commentaires génériques

### Base URL: `/api/v1/content/comments/`

### 4.1 GET /comments/
**Description:** Liste les commentaires avec filtres

**Authentification:** Requise

**Paramètres:**
- `content_type` (string): Type d'objet (ex: "content.publication")
- `object_id` (UUID): ID de l'objet commenté
- `parent_only` (boolean): Commentaires parents uniquement

### 4.2 GET /comments/for_object/
**Description:** Récupère tous les commentaires pour un objet avec hiérarchie

**Authentification:** Requise

**Paramètres requis:**
- `content_type` (string): Type d'objet (ex: "content.publication")
- `object_id` (UUID): ID de l'objet

**Réponse (200 OK):**
```json
[
  {
    "id": "uuid",
    "content": "Excellent article ! Très utile pour préparer mon pitch.",
    "author": {
      "id": "uuid",
      "first_name": "Jean",
      "last_name": "Dupont"
    },
    "parent": null,
    "likes_count": 5,
    "replies_count": 2,
    "is_edited": false,
    "edited_at": null,
    "user_has_liked": false,
    "depth": 0,
    "can_have_replies": true,
    "created_at": "2024-01-20T12:30:00Z",
    "replies": [
      {
        "id": "uuid",
        "content": "Je suis d'accord, ces conseils sont très pratiques !",
        "author": {
          "id": "uuid",
          "first_name": "Marie",
          "last_name": "Martin"
        },
        "parent": "uuid",
        "likes_count": 2,
        "replies_count": 0,
        "depth": 1,
        "created_at": "2024-01-20T13:15:00Z",
        "replies": []
      }
    ]
  }
]
```

### 4.3 POST /comments/
**Description:** Crée un nouveau commentaire

**Authentification:** Requise

**Requête:**
```json
{
  "content_type": "content.publication",
  "object_id": "uuid",
  "content": "Merci pour cet article très instructif !",
  "parent": null
}
```

**Réponse (201 Created):**
```json
{
  "id": "uuid",
  "content": "Merci pour cet article très instructif !",
  "author": {
    "id": "uuid",
    "first_name": "Jean",
    "last_name": "Dupont"
  },
  "parent": null,
  "likes_count": 0,
  "replies_count": 0,
  "is_edited": false,
  "user_has_liked": false,
  "depth": 0,
  "can_have_replies": true,
  "created_at": "2024-01-20T14:30:00Z"
}
```

### 4.4 PUT /comments/{id}/
**Description:** Met à jour un commentaire

**Authentification:** Requise (auteur ou administrateur)

**Requête:**
```json
{
  "content": "Merci pour cet article très instructif ! Mise à jour du commentaire."
}
```

### 4.5 DELETE /comments/{id}/
**Description:** Supprime un commentaire (soft delete)

**Authentification:** Requise (auteur ou administrateur)

**Note:** Le commentaire est marqué comme inactif au lieu d'être supprimé

### 4.6 GET /comments/{id}/replies/
**Description:** Récupère les réponses d'un commentaire

**Authentification:** Requise

### 4.7 POST /comments/{id}/like/
**Description:** Ajoute/retire un like sur un commentaire

**Authentification:** Requise

**Réponse (200/201):**
```json
{
  "detail": "Commentaire liké.",
  "liked": true
}
```

### 4.8 POST /comments/{id}/flag/
**Description:** Signale un commentaire

**Authentification:** Requise

**Réponse (200 OK):**
```json
{
  "detail": "Commentaire signalé."
}
```

---

## 5. Likes de publications et commentaires

### 5.1 GET /publication-likes/
**Description:** Liste les likes de publications

**Authentification:** Requise

**Paramètres:**
- `publication` (UUID): Filtrer par publication

### 5.2 GET /comment-likes/
**Description:** Liste les likes de commentaires

**Authentification:** Requise

**Paramètres:**
- `comment_id` (UUID): Filtrer par commentaire

---

## Types et domaines disponibles

### Types de publications:
```json
{
  "EDUCATIONAL": "Éducatif",
  "ENTERTAINING": "Divertissant", 
  "MOTIVATIONAL": "Motivant",
  "INFORMATIONAL": "Informatif",
  "TIPS": "Conseils",
  "ADVERTISING": "Publicitaire",
  "SPONSORED": "Sponsorisé",
  "NEWS": "Actualités",
  "TUTORIAL": "Tutoriel",
  "CASE_STUDY": "Étude de cas"
}
```

### Domaines de publications:
```json
{
  "PROJECT_MANAGEMENT": "Gestion de projets",
  "FINANCE_INVESTMENT": "Finances et investissements",
  "ENTREPRENEURSHIP": "Entrepreneuriat",
  "PERSONAL_DEVELOPMENT": "Développement personnel",
  "MARKETING_COMMUNICATION": "Marketing et communication",
  "TECHNOLOGY": "Technologie",
  "BUSINESS_STRATEGY": "Stratégie d'entreprise",
  "LEADERSHIP": "Leadership",
  "INNOVATION": "Innovation",
  "NETWORKING": "Réseautage"
}
```

---

## Permissions et limitations

### Permissions par action:
- **Lecture:** Utilisateurs authentifiés (publications publiées uniquement)
- **Création publications:** Administrateurs uniquement
- **Modification publications:** Auteur ou administrateur
- **Création commentaires:** Utilisateurs authentifiés
- **Modification commentaires:** Auteur ou administrateur
- **Likes:** Utilisateurs authentifiés

### Limitations:
- **Médias par publication:** Maximum 3
- **Profondeur commentaires:** Maximum 3 niveaux
- **Taille commentaires:** Maximum 2000 caractères
- **Signalements:** Pas ses propres commentaires

---

## Fonctionnalités automatiques

### Signaux Django:
- **Création like:** Incrémentation automatique des compteurs
- **Suppression like:** Décrémentation automatique des compteurs
- **Création commentaire:** Mise à jour compteur parent et objet commenté
- **Génération slug:** Automatique à partir du titre

### Soft Delete:
- Les commentaires sont marqués comme inactifs au lieu d'être supprimés
- Préservation de l'intégrité des discussions

---

## Intégration frontend

### Exemple de récupération de publications:
```dart
// Récupération de publications par type
Future<List<Publication>> getPublicationsByType(String type) async {
  final uri = Uri.parse('${baseUrl}/content/publications/by_type/')
      .replace(queryParameters: {'type': type});
  
  final response = await http.get(uri, headers: authHeaders);
  
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    return (data['results'] as List)
        .map((json) => Publication.fromJson(json))
        .toList();
  }
  throw Exception('Failed to load publications');
}
```

### Exemple de gestion des commentaires:
```dart
// Récupération des commentaires avec hiérarchie
Future<List<Comment>> getCommentsForObject(
  String contentType, 
  String objectId
) async {
  final uri = Uri.parse('${baseUrl}/content/comments/for_object/')
      .replace(queryParameters: {
        'content_type': contentType,
        'object_id': objectId,
      });
  
  final response = await http.get(uri, headers: authHeaders);
  
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    return (data as List)
        .map((json) => Comment.fromJson(json))
        .toList();
  }
  throw Exception('Failed to load comments');
}

// Création d'un commentaire
Future<Comment> createComment({
  required String contentType,
  required String objectId,
  required String content,
  String? parentId,
}) async {
  final response = await http.post(
    Uri.parse('${baseUrl}/content/comments/'),
    headers: {...authHeaders, 'Content-Type': 'application/json'},
    body: json.encode({
      'content_type': contentType,
      'object_id': objectId,
      'content': content,
      if (parentId != null) 'parent': parentId,
    }),
  );
  
  if (response.statusCode == 201) {
    return Comment.fromJson(json.decode(response.body));
  }
  throw Exception('Failed to create comment');
}
```

### Upload de médias pour publications:
```dart
// Upload de média pour une publication
Future<PublicationMedia> uploadPublicationMedia(
  String publicationId,
  File file,
  String mediaType,
  {String? title, bool isFeatured = false}
) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('${baseUrl}/content/publication-media/'),
  );
  
  request.headers.addAll(authHeaders);
  request.fields['publication'] = publicationId;
  request.fields['media_type'] = mediaType;
  request.fields['is_featured'] = isFeatured.toString();
  if (title != null) request.fields['title'] = title;
  
  request.files.add(await http.MultipartFile.fromPath('file', file.path));
  
  final response = await request.send();
  if (response.statusCode == 201) {
    final responseData = await response.stream.bytesToString();
    return PublicationMedia.fromJson(json.decode(responseData));
  }
  throw Exception('Failed to upload media');
}
```

---

## Codes d'erreur

### Erreurs communes:
- `400`: Données invalides ou paramètres manquants
- `401`: Non authentifié
- `403`: Permissions insuffisantes (non-admin pour publications)
- `404`: Publication/commentaire non trouvé
- `413`: Fichier trop volumineux
- `415`: Type de fichier non supporté

### Exemple d'erreur:
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Seuls les administrateurs peuvent créer des publications",
    "details": {}
  }
}
```

---

## Notes importantes

1. **Publications:** Seuls les administrateurs peuvent créer du contenu éditorial
2. **Commentaires génériques:** Utilisables sur tous les objets de la plateforme
3. **Hiérarchie:** Maximum 3 niveaux de réponses aux commentaires
4. **Médias:** Maximum 3 médias par publication, formats supportés: images, vidéos, documents, audio
5. **SEO:** Support complet avec meta descriptions et slugs automatiques
6. **Modération:** Système de signalement et soft delete pour les commentaires
7. **Performance:** Optimisations avec select_related et prefetch_related
8. **Sponsoring:** Support du contenu sponsorisé avec métadonnées dédiées