# Guide d'Implémentation Frontend - Système de Médias Premium VentureLink

## Vue d'ensemble

Ce document détaille l'implémentation frontend pour gérer les médias multiples des projets avec le système de limites premium :
- **Utilisateurs gratuits** : 1 média par projet
- **Utilisateurs premium** : 3 médias par projet

## 📡 Endpoints API Disponibles

### 1. Récupération des projets avec leurs médias

```http
GET /api/v1/projects/
GET /api/v1/projects/{id}/
```

⚠️ **PROBLÈME IDENTIFIÉ** : Le `ProjectListSerializer` actuel ne retourne que `primary_image_url` au lieu de tous les médias.

#### Solution recommandée : Modifier le backend
Ajouter une propriété `media_urls` au `ProjectListSerializer` :

```python
# Backend - apps/projects/serializers/project_serializer.py
class ProjectListSerializer(serializers.ModelSerializer):
    # ... autres champs ...
    media_urls = serializers.SerializerMethodField()
    
    def get_media_urls(self, obj):
        """Retourne tous les URLs des médias du projet."""
        return [
            {
                'id': str(media.id),
                'url': media.file.url if media.file else None,
                'type': media.media_type,
                'is_primary': media.is_primary,
                'order': media.order
            }
            for media in obj.media.order_by('order', '-created_at')
        ]
```

### 2. Gestion des médias d'un projet

```http
# Lister tous les médias d'un projet
GET /api/v1/projects/{project_id}/media/

# Créer un nouveau média
POST /api/v1/projects/{project_id}/media/
Content-Type: multipart/form-data
{
  "file": (fichier),
  "media_type": "image", // ou "video", "document"
  "title": "Titre optionnel",
  "description": "Description optionnelle",
  "is_primary": false,
  "order": 1
}

# Récupérer un média spécifique
GET /api/v1/projects/{project_id}/media/{media_id}/

# Modifier un média
PUT /api/v1/projects/{project_id}/media/{media_id}/
PATCH /api/v1/projects/{project_id}/media/{media_id}/

# Supprimer un média
DELETE /api/v1/projects/{project_id}/media/{media_id}/
```

### 3. Actions spéciales sur les médias

```http
# Définir comme image principale
POST /api/v1/projects/{project_id}/media/{media_id}/set-primary/

# Réorganiser l'ordre des médias
POST /api/v1/projects/{project_id}/media/reorder/
{
  "media_order": [
    {"id": "uuid1", "order": 1},
    {"id": "uuid2", "order": 2}
  ]
}

# Générer des médias automatiquement
POST /api/v1/projects/{project_id}/media/generate/
{
  "source": "unsplash", // "generated", "unsplash", "placeholder"
  "count": 2,
  "overwrite": false
}
```

### 4. 🎯 Vérification des limites de médias

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

