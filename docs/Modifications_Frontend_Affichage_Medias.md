# 🖼️ Modifications Frontend - Affichage des Médias de Projets

## 📋 Vue d'ensemble

Ce document détaille les modifications précises à apporter dans votre frontend Flutter pour afficher correctement les images des projets générées par le backend Django VentureLink.

## ✅ État du Backend

Le backend Django fonctionne parfaitement :
- ✅ 44 médias générés pour 22 projets
- ✅ API retourne `primary_image_url` : `/media/projects/media/[filename].jpg`
- ✅ Configuration Django correcte pour servir les médias
- ✅ URLs d'exemple : `/media/projects/media/0ec995c1af3444618581294bddb91b49_1749619478.jpg`

## 🎯 Modifications Requises

### 1. **Vérifier le modèle ProjectModel**

**Fichier :** `lib/models/project/project_model.dart`

```dart
@JsonSerializable()
class ProjectModel {
  final String id;
  final String title;
  @JsonKey(name: 'short_description')
  final String shortDescription;
  final ProjectCategory category;
  final String stage;
  final String status;
  @JsonKey(name: 'funding_min')
  final double? fundingMin;
  @JsonKey(name: 'funding_max')
  final double? fundingMax;
  @JsonKey(name: 'funding_currency')
  final String fundingCurrency;
  @JsonKey(name: 'location_country')
  final String? locationCountry;
  @JsonKey(name: 'location_city')
  final String? locationCity;
  @JsonKey(name: 'is_premium')
  final bool isPremium;
  @JsonKey(name: 'is_featured')
  final bool isFeatured;
  @JsonKey(name: 'views_count')
  final int viewsCount;
  @JsonKey(name: 'interests_count')
  final int interestsCount;
  @JsonKey(name: 'favorites_count')
  final int favoritesCount;
  final UserModel creator;
  
  // 🔴 MODIFICATION CRITIQUE : Utiliser primary_image_url
  @JsonKey(name: 'primary_image_url')  // ← Champ correct de l'API
  final String? primaryImageUrl;
  
  // ❌ PAS primary_image, mais primary_image_url
  
  final List<ProjectTag> tags;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'published_at')
  final DateTime? publishedAt;

  ProjectModel({
    required this.id,
    required this.title,
    required this.shortDescription,
    required this.category,
    required this.stage,
    required this.status,
    this.fundingMin,
    this.fundingMax,
    required this.fundingCurrency,
    this.locationCountry,
    this.locationCity,
    required this.isPremium,
    required this.isFeatured,
    required this.viewsCount,
    required this.interestsCount,
    required this.favoritesCount,
    required this.creator,
    this.primaryImageUrl,  // ← Ajouter ce paramètre
    required this.tags,
    required this.createdAt,
    this.publishedAt,
  });

  factory ProjectModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectModelFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectModelToJson(this);
}
```

### 2. **Créer une méthode pour l'URL complète**

**Ajout dans la classe `ProjectModel` :**

```dart
// Dans la classe ProjectModel
String? get fullImageUrl {
  if (primaryImageUrl != null && primaryImageUrl!.isNotEmpty) {
    // Si l'URL est déjà absolue, la retourner telle quelle
    if (primaryImageUrl!.startsWith('http')) {
      return primaryImageUrl;
    }
    // Sinon, construire l'URL absolue
    return '${ApiConfig.baseUrl}$primaryImageUrl';
    // Résultat : http://127.0.0.1:8000/media/projects/media/image.jpg
  }
  return null;
}

// Méthode helper pour vérifier si l'image existe
bool get hasImage => primaryImageUrl != null && primaryImageUrl!.isNotEmpty;
```

### 3. **Vérifier ApiConfig.baseUrl**

**Fichier :** `lib/services/api_config.dart`

```dart
class ApiConfig {
  // 🔴 MODIFICATION : Adapter selon votre environnement
  static const String baseUrl = kIsWeb 
    ? 'http://127.0.0.1:8000'      // Web
    : Platform.isAndroid 
      ? 'http://10.0.2.2:8000'     // Émulateur Android
      : 'http://127.0.0.1:8000';   // iOS/Device physique
  
  static const String projects = '/api/v1/projects';
  static const String categories = '/api/v1/categories';
  static const String tags = '/api/v1/tags';
  
  // Autres endpoints...
}
```

