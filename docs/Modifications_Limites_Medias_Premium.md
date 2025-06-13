# 📱 Modifications Frontend - Limites de Médias Premium

## 📋 Vue d'ensemble

Ce document détaille les modifications frontend nécessaires pour intégrer la nouvelle fonctionnalité de limites de médias basée sur le statut premium des utilisateurs.

## ✅ Fonctionnalités Backend Implémentées

### 🔧 Améliorations Backend Réalisées :

1. **✅ Compression d'images optimisée** - Meilleur rapport qualité/taille
2. **✅ Limites de médias par statut utilisateur** :
   - **Utilisateurs gratuits** : 1 média par projet
   - **Utilisateurs premium** : 3 médias par projet
3. **✅ Nouvelle API endpoint** : `/projects/{id}/media/limits/`
4. **✅ Validation automatique** lors de l'ajout de médias
5. **✅ Messages d'encouragement** pour le passage premium

## 🎯 Modifications Frontend Requises

### 1. **Mise à jour du service API MediaService**

**Fichier :** `lib/services/media_service.dart`

```dart
import 'package:dio/dio.dart';
import '../models/media/media_limits.dart';
import '../models/media/project_media.dart';
import 'api_config.dart';

class MediaService {
  final Dio _dio;

  MediaService(this._dio);

  // 🔴 NOUVELLE MÉTHODE : Récupérer les limites de médias
  Future<MediaLimits> getMediaLimits(String projectId) async {
    try {
      final response = await _dio.get(
        '${ApiConfig.projects}/$projectId/media/limits/',
      );
      return MediaLimits.fromJson(response.data);
    } catch (e) {
      throw _handleError(e);
    }
  }

  // 🔴 MÉTHODE AMÉLIORÉE : Upload avec vérification des limites
  Future<ProjectMedia> uploadMedia({
    required String projectId,
    required File file,
    String? title,
    String? description,
    bool isPrimary = false,
  }) async {
    try {
      // Vérifier les limites avant l'upload
      final limits = await getMediaLimits(projectId);
      
      if (!limits.canAdd) {
        throw MediaLimitException(
          message: limits.upgradeMessage,
          isLimitReached: true,
          isPremium: limits.isPremium,
          currentCount: limits.current,
          maxCount: limits.limit,
        );
      }

      // Procéder à l'upload
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path),
        'title': title ?? 'Nouveau média',
        'description': description ?? '',
        'is_primary': isPrimary,
        'media_type': 'IMAGE',
      });

      final response = await _dio.post(
        '${ApiConfig.projects}/$projectId/media/',
        data: formData,
      );

      return ProjectMedia.fromJson(response.data);
    } catch (e) {
      throw _handleError(e);
    }
  }

  // Autres méthodes existantes...
  
  Exception _handleError(dynamic error) {
    if (error is DioException) {
      if (error.response?.statusCode == 400) {
        final message = error.response?.data['error'] ?? 'Erreur de validation';
        
        // Détecter les erreurs de limite
        if (message.contains('Limite de médias')) {
          return MediaLimitException(
            message: message,
            isLimitReached: true,
          );
        }
      }
    }
    return Exception('Erreur lors de l\'opération: $error');
  }
}

// 🔴 NOUVELLE EXCEPTION : Pour les erreurs de limite
class MediaLimitException implements Exception {
  final String message;
  final bool isLimitReached;
  final bool isPremium;
  final int currentCount;
  final int maxCount;

  MediaLimitException({
    required this.message,
    this.isLimitReached = false,
    this.isPremium = false,
    this.currentCount = 0,
    this.maxCount = 1,
  });

  @override
  String toString() => message;
}
```

### 2. **Nouveau modèle MediaLimits**

**Fichier :** `lib/models/media/media_limits.dart`

```dart
import 'package:json_annotation/json_annotation.dart';

part 'media_limits.g.dart';

@JsonSerializable()
class MediaLimits {
  @JsonKey(name: 'can_add')
  final bool canAdd;
  
  final int limit;
  final int current;
  final int remaining;
  
  @JsonKey(name: 'is_premium')
  final bool isPremium;
  
  @JsonKey(name: 'upgrade_message')
  final String upgradeMessage;

  MediaLimits({
    required this.canAdd,
    required this.limit,
    required this.current,
    required this.remaining,
    required this.isPremium,
    required this.upgradeMessage,
  });

  factory MediaLimits.fromJson(Map<String, dynamic> json) =>
      _$MediaLimitsFromJson(json);

  Map<String, dynamic> toJson() => _$MediaLimitsToJson(this);

  // Getters helper
  bool get isAtLimit => remaining == 0;
  double get progressPercentage => current / limit;
  String get limitText => '$current/$limit médias';
}
```

