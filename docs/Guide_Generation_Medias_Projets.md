# Guide de Génération de Médias pour les Projets VentureLink

## Vue d'ensemble

Ce guide décrit le système complet de génération et gestion des médias pour les projets dans l'application VentureLink. Le système permet de :

- Générer automatiquement des images pour les projets existants
- Télécharger des images depuis des sources externes (Unsplash)
- Créer des placeholders personnalisés basés sur les catégories
- Gérer les médias via une API REST complète

## Architecture

### Composants principaux

1. **ProjectMediaService** : Service principal pour la gestion des médias
2. **Commande Django** : `generate_project_media` pour les opérations en lot
3. **API REST** : Endpoints pour la gestion via l'interface web
4. **Modèles** : `ProjectMedia` pour le stockage des métadonnées

### Structure des fichiers

```
apps/projects/
├── models/
│   └── project_media.py              # Modèle des médias
├── services/
│   └── project_media_service.py      # Service de gestion
├── views/
│   └── project_media_views.py        # Vues API
├── management/
│   └── commands/
│       └── generate_project_media.py # Commande Django
└── serializers/
    └── project_media_serializer.py   # Sérialiseurs API
```

## Types de génération disponibles

### 1. Images générées (`generated`)
- **Description** : Images personnalisées avec formes géométriques et texte
- **Caractéristiques** :
  - Couleurs basées sur la catégorie du projet
  - Titre et catégorie affichés
  - Formes décoratives (cercles, rectangles, losanges)
  - Résolution : 1200x800 pixels
  - Format : JPEG optimisé

### 2. Images Unsplash (`unsplash`)
- **Description** : Images téléchargées depuis Unsplash
- **Caractéristiques** :
  - Mots-clés basés sur la catégorie
  - Images haute qualité
  - Fallback automatique vers `generated` en cas d'échec
  - Résolution : 1200x800 pixels

### 3. Placeholders simples (`placeholder`)
- **Description** : Images minimalistes avec texte simple
- **Caractéristiques** :
  - Couleur de fond basée sur le hash du titre
  - Texte centré
  - Résolution : 800x600 pixels
  - Idéal pour les tests et prototypes

## Utilisation via la commande Django

### Syntaxe de base

```bash
python manage.py generate_project_media [options]
```

### Options disponibles

| Option | Type | Description | Défaut |
|--------|------|-------------|---------|
| `--project-id` | UUID | ID du projet spécifique à traiter | Tous |
| `--source` | String | Source des images (generated/unsplash/placeholder) | generated |
| `--count` | Integer | Nombre d'images par projet | 1 |
| `--overwrite` | Boolean | Remplacer les médias existants | False |

### Exemples d'utilisation

#### Générer une image pour un projet spécifique
```bash
python manage.py generate_project_media \
  --project-id 90d28f49-2b56-48af-92f8-90b01c9590a8 \
  --source generated \
  --count 1
```

#### Générer des médias pour tous les projets
```bash
python manage.py generate_project_media \
  --source generated \
  --count 2
```

#### Utiliser Unsplash avec fallback
```bash
python manage.py generate_project_media \
  --source unsplash \
  --count 1 \
  --overwrite
```

#### Créer des placeholders pour les tests
```bash
python manage.py generate_project_media \
  --source placeholder \
  --count 1
```

## Utilisation via l'API REST

### Endpoints disponibles

#### 1. Génération de médias
```http
POST /api/v1/projects/{project_id}/media/generate/
```

**Body :**
```json
{
  "source": "generated",
  "count": 2,
  "overwrite": true
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "2 média(s) généré(s) avec succès",
  "stats": {
    "created": 2
  },
  "media": [
    {
      "id": "uuid",
      "title": "Image générée 1 - Titre du projet",
      "file": "/media/projects/media/filename.jpg",
      "is_primary": true,
      "media_type": "IMAGE"
    }
  ]
}
```

#### 2. Lister les médias
```http
GET /api/v1/projects/{project_id}/media/
```

#### 3. Définir comme principal
```http
POST /api/v1/projects/{project_id}/media/{media_id}/set-primary/
```

#### 4. Réorganiser les médias
```http
POST /api/v1/projects/{project_id}/media/reorder/
```

**Body :**
```json
{
  "media_order": [
    {"id": "uuid1", "order": 1},
    {"id": "uuid2", "order": 2}
  ]
}
```

### Authentification

Toutes les opérations de modification nécessitent :
- Authentification JWT valide
- Être le créateur du projet

## Configuration des couleurs par catégorie

Le système utilise des palettes de couleurs spécifiques pour chaque catégorie :