### 1. Modèle de données

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
  final DateTime createdAt;

  ProjectMedia({
    required this.id,
    required this.url,
    required this.type,
    this.title,
    this.description,
    required this.isPrimary,
    required this.order,
    required this.createdAt,
  });

  factory ProjectMedia.fromJson(Map<String, dynamic> json) {
    return ProjectMedia(
      id: json['id'],
      url: json['file_url'] ?? '',
      type: json['media_type'] ?? 'image',
      title: json['title'],
      description: json['description'],
      isPrimary: json['is_primary'] ?? false,
      order: json['order'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
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
  // ... autres propriétés ...
  final List<ProjectMedia> mediaList; // 🔥 NOUVEAU : remplace/complète primaryImageUrl
  final String? primaryImageUrl; // Gardé pour compatibilité
  
  Project({
    // ... autres paramètres ...
    this.mediaList = const [],
    this.primaryImageUrl,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      // ... autres mappings ...
      mediaList: (json['media_urls'] as List<dynamic>?)
          ?.map((media) => ProjectMedia.fromJson(media))
          .toList() ?? [],
      primaryImageUrl: json['primary_image_url'],
    );
  }

  // Utilitaires pour la compatibilité
  ProjectMedia? get primaryMedia {
    return mediaList.where((media) => media.isPrimary).firstOrNull ??
           mediaList.firstOrNull;
  }

  List<ProjectMedia> get imageMedias {
    return mediaList.where((media) => media.type == 'image').toList();
  }
}
```

### 3. Service API étendu

```dart
// services/media_service.dart
class MediaService {
  final ApiService _apiService;

  MediaService(this._apiService);

  // Récupérer tous les médias d'un projet
  Future<List<ProjectMedia>> getProjectMedia(String projectId) async {
    final response = await _apiService.get('/projects/$projectId/media/');
    return (response.data as List)
        .map((json) => ProjectMedia.fromJson(json))
        .toList();
  }

  // Ajouter un média
  Future<ProjectMedia> uploadMedia({
    required String projectId,
    required File file,
    required String mediaType,
    String? title,
    String? description,
    bool isPrimary = false,
    int order = 0,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(file.path),
      'media_type': mediaType,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      'is_primary': isPrimary,
      'order': order,
    });

    final response = await _apiService.post(
      '/projects/$projectId/media/',
      data: formData,
    );

    return ProjectMedia.fromJson(response.data);
  }

  // Vérifier les limites
  Future<MediaLimits> getMediaLimits(String projectId) async {
    final response = await _apiService.get('/projects/$projectId/media/limits/');
    return MediaLimits.fromJson(response.data);
  }

  // Définir comme image principale
  Future<void> setPrimaryMedia(String projectId, String mediaId) async {
    await _apiService.post('/projects/$projectId/media/$mediaId/set-primary/');
  }

  // Réorganiser les médias
  Future<List<ProjectMedia>> reorderMedia(
    String projectId,
    List<Map<String, dynamic>> mediaOrder,
  ) async {
    final response = await _apiService.post(
      '/projects/$projectId/media/reorder/',
      data: {'media_order': mediaOrder},
    );

    return (response.data['media'] as List)
        .map((json) => ProjectMedia.fromJson(json))
        .toList();
  }

  // Supprimer un média
  Future<void> deleteMedia(String projectId, String mediaId) async {
    await _apiService.delete('/projects/$projectId/media/$mediaId/');
  }
}
```

### 4. Exception personnalisée

```dart
// exceptions/media_exceptions.dart
class MediaLimitException implements Exception {
  final String message;
  final MediaLimits limits;

  MediaLimitException(this.message, this.limits);

  @override
  String toString() => 'MediaLimitException: $message';
}
```

### 5. Widget indicateur de limites

```dart
// widgets/media_limit_indicator.dart
class MediaLimitIndicator extends StatelessWidget {
  final MediaLimits limits;
  final VoidCallback? onUpgradePressed;

  const MediaLimitIndicator({
    Key? key,
    required this.limits,
    this.onUpgradePressed,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: limits.isPremium ? Colors.amber.shade50 : Colors.blue.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: limits.isPremium ? Colors.amber : Colors.blue,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Icon(
            limits.isPremium ? Icons.star : Icons.info,
            color: limits.isPremium ? Colors.amber : Colors.blue,
            size: 20,
          ),
          SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${limits.current}/${limits.limit} médias utilisés',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: limits.isPremium ? Colors.amber.shade700 : Colors.blue.shade700,
                  ),
                ),
                if (limits.remaining > 0)
                  Text(
                    '${limits.remaining} média(s) restant(s)',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                if (!limits.canAdd)
                  Text(
                    'Limite atteinte',
                    style: TextStyle(fontSize: 12, color: Colors.red),
                  ),
              ],
            ),
          ),
          if (!limits.isPremium && onUpgradePressed != null)
            TextButton(
              onPressed: onUpgradePressed,
              child: Text('Passer Premium'),
            ),
        ],
      ),
    );
  }
}
```

### 6. Widget d'upload avec gestion des limites

```dart
// widgets/media_upload_widget.dart
class MediaUploadWidget extends StatefulWidget {
  final String projectId;
  final List<ProjectMedia> currentMedia;
  final Function(List<ProjectMedia>) onMediaUpdated;

  const MediaUploadWidget({
    Key? key,
    required this.projectId,
    required this.currentMedia,
    required this.onMediaUpdated,
  }) : super(key: key);

  @override
  _MediaUploadWidgetState createState() => _MediaUploadWidgetState();
}

