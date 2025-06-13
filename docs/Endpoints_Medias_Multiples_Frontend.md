# Documentation des Endpoints - Médias Multiples VentureLink

## 🎯 Problème identifié

Le frontend ne récupère actuellement qu'**un seul média par projet** car :

1. **Le `ProjectListSerializer` backend ne retourne que `primary_image_url`**
2. **Les endpoints pour récupérer tous les médias ne sont pas documentés**
3. **Le frontend n'utilise pas les endpoints de médias multiples**

## 📡 Endpoints API Disponibles

### 1. ❌ Endpoint actuel (problématique)
```http
GET /api/v1/projects/
```
**Réponse actuelle :**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "Mon Projet",
      "primary_image_url": "https://example.com/image1.jpg",  // ⚠️ UN SEUL MÉDIA
      // ... autres champs
    }
  ]
}
```

### 2. ✅ Solution : Modifier le backend

**Fichier à modifier :** `apps/projects/serializers/project_serializer.py`

```python
class ProjectListSerializer(serializers.ModelSerializer):
    # ... champs existants ...
    media_urls = serializers.SerializerMethodField()  # 🔥 NOUVEAU
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'short_description', 'category', 'tags',
            'stage', 'funding_min', 'funding_max', 'funding_currency',
            'location_country', 'location_city', 'creator_name',
            'primary_image_url',  # Gardé pour compatibilité
            'media_urls',  # 🔥 NOUVEAU : tous les médias
            'views_count', 'interests_count', 'favorites_count',
            'is_premium', 'is_featured', 'published_at'
        ]
    
    def get_media_urls(self, obj):
        """Retourne tous les médias du projet."""
        return [
            {
                'id': str(media.id),
                'url': media.file.url if media.file else None,
                'type': media.media_type,
                'title': media.title,
                'description': media.description,
                'is_primary': media.is_primary,
                'order': media.order
            }
            for media in obj.media.order_by('order', '-created_at')
        ]
```

### 3. ✅ Endpoints de médias disponibles

```http
# Lister tous les médias d'un projet
GET /api/v1/projects/{project_id}/media/

# Créer un nouveau média (avec vérification de limite)
POST /api/v1/projects/{project_id}/media/
Content-Type: multipart/form-data

# Récupérer un média spécifique
GET /api/v1/projects/{project_id}/media/{media_id}/

# Modifier un média
PATCH /api/v1/projects/{project_id}/media/{media_id}/

# Supprimer un média
DELETE /api/v1/projects/{project_id}/media/{media_id}/

# Actions spéciales
POST /api/v1/projects/{project_id}/media/{media_id}/set-primary/
POST /api/v1/projects/{project_id}/media/reorder/
POST /api/v1/projects/{project_id}/media/generate/

# 🎯 Vérifier les limites de médias
GET /api/v1/projects/{project_id}/media/limits/
```

### 4. 🎯 Endpoint des limites (critique pour le frontend)

```http
GET /api/v1/projects/{project_id}/media/limits/
```

**Réponse :**
```json
{
  "can_add": true,
  "limit": 3,
  "current": 1,
  "remaining": 2,
  "is_premium": true,
  "upgrade_message": "Compte premium : jusqu'à 3 médias par projet."
}
```

## 📱 Implémentation Flutter

### 1. Modèles de données

```dart
// models/project_media.dart
class ProjectMedia {
  final String id;
  final String url;
  final String type; // 'image', 'video', 'document'
  final String? title;
  final String? description;
  final bool isPrimary;
  final int order;

  ProjectMedia({
    required this.id,
    required this.url,
    required this.type,
    this.title,
    this.description,
    required this.isPrimary,
    required this.order,
  });

  factory ProjectMedia.fromJson(Map<String, dynamic> json) {
    return ProjectMedia(
      id: json['id'],
      url: json['url'] ?? '',
      type: json['type'] ?? 'image',
      title: json['title'],
      description: json['description'],
      isPrimary: json['is_primary'] ?? false,
      order: json['order'] ?? 0,
    );
  }
}

// models/media_limits.dart
class MediaLimits {
  final bool canAdd;
  final int limit;
  final int current;
  final int remaining;
  final bool isPremium;
  final String upgradeMessage;