| Catégorie | Couleur principale | Couleur secondaire | Background |
|-----------|-------------------|-------------------|------------|
| Agriculture | #228B22 (Vert forêt) | #32CD32 (Vert lime) | #8FBC8F |
| Technologie | #191970 (Bleu nuit) | #87CEEB (Bleu ciel) | #4682B4 |
| Santé | #8B0000 (Rouge foncé) | #FFB6C1 (Rose clair) | #DC143C |
| Éducation | #B8860B (Or foncé) | #FFFFE0 (Jaune clair) | #DAA520 |
| Commerce | #4B0082 (Indigo) | #DDA0DD (Prune) | #9370DB |
| Énergie | #FF4500 (Orange rouge) | #FFE4E1 (Rose pâle) | #FF8C00 |
| Transport | #708090 (Gris ardoise) | #F0F8FF (Bleu alice) | #2F4F4F |
| Tourisme | #008B8B (Sarcelle foncé) | #F0FFFF (Azur) | #20B2AA |
| FinTech | #556B2F (Olive foncé) | #F5FFFA (Menthe) | #6B8E23 |

## Mots-clés Unsplash par catégorie

| Catégorie | Mots-clés |
|-----------|-----------|
| Agriculture | agriculture,farming,crops |
| Technologie | technology,innovation,startup |
| Santé | healthcare,medical,health |
| Éducation | education,learning,knowledge |
| Commerce | business,commerce,trade |
| Énergie | energy,renewable,power |
| Transport | transportation,logistics,mobility |
| Tourisme | tourism,travel,destination |
| FinTech | fintech,finance,banking |

## Gestion des erreurs

### Erreurs communes

1. **Projet non trouvé**
   ```json
   {"error": "Projet non trouvé", "status": 404}
   ```

2. **Permission refusée**
   ```json
   {"error": "Vous n'êtes pas autorisé à modifier ce projet", "status": 403}
   ```

3. **Médias existants**
   ```json
   {
     "error": "Le projet a déjà des médias. Utilisez overwrite=true",
     "existing_media_count": 2,
     "status": 400
   }
   ```

4. **Erreur Unsplash**
   - Fallback automatique vers generation locale
   - Log de l'erreur pour monitoring

### Logs et monitoring

Le système log automatiquement :
- Erreurs de téléchargement Unsplash
- Erreurs de génération d'images
- Statistiques de génération

## Performance et optimisation

### Optimisations appliquées

1. **Compression JPEG** : Qualité 85% avec optimisation
2. **Redimensionnement automatique** : Max 1920x1080 pour Unsplash
3. **Format standardisé** : Conversion automatique en JPEG
4. **Cache des couleurs** : Palettes précalculées
5. **Transactions atomiques** : Cohérence des données

### Recommandations

- **Production** : Utiliser un CDN pour les médias
- **Stockage** : Configurer un stockage externe (AWS S3, Google Cloud)
- **Monitoring** : Surveiller l'espace disque utilisé
- **Backup** : Inclure le dossier media dans les sauvegardes

## Maintenance

### Scripts utiles

#### Vérifier les médias existants
```bash
python check_project_media.py
```

#### Nettoyer les fichiers orphelins
```python
# À implémenter si nécessaire
from apps.projects.services.project_media_service import ProjectMediaService
ProjectMediaService.cleanup_orphaned_files()
```

### Statistiques

Pour obtenir des statistiques complètes :

```python
from apps.projects.models import Project, ProjectMedia

stats = {
    'total_projects': Project.objects.count(),
    'projects_with_media': Project.objects.filter(media__isnull=False).distinct().count(),
    'total_media': ProjectMedia.objects.count(),
    'primary_images': ProjectMedia.objects.filter(is_primary=True).count(),
}
```

## Extension du système

### Ajouter de nouvelles sources

1. Étendre `ProjectMediaService._generate_media_for_project()`
2. Ajouter les mots-clés dans `_get_category_keywords()`
3. Mettre à jour la documentation API

### Nouveaux types de médias

1. Étendre `ProjectMedia.MEDIA_TYPE_CHOICES`
2. Adapter les méthodes de génération
3. Mettre à jour les permissions

### Support multi-devises

Le système est déjà préparé pour l'internationalisation :
- Textes traduits dans les images générées
- Support des catégories multilingues
- API localisée

## Dépannage

### Problèmes fréquents

1. **Pillow non installé**
   ```bash
   pip install Pillow==10.0.1
   ```

2. **Permissions de fichiers**
   ```bash
   chmod 755 media/
   chmod 644 media/projects/media/*
   ```

3. **Espace disque insuffisant**
   - Vérifier l'espace disponible
   - Implémenter une rotation des anciens médias

4. **Erreurs de timeout Unsplash**
   - Le système utilise un fallback automatique
   - Vérifier la connectivité réseau

## Sécurité

### Mesures de protection

1. **Validation des fichiers** : Vérification du type MIME
2. **Limitation de taille** : Max 1920x1080 pixels
3. **Authentification** : JWT requis pour modifications
4. **Permissions** : Seul le créateur peut modifier
5. **Rate limiting** : Limite de 5 médias par génération

### Recommandations

- Implémenter un antivirus pour les uploads
- Configurer des quotas de stockage par utilisateur
- Logger toutes les opérations de modification
- Mettre en place des alertes de sécurité

---

Ce système de génération de médias permet d'enrichir automatiquement tous les projets existants avec des visuels attractifs et cohérents, améliorant ainsi l'expérience utilisateur de la plateforme VentureLink. 