class _MediaUploadWidgetState extends State<MediaUploadWidget> {
  final MediaService _mediaService = GetIt.instance<MediaService>();
  MediaLimits? _limits;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadLimits();
  }

  Future<void> _loadLimits() async {
    try {
      final limits = await _mediaService.getMediaLimits(widget.projectId);
      setState(() => _limits = limits);
    } catch (e) {
      // Gérer l'erreur
    }
  }

  Future<void> _pickAndUploadImage() async {
    if (_limits?.canAdd != true) {
      _showUpgradeDialog();
      return;
    }

    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    
    if (pickedFile != null) {
      setState(() => _isLoading = true);
      
      try {
        final newMedia = await _mediaService.uploadMedia(
          projectId: widget.projectId,
          file: File(pickedFile.path),
          mediaType: 'image',
          isPrimary: widget.currentMedia.isEmpty, // Premier média = principal
        );

        final updatedMedia = [...widget.currentMedia, newMedia];
        widget.onMediaUpdated(updatedMedia);
        await _loadLimits(); // Recharger les limites
        
      } catch (e) {
        if (e is DioError && e.response?.status == 400) {
          _showUpgradeDialog();
        } else {
          // Afficher erreur générale
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erreur lors de l\'upload: ${e.toString()}')),
          );
        }
      } finally {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showUpgradeDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Limite atteinte'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_limits?.upgradeMessage ?? 'Limite de médias atteinte'),
            SizedBox(height: 16),
            if (!(_limits?.isPremium ?? false))
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  // Naviguer vers la page d'upgrade premium
                  Navigator.pushNamed(context, '/premium-upgrade');
                },
                child: Text('Passer au Premium'),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Fermer'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (_limits != null)
          MediaLimitIndicator(
            limits: _limits!,
            onUpgradePressed: () => Navigator.pushNamed(context, '/premium-upgrade'),
          ),
        SizedBox(height: 16),
        
        // Grille des médias existants
        if (widget.currentMedia.isNotEmpty)
          GridView.builder(
            shrinkWrap: true,
            physics: NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
            ),
            itemCount: widget.currentMedia.length,
            itemBuilder: (context, index) {
              final media = widget.currentMedia[index];
              return Stack(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      media.url,
                      fit: BoxFit.cover,
                      width: double.infinity,
                      height: double.infinity,
                    ),
                  ),
                  if (media.isPrimary)
                    Positioned(
                      top: 4,
                      left: 4,
                      child: Container(
                        padding: EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.amber,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Icon(Icons.star, size: 12, color: Colors.white),
                      ),
                    ),
                  Positioned(
                    top: 4,
                    right: 4,
                    child: GestureDetector(
                      onTap: () => _deleteMedia(media),
                      child: Container(
                        padding: EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.red,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Icon(Icons.close, size: 12, color: Colors.white),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        
        SizedBox(height: 16),
        
        // Bouton d'ajout
        if (_isLoading)
          CircularProgressIndicator()
        else
          ElevatedButton.icon(
            onPressed: _limits?.canAdd == true ? _pickAndUploadImage : null,
            icon: Icon(Icons.add_photo_alternate),
            label: Text('Ajouter une image'),
          ),
      ],
    );
  }

  Future<void> _deleteMedia(ProjectMedia media) async {
    try {
      await _mediaService.deleteMedia(widget.projectId, media.id);
      final updatedMedia = widget.currentMedia.where((m) => m.id != media.id).toList();
      widget.onMediaUpdated(updatedMedia);
      await _loadLimits();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur lors de la suppression')),
      );
    }
  }
}
```

## 🚀 Checklist d'implémentation

### Backend (À faire en priorité)
- [ ] ✅ Modifier `ProjectListSerializer` pour inclure `media_urls`
- [ ] ✅ Vérifier que les endpoints de médias sont bien exposés  
- [ ] ✅ Tester les limites de médias avec les endpoints

### Frontend
- [ ] 📱 Créer les modèles `ProjectMedia` et `MediaLimits`
- [ ] 📱 Mettre à jour le modèle `Project` avec `mediaList`
- [ ] 📱 Implémenter `MediaService` étendu
- [ ] 📱 Créer `MediaLimitIndicator` widget
- [ ] 📱 Créer `MediaUploadWidget` avec gestion des limites
- [ ] 📱 Mettre à jour les pages de création/édition de projet
- [ ] 📱 Mettre à jour les pages de listing des projets pour afficher plusieurs médias
- [ ] 📱 Implémenter la navigation vers la page d'upgrade premium
- [ ] 📱 Ajouter la gestion d'erreurs spécifique aux limites de médias

### Tests
- [ ] 🧪 Tester l'upload avec limite atteinte
- [ ] 🧪 Tester l'affichage de plusieurs médias
- [ ] 🧪 Tester le passage d'utilisateur gratuit à premium

## 💡 Notes importantes

1. **Compatibilité** : Le champ `primaryImageUrl` est maintenu pour la compatibilité lors de la transition
2. **Performance** : Les médias sont chargés de manière optimisée avec les projets
3. **UX** : Les messages d'upgrade sont contextuels et encouragent la conversion premium
4. **Sécurité** : Tous les uploads passent par la validation des limites côté backend

## 🔄 Migration suggérée

1. **Phase 1** : Modifier le backend (`ProjectListSerializer`)
2. **Phase 2** : Mettre à jour les modèles Flutter
3. **Phase 3** : Implémenter les nouveaux widgets
4. **Phase 4** : Mettre à jour les pages existantes
5. **Phase 5** : Tests et déploiement 