# Guide Frontend : Récupération et Affichage des Médias de Publications

## Vue d'ensemble

Ce guide détaille comment le frontend doit récupérer et afficher les médias associés aux publications de l'application content de VentureLink.

## Structure des Médias

### Modèle PublicationMedia

Chaque publication peut avoir jusqu'à **3 médias** avec les propriétés suivantes :

```typescript
interface PublicationMedia {
  id: string;
  file: string;           // URL du fichier média
  media_type: 'IMAGE' | 'VIDEO' | 'DOCUMENT' | 'AUDIO';
  title?: string;         // Titre optionnel du média
  description?: string;   // Description optionnelle du média
  alt_text?: string;      // Texte alternatif pour accessibilité
  order: number;          // Ordre d'affichage (0, 1, 2)
  is_featured: boolean;   // True si c'est l'image de couverture
  file_size: number;      // Taille du fichier en octets
  created_at: string;     // Date de création
}
```

## Endpoints API

### 1. Récupération des Publications avec Médias

#### Liste des Publications (résumé)
```http
GET /api/content/publications/
```

**Réponse :**
```typescript
interface PublicationList {
  id: string;
  title: string;
  summary?: string;
  publication_type: string;
  domain: string;
  author: UserSimple;
  status: string;
  published_at: string;
  views_count: number;
  likes_count: number;
  comments_count: number;
  is_featured: boolean;
  is_pinned: boolean;
  is_sponsored: boolean;
  sponsor_name?: string;
  featured_media?: PublicationMedia; // ⚠️ SEULE l'image de couverture
  tags_list: string[];
  user_has_liked: boolean;
  slug: string;
}
```

#### Détail d'une Publication (complet)
```http
GET /api/content/publications/{id}/
```

**Réponse :**
```typescript
interface PublicationDetail {
  // ... tous les champs de base
  media: PublicationMedia[];  // ⚠️ TOUS les médias de la publication
  likes: PublicationLike[];
  user_has_liked: boolean;
  can_be_commented: boolean;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}
```

### 2. Récupération Directe des Médias

#### Tous les médias d'une publication
```http
GET /api/content/publication-media/?publication_id={publication_id}
```

#### Un média spécifique
```http
GET /api/content/publication-media/{media_id}/
```

## Configuration des URLs de Médias

Les médias sont servis depuis :
- **URL de base :** `{BACKEND_URL}/media/`
- **Chemin complet :** `{BACKEND_URL}/media/publications/media/{filename}`

### Exemple de Configuration Frontend

```typescript
// Configuration
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const MEDIA_BASE_URL = `${BACKEND_URL}/media/`;

// Helper function
const getMediaUrl = (mediaFile: string): string => {
  if (mediaFile.startsWith('http')) {
    return mediaFile; // URL absolue
  }
  return `${MEDIA_BASE_URL}${mediaFile}`;
};
```

## Stratégies d'Affichage

### 1. Liste des Publications (Aperçu)

Pour la liste des publications, utilisez uniquement `featured_media` :

```typescript
interface PublicationListProps {
  publications: PublicationList[];
}

const PublicationList: React.FC<PublicationListProps> = ({ publications }) => {
  return (
    <div className="publications-grid">
      {publications.map(publication => (
        <div key={publication.id} className="publication-card">
          {/* Image de couverture */}
          {publication.featured_media && (
            <div className="publication-cover">
              {publication.featured_media.media_type === 'IMAGE' && (
                <img 
                  src={getMediaUrl(publication.featured_media.file)}
                  alt={publication.featured_media.alt_text || publication.title}
                  className="cover-image"
                />
              )}
              {publication.featured_media.media_type === 'VIDEO' && (
                <video 
                  src={getMediaUrl(publication.featured_media.file)}
                  poster={getMediaUrl(publication.featured_media.file)}
                  className="cover-video"
                  muted
                >
                  <source src={getMediaUrl(publication.featured_media.file)} />
                </video>
              )}
            </div>
          )}
          
          {/* Contenu textuel */}
          <div className="publication-content">
            <h3>{publication.title}</h3>
            <p>{publication.summary}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
```