### 4. **Modifier l'affichage des images - ProjectCard**

**Fichier :** `lib/widgets/project/project_card.dart`

```dart
class ProjectCard extends StatelessWidget {
  final ProjectModel project;
  final VoidCallback? onTap;

  const ProjectCard({
    Key? key,
    required this.project,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 🔴 MODIFICATION : Image avec gestion d'erreurs
            Container(
              height: 200,
              width: double.infinity,
              child: ClipRRect(
                borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
                child: project.hasImage
                    ? CachedNetworkImage(
                        imageUrl: project.fullImageUrl!,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          color: Colors.grey[300],
                          child: Center(
                            child: CircularProgressIndicator(
                              color: Theme.of(context).primaryColor,
                            ),
                          ),
                        ),
                        errorWidget: (context, url, error) {
                          // 🔴 LOG DE DEBUG
                          print('❌ Erreur chargement image: $url');
                          print('   Erreur: $error');
                          print('   Projet: ${project.title}');
                          
                          return Container(
                            color: Colors.grey[300],
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.broken_image,
                                  size: 50,
                                  color: Colors.grey[600],
                                ),
                                SizedBox(height: 8),
                                Text(
                                  'Image non disponible',
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      )
                    : Container(
                        color: Colors.grey[300],
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.image,
                              size: 50,
                              color: Colors.grey[600],
                            ),
                            SizedBox(height: 8),
                            Text(
                              'Aucune image',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
              ),
            ),
            
            // Contenu de la carte
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Titre
                  Text(
                    project.title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  
                  SizedBox(height: 8),
                  
                  // Description
                  Text(
                    project.shortDescription,
                    style: Theme.of(context).textTheme.bodyMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  
                  SizedBox(height: 12),
                  
                  // Statistiques
                  Row(
                    children: [
                      Icon(Icons.visibility, size: 16, color: Colors.grey),
                      SizedBox(width: 4),
                      Text('${project.viewsCount}'),
                      SizedBox(width: 16),
                      Icon(Icons.favorite, size: 16, color: Colors.grey),
                      SizedBox(width: 4),
                      Text('${project.favoritesCount}'),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 5. **Ajouter des logs de debug**

**Fichier :** `lib/services/project_service.dart`

```dart
class ProjectService {
  final Dio _dio;

  ProjectService(this._dio);