### 3. **Widget indicateur de limite**

**Fichier :** `lib/widgets/media/media_limit_indicator.dart`

```dart
import 'package:flutter/material.dart';
import '../../models/media/media_limits.dart';

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
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // En-tête avec icône
            Row(
              children: [
                Icon(
                  limits.isPremium ? Icons.workspace_premium : Icons.image,
                  color: limits.isPremium ? Colors.amber : Colors.grey,
                ),
                SizedBox(width: 8),
                Text(
                  limits.isPremium ? 'Compte Premium' : 'Compte Gratuit',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: limits.isPremium ? Colors.amber[700] : Colors.grey[700],
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 12),
            
            // Barre de progression
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: limits.progressPercentage,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      limits.isAtLimit 
                        ? Colors.red
                        : limits.isPremium 
                          ? Colors.amber 
                          : Colors.blue,
                    ),
                  ),
                ),
                SizedBox(width: 12),
                Text(
                  limits.limitText,
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    color: limits.isAtLimit ? Colors.red : null,
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 12),
            
            // Message d'upgrade
            Text(
              limits.upgradeMessage,
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
              ),
            ),
            
            // Bouton d'upgrade pour les comptes gratuits
            if (!limits.isPremium && onUpgradePressed != null) ...[
              SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: onUpgradePressed,
                  icon: Icon(Icons.upgrade),
                  label: Text('Passer au Premium'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

### 4. **Mise à jour du widget d'upload de médias**

**Fichier :** `lib/widgets/media/media_upload_widget.dart`

```dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

import '../../models/media/media_limits.dart';
import '../../services/media_service.dart';
import 'media_limit_indicator.dart';

class MediaUploadWidget extends StatefulWidget {
  final String projectId;
  final VoidCallback? onMediaUploaded;
  final VoidCallback? onUpgradePressed;

  const MediaUploadWidget({
    Key? key,
    required this.projectId,
    this.onMediaUploaded,
    this.onUpgradePressed,
  }) : super(key: key);

  @override
  State<MediaUploadWidget> createState() => _MediaUploadWidgetState();
}

class _MediaUploadWidgetState extends State<MediaUploadWidget> {
  final MediaService _mediaService = MediaService(DioClient.instance);
  
  MediaLimits? _limits;
  bool _isLoading = false;
  bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    _loadLimits();
  }

  Future<void> _loadLimits() async {
    setState(() => _isLoading = true);
    
    try {
      final limits = await _mediaService.getMediaLimits(widget.projectId);
      setState(() {
        _limits = limits;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showError('Erreur lors du chargement des limites: $e');
    }
  }

  Future<void> _pickAndUploadImage() async {
    // Vérifier les limites avant de permettre la sélection
    if (_limits != null && !_limits!.canAdd) {
      _showLimitDialog();
      return;
    }

    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1920,
      maxHeight: 1080,
      imageQuality: 85,
    );

    if (pickedFile != null) {
      await _uploadImage(File(pickedFile.path));
    }
  }

  Future<void> _uploadImage(File file) async {
    setState(() => _isUploading = true);

    try {
      await _mediaService.uploadMedia(
        projectId: widget.projectId,
        file: file,
        title: 'Nouvelle image',
      );

      // Recharger les limites après upload
      await _loadLimits();
      
      widget.onMediaUploaded?.call();
      
      _showSuccess('Image uploadée avec succès !');
      
    } on MediaLimitException catch (e) {
      _showLimitDialog(error: e.message);
    } catch (e) {
      _showError('Erreur lors de l\'upload: $e');
    } finally {
      setState(() => _isUploading = false);
    }
  }

  void _showLimitDialog({String? error}) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.warning, color: Colors.orange),
            SizedBox(width: 8),
            Text('Limite atteinte'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(error ?? _limits?.upgradeMessage ?? 'Limite de médias atteinte'),
            
            if (_limits != null && !_limits!.isPremium) ...[
              SizedBox(height: 16),
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber[200]!),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.workspace_premium, 
                             color: Colors.amber[700], size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Avantages Premium',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.amber[700],
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    Text('• Jusqu\'à 3 médias par projet'),
                    Text('• Images haute qualité'),
                    Text('• Support prioritaire'),
                  ],
                ),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Fermer'),
          ),
          if (_limits != null && !_limits!.isPremium) ...[
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).pop();
                widget.onUpgradePressed?.call();
              },
              icon: Icon(Icons.upgrade),
              label: Text('Passer au Premium'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amber,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ],
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        // Indicateur de limites
        if (_limits != null)
          MediaLimitIndicator(
            limits: _limits!,
            onUpgradePressed: widget.onUpgradePressed,
          ),

        SizedBox(height: 16),

        // Bouton d'upload
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _isUploading 
              ? null 
              : (_limits?.canAdd ?? false) 
                ? _pickAndUploadImage 
                : () => _showLimitDialog(),
            icon: _isUploading 
              ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Icon(Icons.add_photo_alternate),
            label: Text(
              _isUploading 
                ? 'Upload en cours...' 
                : _limits?.canAdd == false
                  ? 'Limite atteinte'
                  : 'Ajouter une image',
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: _limits?.canAdd == false 
                ? Colors.grey 
                : Theme.of(context).primaryColor,
              padding: EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
      ],
    );
  }
}
```

### 5. **Mise à jour de la page de détail du projet**

**Fichier :** `lib/pages/project/project_detail_page.dart`

```dart
// Dans la classe _ProjectDetailPageState