### 2. Détail d'une Publication (Tous les médias)

Pour les détails, récupérez et affichez tous les médias :

```typescript
interface PublicationDetailProps {
  publication: PublicationDetail;
}

const PublicationDetail: React.FC<PublicationDetailProps> = ({ publication }) => {
  // Trier les médias par ordre
  const sortedMedia = [...publication.media].sort((a, b) => a.order - b.order);
  
  return (
    <article className="publication-detail">
      {/* Titre */}
      <h1>{publication.title}</h1>
      
      {/* Médias */}
      {sortedMedia.length > 0 && (
        <div className="publication-media">
          {sortedMedia.map(media => (
            <MediaComponent key={media.id} media={media} />
          ))}
        </div>
      )}
      
      {/* Contenu textuel */}
      <div className="publication-content">
        <div dangerouslySetInnerHTML={{ __html: publication.content }} />
      </div>
    </article>
  );
};
```

### 3. Composant Média Générique

```typescript
interface MediaComponentProps {
  media: PublicationMedia;
  className?: string;
}

const MediaComponent: React.FC<MediaComponentProps> = ({ media, className = '' }) => {
  const mediaUrl = getMediaUrl(media.file);
  
  const renderMedia = () => {
    switch (media.media_type) {
      case 'IMAGE':
        return (
          <img 
            src={mediaUrl}
            alt={media.alt_text || media.title || 'Image de publication'}
            title={media.title}
            className={`media-image ${className}`}
            loading="lazy"
          />
        );
        
      case 'VIDEO':
        return (
          <video 
            src={mediaUrl}
            controls
            className={`media-video ${className}`}
            title={media.title}
          >
            <source src={mediaUrl} />
            Votre navigateur ne supporte pas les vidéos.
          </video>
        );
        
      case 'AUDIO':
        return (
          <audio 
            src={mediaUrl}
            controls
            className={`media-audio ${className}`}
            title={media.title}
          >
            <source src={mediaUrl} />
            Votre navigateur ne supporte pas l'audio.
          </audio>
        );
        
      case 'DOCUMENT':
        return (
          <div className={`media-document ${className}`}>
            <a 
              href={mediaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="document-link"
            >
              📄 {media.title || 'Document'}
            </a>
            <span className="file-size">
              ({formatFileSize(media.file_size)})
            </span>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="media-container">
      {renderMedia()}
      {media.description && (
        <p className="media-description">{media.description}</p>
      )}
    </div>
  );
};

// Helper pour formater la taille des fichiers
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
```

## Gestion des Erreurs

### 1. Médias Manquants

```typescript
const handleImageError = (event: React.SyntheticEvent<HTMLImageElement>) => {
  const img = event.currentTarget;
  img.src = '/images/placeholder-image.png'; // Image de remplacement
  img.alt = 'Image non disponible';
};

// Utilisation
<img 
  src={getMediaUrl(media.file)}
  alt={media.alt_text || 'Image'}
  onError={handleImageError}
/>
```

### 2. Types de Médias Non Supportés

```typescript
const isSupportedMediaType = (mediaType: string): boolean => {
  return ['IMAGE', 'VIDEO', 'AUDIO', 'DOCUMENT'].includes(mediaType);
};
```

## Performance et Optimisation

### 1. Lazy Loading

```typescript
// Pour les images
<img 
  src={getMediaUrl(media.file)}
  alt={media.alt_text}
  loading="lazy"
  decoding="async"
/>
```

### 2. Préchargement des Médias de Couverture

```typescript
useEffect(() => {
  publications.forEach(publication => {
    if (publication.featured_media?.media_type === 'IMAGE') {
      const img = new Image();
      img.src = getMediaUrl(publication.featured_media.file);
    }
  });
}, [publications]);
```