  MediaLimits({
    required this.canAdd,
    required this.limit,
    required this.current,
    required this.remaining,
    required this.isPremium,
    required this.upgradeMessage,
  });

  factory MediaLimits.fromJson(Map<String, dynamic> json) {
    return MediaLimits(
      canAdd: json['can_add'] ?? false,
      limit: json['limit'] ?? 1,
      current: json['current'] ?? 0,
      remaining: json['remaining'] ?? 0,
      isPremium: json['is_premium'] ?? false,
      upgradeMessage: json['upgrade_message'] ?? '',
    );
  }
}
```

### 2. Mise à jour du modèle Project

```dart
// models/project.dart
class Project {
  // ... autres propriétés existantes ...
  final List<ProjectMedia> mediaList; // 🔥 NOUVEAU
  final String? primaryImageUrl; // Gardé pour compatibilité
  
  Project({
    // ... autres paramètres ...
    this.mediaList = const [],
    this.primaryImageUrl,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      // ... autres mappings existants ...
      mediaList: (json['media_urls'] as List<dynamic>?)
          ?.map((media) => ProjectMedia.fromJson(media))
          .toList() ?? [],
      primaryImageUrl: json['primary_image_url'],
    );
  }

  // Utilitaires
  ProjectMedia? get primaryMedia {
    return mediaList.where((media) => media.isPrimary).firstOrNull ??
           mediaList.firstOrNull;
  }

  List<ProjectMedia> get imageMedias {
    return mediaList.where((media) => media.type == 'image').toList();
  }

  String? get displayImageUrl {
    return primaryMedia?.url ?? primaryImageUrl;
  }
}
```

### 3. Service API

```dart
// services/media_service.dart
class MediaService {
  final ApiService _apiService;

  MediaService(this._apiService);

  Future<List<ProjectMedia>> getProjectMedia(String projectId) async {
    final response = await _apiService.get('/projects/$projectId/media/');
    return (response.data as List)
        .map((json) => ProjectMedia.fromJson(json))
        .toList();
  }

  Future<MediaLimits> getMediaLimits(String projectId) async {
    final response = await _apiService.get('/projects/$projectId/media/limits/');
    return MediaLimits.fromJson(response.data);
  }

  Future<ProjectMedia> uploadMedia({
    required String projectId,
    required File file,
    required String mediaType,
    String? title,
    String? description,
    bool isPrimary = false,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path),
      'media_type': mediaType,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      'is_primary': isPrimary,
    });

    final response = await _apiService.post(
      '/projects/$projectId/media/',
      data: formData,
    );

    return ProjectMedia.fromJson(response.data);
  }

  Future<void> deleteMedia(String projectId, String mediaId) async {
    await _apiService.delete('/projects/$projectId/media/$mediaId/');
  }

  Future<void> setPrimaryMedia(String projectId, String mediaId) async {
    await _apiService.post('/projects/$projectId/media/$mediaId/set-primary/');
  }
}
```

## 🔄 Plan de correction

### Étape 1 : Corriger le backend (PRIORITAIRE)

```python
# apps/projects/serializers/project_serializer.py
# Ajouter la méthode get_media_urls() au ProjectListSerializer
```

### Étape 2 : Mise à jour du frontend

1. **Mettre à jour le modèle Project** pour utiliser `media_urls`
2. **Créer MediaService** pour gérer les endpoints spécialisés
3. **Modifier les widgets** pour afficher plusieurs médias
4. **Implémenter la gestion des limites** avec messages d'upgrade

### Étape 3 : Tests

1. **Vérifier que les projets retournent bien tous leurs médias**
2. **Tester les limites** (1 pour gratuit, 3 pour premium)
3. **Valider l'UX** d'upgrade premium

## 🚨 Actions immédiates requises

1. **Modifier `ProjectListSerializer`** pour inclure `media_urls`
2. **Tester l'endpoint** `/api/v1/projects/` après modification
3. **Mettre à jour le frontend** pour utiliser `media_urls`
4. **Documenter la transition** de `primary_image_url` vers `mediaList`

Sans ces corrections, le frontend continuera à n'afficher qu'un seul média par projet, rendant le système de médias multiples inutile ! 