  Future<PaginatedResponse<ProjectModel>> getProjects({
    int page = 1,
    int pageSize = 20,
    // ... autres paramètres
  }) async {
    try {
      final response = await _dio.get(
        '${ApiConfig.projects}/',
        queryParameters: queryParameters,
      );

      final paginatedResponse = PaginatedResponse<ProjectModel>.fromJson(
        response.data,
        (json) => ProjectModel.fromJson(json as Map<String, dynamic>),
      );

      // 🔴 AJOUT : Debug des images
      _debugProjectImages(paginatedResponse.results);

      return paginatedResponse;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // 🔴 NOUVELLE MÉTHODE : Debug des images
  void _debugProjectImages(List<ProjectModel> projects) {
    print('🖼️ Debug des images de projets:');
    print('   Nombre de projets: ${projects.length}');
    print('   Base URL: ${ApiConfig.baseUrl}');
    print('');
    
    for (var project in projects) {
      print('📁 Projet: ${project.title}');
      print('   primaryImageUrl brut: ${project.primaryImageUrl}');
      print('   fullImageUrl construit: ${project.fullImageUrl}');
      print('   hasImage: ${project.hasImage}');
      print('---');
    }
  }
}
```

### 6. **Vérifier les permissions réseau**

**Fichier :** `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- 🔴 AJOUT : Permissions réseau -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:label="venture_link"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="true">  <!-- 🔴 AJOUT : Pour le développement local -->
        
        <!-- ... reste de la configuration -->
    </application>
</manifest>
```

### 7. **Widget de test pour debug**

**Fichier :** `lib/widgets/debug/test_image_widget.dart`

```dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

class TestImageWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // 🔴 URL de test basée sur les images générées
    const testUrls = [
      'http://127.0.0.1:8000/media/projects/media/0ec995c1af3444618581294bddb91b49_1749619478.jpg',
      'http://127.0.0.1:8000/media/projects/media/fd697a19a5ce4fdd9fcaad0bb50c1b4b_1749619458.jpg',
      'http://127.0.0.1:8000/media/projects/media/639e3fffec15461c857e73c5bba1d5ec_1749619458.jpg',
    ];
    
    return Scaffold(
      appBar: AppBar(title: Text('Test Images Projets')),
      body: ListView.builder(
        itemCount: testUrls.length,
        itemBuilder: (context, index) {
          final url = testUrls[index];
          return Card(
            margin: EdgeInsets.all(16),
            child: Column(
              children: [
                Text('Image ${index + 1}'),
                SizedBox(height: 8),
                Container(
                  height: 200,
                  width: double.infinity,
                  child: CachedNetworkImage(
                    imageUrl: url,
                    fit: BoxFit.cover,
                    placeholder: (context, url) => Container(
                      color: Colors.grey[300],
                      child: Center(child: CircularProgressIndicator()),
                    ),
                    errorWidget: (context, url, error) {
                      print('❌ Test Image Error: $url - $error');
                      return Container(
                        color: Colors.red[100],
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.error, color: Colors.red),
                              SizedBox(height: 8),
                              Text('Erreur: $error', textAlign: TextAlign.center),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                SizedBox(height: 8),
                Text(url, style: TextStyle(fontSize: 12)),
              ],
            ),
          );
        },
      ),
    );
  }
}
```

### 8. **Mise à jour des dépendances**

**Fichier :** `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # Image handling
  cached_network_image: ^3.3.0
  
  # Network
  dio: ^5.4.0
  
  # JSON
  json_annotation: ^4.8.1
  
  # ... autres dépendances

dev_dependencies:
  # JSON generation
  json_serializable: ^6.7.1
  build_runner: ^2.4.7
  
  # ... autres dev_dependencies
```

### 9. **Régénérer les modèles JSON**

Après avoir modifié le modèle, exécutez :

```bash
flutter packages pub run build_runner build --delete-conflicting-outputs
```

## 🔍 Étapes de diagnostic

### 1. **Vérification des logs**
- Activez les logs de debug dans `ProjectService`
- Vérifiez que `primaryImageUrl` est bien récupéré de l'API
- Contrôlez que `fullImageUrl` est correctement construite

### 2. **Test d'une URL spécifique**
- Utilisez le `TestImageWidget` avec une URL connue
- Testez l'accès direct dans un navigateur : `http://127.0.0.1:8000/media/projects/media/[filename].jpg`

### 3. **Vérification de la connectivité**
- Testez l'API directement avec un client REST
- Vérifiez que le backend Django est accessible depuis le device/émulateur

### 4. **Outils de développement Flutter**
- Utilisez Flutter Inspector pour inspecter les requêtes réseau
- Vérifiez les erreurs dans la console

## 🎯 URLs finales attendues

Vos URLs finales doivent ressembler à :
```
http://127.0.0.1:8000/media/projects/media/0ec995c1af3444618581294bddb91b49_1749619478.jpg
http://127.0.0.1:8000/media/projects/media/fd697a19a5ce4fdd9fcaad0bb50c1b4b_1749619458.jpg
http://127.0.0.1:8000/media/projects/media/639e3fffec15461c857e73c5bba1d5ec_1749619458.jpg
```

## ✅ Checklist de vérification

- [ ] `ProjectModel` utilise `@JsonKey(name: 'primary_image_url')`
- [ ] Méthode `fullImageUrl` ajoutée au modèle
- [ ] `ApiConfig.baseUrl` configuré correctement
- [ ] Permissions réseau ajoutées dans `AndroidManifest.xml`
- [ ] `usesCleartextTraffic="true"` activé pour le développement
- [ ] Logs de debug activés
- [ ] Modèles JSON régénérés avec `build_runner`
- [ ] `CachedNetworkImage` avec gestion d'erreurs appropriée

## 🚀 Résultat attendu

Après ces modifications, les projets devraient afficher leurs images correctement dans l'application Flutter, avec :
- Affichage des images générées par le backend
- Placeholder pendant le chargement
- Gestion des erreurs avec icônes appropriées
- Logs de debug pour faciliter le troubleshooting

Le backend VentureLink fonctionne parfaitement. Ces modifications Flutter devraient résoudre complètement le problème d'affichage des images. 