### 3. Mise en Cache

```typescript
// Configuration Next.js pour les médias
// next.config.js
module.exports = {
  images: {
    domains: ['localhost', 'votre-domaine.com'],
    loader: 'default',
  },
};

// Utilisation
import Image from 'next/image';

<Image
  src={getMediaUrl(media.file)}
  alt={media.alt_text}
  width={800}
  height={600}
  priority={media.is_featured}
/>
```

## Exemples Pratiques

### 1. Carrousel de Médias

```typescript
const MediaCarousel: React.FC<{ media: PublicationMedia[] }> = ({ media }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const sortedMedia = [...media].sort((a, b) => a.order - b.order);
  
  return (
    <div className="media-carousel">
      <div className="carousel-container">
        <MediaComponent media={sortedMedia[currentIndex]} />
      </div>
      
      {sortedMedia.length > 1 && (
        <div className="carousel-controls">
          <button 
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
          >
            ← Précédent
          </button>
          
          <span>{currentIndex + 1} / {sortedMedia.length}</span>
          
          <button 
            onClick={() => setCurrentIndex(Math.min(sortedMedia.length - 1, currentIndex + 1))}
            disabled={currentIndex === sortedMedia.length - 1}
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  );
};
```

### 2. Grille de Médias

```typescript
const MediaGrid: React.FC<{ media: PublicationMedia[] }> = ({ media }) => {
  const sortedMedia = [...media].sort((a, b) => a.order - b.order);
  
  return (
    <div className={`media-grid media-count-${sortedMedia.length}`}>
      {sortedMedia.map(mediaItem => (
        <div key={mediaItem.id} className="media-grid-item">
          <MediaComponent media={mediaItem} />
        </div>
      ))}
    </div>
  );
};
```

## Cas d'Usage Spéciaux

### 1. Publications Sponsorisées

```typescript
// Les publications sponsorisées peuvent avoir des médias publicitaires
if (publication.is_sponsored) {
  // Afficher l'indicateur de sponsoring
  // Gérer les médias publicitaires différemment
}
```

### 2. Publications Épinglées

```typescript
// Les publications épinglées peuvent avoir des médias prioritaires
if (publication.is_pinned) {
  // Précharger les médias
  // Afficher en priorité
}
```

## Checklist d'Implémentation

- [ ] ✅ Configurer l'URL de base des médias
- [ ] ✅ Implémenter le helper `getMediaUrl()`
- [ ] ✅ Créer le composant `MediaComponent` générique
- [ ] ✅ Gérer les erreurs de chargement
- [ ] ✅ Implémenter le lazy loading
- [ ] ✅ Ajouter les textes alternatifs pour l'accessibilité
- [ ] ✅ Tester tous les types de médias (IMAGE, VIDEO, AUDIO, DOCUMENT)
- [ ] ✅ Optimiser les performances avec mise en cache
- [ ] ✅ Gérer les médias manquants ou corrompus
- [ ] ✅ Tester sur différentes tailles d'écran

## Notes Importantes

1. **Limite de 3 médias** : Chaque publication ne peut avoir que 3 médias maximum
2. **Image de couverture** : Un seul média peut être `is_featured: true`
3. **Ordre d'affichage** : Utilisez toujours le champ `order` pour trier
4. **Accessibilité** : Toujours utiliser `alt_text` ou `title` pour les médias
5. **Performance** : Implémenter le lazy loading pour les grandes listes
6. **Sécurité** : Les URLs de médias sont publiques mais les fichiers sont validés côté backend

## Support et Dépannage

- **Médias ne s'affichent pas** : Vérifier la configuration `MEDIA_URL` et `MEDIA_ROOT`
- **Erreurs CORS** : Configurer `CORS_ALLOWED_ORIGINS` pour inclure le domaine frontend
- **Images trop lentes** : Implémenter la compression et le redimensionnement
- **Vidéos ne se lisent pas** : Vérifier les codecs supportés par le navigateur