Future<void> _navigateToUpgrade() async {
  // Naviguer vers la page d'upgrade premium
  Navigator.of(context).pushNamed('/premium-upgrade');
}

// Dans le build method, ajouter le widget d'upload
Widget _buildMediaSection() {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        'Médias du projet',
        style: Theme.of(context).textTheme.titleLarge,
      ),
      
      SizedBox(height: 16),
      
      // Widget d'upload avec gestion des limites
      if (_isOwner) // Seulement si l'utilisateur est le propriétaire
        MediaUploadWidget(
          projectId: widget.projectId,
          onMediaUploaded: _refreshProject,
          onUpgradePressed: _navigateToUpgrade,
        ),
      
      SizedBox(height: 16),
      
      // Grille des médias existants
      _buildMediaGrid(),
    ],
  );
}
```

### 6. **Mise à jour des dépendances**

**Fichier :** `pubspec.yaml`

```yaml
dependencies:
  # Existantes...
  
  # Pour l'upload d'images
  image_picker: ^1.0.4
  
  # Pour les requêtes multipart
  dio: ^5.3.2
  
  # Pour la génération JSON
  json_annotation: ^4.8.1

dev_dependencies:
  # Existantes...
  
  # Pour la génération de code
  build_runner: ^2.4.7
  json_serializable: ^6.7.1
```

### 7. **Régénération du code**

Après avoir ajouté les nouveaux modèles, exécutez :

```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

## 🔍 Tests recommandés

### Tests utilisateur gratuit :
1. ✅ Vérifier qu'un seul média peut être ajouté
2. ✅ Affichage du message de limite atteinte
3. ✅ Proposition d'upgrade vers premium
4. ✅ Blocage de l'upload supplémentaire

### Tests utilisateur premium :
1. ✅ Possibilité d'ajouter jusqu'à 3 médias
2. ✅ Affichage de l'indicateur premium
3. ✅ Compression automatique des images
4. ✅ Pas de limitation restrictive

## 🎯 Fonctionnalités backend disponibles

### Endpoints disponibles :
- `GET /api/v1/projects/{id}/media/limits/` - Informations sur les limites
- `POST /api/v1/projects/{id}/media/` - Upload avec validation automatique
- `POST /api/v1/projects/{id}/media/{media_id}/set-primary/` - Définir image principale
- `POST /api/v1/projects/{id}/media/reorder/` - Réorganiser les médias

### Améliorations automatiques :
- **Compression intelligente** des images (qualité optimale, taille réduite)
- **Validation des limites** en temps réel
- **Messages d'encouragement** pour l'upgrade premium
- **Redimensionnement automatique** (max 1920px)
- **Conversion en JPEG** optimisé

## ✅ Checklist d'implémentation

- [ ] Ajouter le modèle `MediaLimits`
- [ ] Mettre à jour `MediaService` avec les nouvelles méthodes
- [ ] Créer le widget `MediaLimitIndicator`
- [ ] Créer le widget `MediaUploadWidget`
- [ ] Mettre à jour la page de détail du projet
- [ ] Ajouter la gestion des erreurs de limite
- [ ] Implémenter la navigation vers l'upgrade premium
- [ ] Tester avec des comptes gratuits et premium
- [ ] Régénérer le code avec `build_runner`

## 🚀 Résultat attendu

Après ces modifications, l'application Flutter devrait :

✅ **Afficher clairement les limites de médias** selon le statut utilisateur  
✅ **Bloquer l'upload** quand la limite est atteinte  
✅ **Encourager l'upgrade premium** avec des messages pertinents  
✅ **Gérer automatiquement la compression** des images  
✅ **Offrir une expérience utilisateur fluide** pour les deux types de comptes  

Le système est conçu pour encourager naturellement l'upgrade vers le premium tout en respectant les utilisateurs gratuits. 