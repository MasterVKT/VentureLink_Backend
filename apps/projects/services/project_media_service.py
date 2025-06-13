"""
Service for managing project media.
"""
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, ValidationError

from apps.projects.models import Project, ProjectMedia

import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
from django.core.files.base import ContentFile
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ProjectMediaService:
    """Service for managing project media."""

    # 🔴 NOUVELLE FONCTIONNALITÉ : Limites de médias basées sur le statut premium
    MAX_MEDIA_FREE_USER = 1
    MAX_MEDIA_PREMIUM_USER = 3
    
    # 🔴 NOUVELLE FONCTIONNALITÉ : Configuration de compression optimisée
    COMPRESSION_CONFIG = {
        'high_quality': {'quality': 95, 'optimize': True},
        'standard': {'quality': 85, 'optimize': True},
        'web_optimized': {'quality': 75, 'optimize': True, 'progressive': True},
        'thumbnail': {'quality': 70, 'optimize': True}
    }

    @staticmethod
    def get_user_media_limit(user):
        """
        Retourne la limite de médias par projet pour un utilisateur.
        
        Args:
            user: Utilisateur
            
        Returns:
            int: Limite de médias par projet
        """
        return ProjectMediaService.MAX_MEDIA_PREMIUM_USER if user.is_premium else ProjectMediaService.MAX_MEDIA_FREE_USER

    @staticmethod
    def check_media_limit(project, user, exclude_media_id=None):
        """
        Vérifie si l'utilisateur peut ajouter des médias au projet.
        
        Args:
            project: Projet
            user: Utilisateur
            exclude_media_id: ID du média à exclure du décompte (pour les mises à jour)
            
        Returns:
            dict: {'can_add': bool, 'limit': int, 'current': int, 'remaining': int}
            
        Raises:
            ValidationError: Si la limite est dépassée
        """
        limit = ProjectMediaService.get_user_media_limit(user)
        
        # Compter les médias existants
        current_media = project.media.all()
        if exclude_media_id:
            current_media = current_media.exclude(id=exclude_media_id)
        current_count = current_media.count()
        
        remaining = max(0, limit - current_count)
        can_add = remaining > 0
        
        return {
            'can_add': can_add,
            'limit': limit,
            'current': current_count,
            'remaining': remaining,
            'is_premium': user.is_premium
        }

    @staticmethod
    def compress_image(image, target_size_kb=500, max_dimension=1920):
        """
        Compresse une image avec le meilleur rapport qualité/taille.
        
        Args:
            image: Image PIL
            target_size_kb: Taille cible en KB
            max_dimension: Dimension maximale (largeur ou hauteur)
            
        Returns:
            ContentFile: Image compressée
        """
        # Redimensionner si nécessaire
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convertir en RGB si nécessaire
        if image.mode in ('RGBA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Appliquer un léger filtre de netteté pour compenser la compression
        image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=3))
        
        # Essayer différents niveaux de qualité pour atteindre la taille cible
        target_size_bytes = target_size_kb * 1024
        best_quality = 95
        
        for quality in [95, 85, 75, 65, 55, 45]:
            img_io = io.BytesIO()
            
            # Configuration de compression optimisée
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': True,
                'progressive': True,
                'subsampling': 0 if quality >= 85 else 2  # Meilleur sous-échantillonnage pour haute qualité
            }
            
            image.save(img_io, **save_kwargs)
            
            if img_io.tell() <= target_size_bytes or quality == 45:
                best_quality = quality
                break
            
        # Sauvegarder avec la meilleure qualité trouvée
        img_io.seek(0)
        img_io.truncate(0)
        
        final_save_kwargs = {
            'format': 'JPEG',
            'quality': best_quality,
            'optimize': True,
            'progressive': True,
            'subsampling': 0 if best_quality >= 85 else 2
        }
        
        image.save(img_io, **final_save_kwargs)
        img_io.seek(0)
        
        logger.info(f"Image compressée: qualité={best_quality}, taille={img_io.tell()/1024:.1f}KB")
        
        return ContentFile(img_io.getvalue())

    @staticmethod
    def get_project_media(project_id, media_type=None):
        """
        Get all media for a project.
        
        Args:
            project_id: The project ID
            media_type: Optional media type filter
            
        Returns:
            QuerySet of ProjectMedia objects
        """
        media = ProjectMedia.objects.filter(project_id=project_id)
        
        if media_type:
            media = media.filter(media_type=media_type)
            
        return media.order_by('order', '-created_at')

    @staticmethod
    def get_media_detail(media_id, project_id=None):
        """
        Get a specific project media.
        
        Args:
            media_id: The media ID
            project_id: Optional project ID to validate ownership
            
        Returns:
            ProjectMedia object
            
        Raises:
            ProjectMedia.DoesNotExist: If media not found
        """
        if project_id:
            return ProjectMedia.objects.get(id=media_id, project_id=project_id)
        return ProjectMedia.objects.get(id=media_id)

    @staticmethod
    def create_media(project_id, creator, file, media_type, title=None, description=None, is_primary=False, order=0):
        """
        Create a new media for a project.
        
        Args:
            project_id: The project ID
            creator: User creating the media
            file: The media file
            media_type: Type of media
            title: Optional title
            description: Optional description
            is_primary: Whether this is the primary image
            order: Display order
            
        Returns:
            Created ProjectMedia object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ValidationError: If media limit is exceeded
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != creator:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à ajouter des médias à ce projet"))
        
        # 🔴 NOUVELLE FONCTIONNALITÉ : Vérifier la limite de médias
        limit_check = ProjectMediaService.check_media_limit(project, creator)
        if not limit_check['can_add']:
            if creator.is_premium:
                raise ValidationError(
                    f"Limite de médias atteinte. Vous pouvez avoir au maximum {limit_check['limit']} médias par projet (compte premium)."
                )
            else:
                raise ValidationError(
                    f"Limite de médias atteinte. Vous pouvez avoir au maximum {limit_check['limit']} média par projet. "
                    f"Passez au compte premium pour avoir jusqu'à {ProjectMediaService.MAX_MEDIA_PREMIUM_USER} médias par projet."
                )
        
        # 🔴 NOUVELLE FONCTIONNALITÉ : Compresser les images
        if media_type == ProjectMedia.MEDIA_TYPE_IMAGE and hasattr(file, 'read'):
            try:
                # Ouvrir l'image avec PIL
                image = Image.open(file)
                
                # Appliquer la compression optimisée
                compressed_file = ProjectMediaService.compress_image(image)
                
                # Remplacer le fichier original par la version compressée
                original_name = getattr(file, 'name', 'image.jpg')
                compressed_file.name = original_name
                file = compressed_file
                
                logger.info(f"Image compressée pour le projet {project_id}")
                
            except Exception as e:
                logger.warning(f"Impossible de compresser l'image pour le projet {project_id}: {e}")
                # Continuer avec le fichier original si la compression échoue
        
        # Create with transaction to ensure consistency
        with transaction.atomic():
            # If this media is marked as primary, remove primary status from others
            if is_primary and media_type == ProjectMedia.MEDIA_TYPE_IMAGE:
                ProjectMedia.objects.filter(
                    project=project,
                    media_type=ProjectMedia.MEDIA_TYPE_IMAGE,
                    is_primary=True
                ).update(is_primary=False)
            
            # Create the media
            media = ProjectMedia.objects.create(
                project=project,
                file=file,
                media_type=media_type,
                title=title,
                description=description,
                is_primary=is_primary,
                order=order
            )
            
            return media

    @staticmethod
    def update_media(media_id, project_id, user, data):
        """
        Update a project media.
        
        Args:
            media_id: The media ID
            project_id: The project ID
            user: User performing the update
            data: Dictionary with fields to update
            
        Returns:
            Updated ProjectMedia object
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectMedia.DoesNotExist: If media not found
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à modifier les médias de ce projet"))
        
        # Get the media
        media = ProjectMedia.objects.get(id=media_id, project=project)
        
        # Update with transaction to ensure consistency
        with transaction.atomic():
            # Handle primary status
            if data.get('is_primary') and data.get('is_primary') != media.is_primary and media.media_type == ProjectMedia.MEDIA_TYPE_IMAGE:
                ProjectMedia.objects.filter(
                    project=project,
                    media_type=ProjectMedia.MEDIA_TYPE_IMAGE,
                    is_primary=True
                ).exclude(id=media_id).update(is_primary=False)
            
            # Update fields
            for field, value in data.items():
                if hasattr(media, field) and field != 'file' and field != 'project':
                    setattr(media, field, value)
            
            # Handle file update separately if provided
            if 'file' in data:
                media.file = data['file']
            
            media.save()
            return media

    @staticmethod
    def delete_media(media_id, project_id, user):
        """
        Delete a project media.
        
        Args:
            media_id: The media ID
            project_id: The project ID
            user: User performing the deletion
            
        Returns:
            bool: True if successful
            
        Raises:
            PermissionDenied: If user is not the project creator
            ProjectMedia.DoesNotExist: If media not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à supprimer les médias de ce projet"))
        
        # Get the media and delete
        media = ProjectMedia.objects.get(id=media_id, project=project)
        media.delete()
        
        return True

    @staticmethod
    def reorder_media(project_id, user, media_order_data):
        """
        Reorder project media.
        
        Args:
            project_id: The project ID
            user: User performing the reordering
            media_order_data: List of dicts with media_id and new order
            
        Returns:
            bool: True if successful
            
        Raises:
            PermissionDenied: If user is not the project creator
            Project.DoesNotExist: If project not found
        """
        # Get the project and validate ownership
        project = Project.objects.get(id=project_id)
        
        if project.creator != user:
            raise PermissionDenied(_("Vous n'êtes pas autorisé à réorganiser les médias de ce projet"))
        
        # Update orders with transaction
        with transaction.atomic():
            for item in media_order_data:
                media_id = item.get('media_id')
                new_order = item.get('order')
                
                if media_id and new_order is not None:
                    try:
                        media = ProjectMedia.objects.get(id=media_id, project=project)
                        media.order = new_order
                        media.save(update_fields=['order'])
                    except ProjectMedia.DoesNotExist:
                        continue
        
        return True

    @staticmethod
    def generate_placeholder_image(project, width=1200, height=800):
        """
        Génère une image de placeholder personnalisée pour un projet
        
        Args:
            project: Instance du projet
            width: Largeur de l'image
            height: Hauteur de l'image
            
        Returns:
            ContentFile: Fichier image généré
        """
        # Couleurs basées sur la catégorie
        colors = ProjectMediaService._get_category_colors(
            project.category.name_fr if project.category else 'Général'
        )
        
        # Créer l'image
        image = Image.new('RGB', (width, height), colors['background'])
        draw = ImageDraw.Draw(image)
        
        # Ajouter des formes géométriques
        ProjectMediaService._add_geometric_shapes(draw, width, height, colors)
        
        # Ajouter le texte
        ProjectMediaService._add_text_to_image(draw, project, width, height, colors)
        
        # 🔴 AMÉLIORATION : Utiliser la compression optimisée
        return ProjectMediaService.compress_image(image, target_size_kb=400)
    
    @staticmethod
    def download_image_from_url(url, timeout=30):
        """
        Télécharge une image depuis une URL
        
        Args:
            url: URL de l'image
            timeout: Timeout en secondes
            
        Returns:
            ContentFile: Fichier image téléchargé
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Vérifier que c'est bien une image
            image = Image.open(io.BytesIO(response.content))
            
            # Redimensionner si nécessaire
            if image.size[0] > 1920 or image.size[1] > 1080:
                image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
            
            # 🔴 AMÉLIORATION : Utiliser la compression optimisée
            return ProjectMediaService.compress_image(image, target_size_kb=500)
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement d'image depuis {url}: {e}")
            raise
    
    @staticmethod
    def create_project_media(project, file_content, title=None, description=None, 
                           is_primary=False, media_type=ProjectMedia.MEDIA_TYPE_IMAGE):
        """
        Crée un média pour un projet
        
        Args:
            project: Instance du projet
            file_content: Contenu du fichier (ContentFile)
            title: Titre du média
            description: Description du média
            is_primary: Si c'est le média principal
            media_type: Type de média
            
        Returns:
            ProjectMedia: Instance créée
        """
        with transaction.atomic():
            # Si c'est défini comme principal, désactiver les autres
            if is_primary:
                ProjectMedia.objects.filter(
                    project=project, 
                    is_primary=True
                ).update(is_primary=False)
            
            # Créer l'instance
            project_media = ProjectMedia(
                project=project,
                media_type=media_type,
                title=title or f"Média - {project.title}",
                description=description or f"Média pour le projet {project.title}",
                is_primary=is_primary,
                order=ProjectMedia.objects.filter(project=project).count() + 1
            )
            
            # Sauvegarder le fichier
            filename = f"project_{project.id}_{project_media.id or 'new'}.jpg"
            project_media.file.save(filename, file_content, save=False)
            project_media.save()
            
            return project_media
    
    @staticmethod
    def bulk_generate_media_for_projects(projects=None, count=1, source='generated'):
        """
        Génère des médias pour plusieurs projets
        
        Args:
            projects: Liste des projets (None pour tous)
            count: Nombre de médias par projet
            source: Source des médias ('generated', 'unsplash', 'placeholder')
            
        Returns:
            dict: Statistiques de génération
        """
        if projects is None:
            projects = Project.objects.all()
        
        stats = {
            'processed': 0,
            'success': 0,
            'errors': 0,
            'total_media': 0
        }
        
        for project in projects:
            stats['processed'] += 1
            try:
                project_stats = ProjectMediaService._generate_media_for_project(
                    project, count, source
                )
                stats['success'] += 1
                stats['total_media'] += project_stats['created']
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Erreur génération média pour projet {project.id}: {e}")
        
        return stats
    
    @staticmethod
    def _generate_media_for_project(project, count, source):
        """Génère des médias pour un projet spécifique"""
        stats = {'created': 0}
        
        for i in range(count):
            try:
                if source == 'generated':
                    file_content = ProjectMediaService.generate_placeholder_image(project)
                    title = f"Image générée {i+1} - {project.title}"
                elif source == 'unsplash':
                    try:
                        keywords = ProjectMediaService._get_category_keywords(
                            project.category.name_fr if project.category else 'business'
                        )
                        url = f"https://source.unsplash.com/1200x800/?{keywords}"
                        file_content = ProjectMediaService.download_image_from_url(url)
                        title = f"Image Unsplash {i+1} - {project.title}"
                    except:
                        # Fallback vers placeholder
                        file_content = ProjectMediaService.generate_placeholder_image(project)
                        title = f"Image placeholder {i+1} - {project.title}"
                else:  # placeholder
                    file_content = ProjectMediaService._generate_simple_placeholder(project)
                    title = f"Placeholder {i+1} - {project.title}"
                
                # Créer le média
                ProjectMediaService.create_project_media(
                    project=project,
                    file_content=file_content,
                    title=title,
                    description=f"Média généré automatiquement pour {project.title}",
                    is_primary=(i == 0 and not project.media.filter(is_primary=True).exists())
                )
                
                stats['created'] += 1
                
            except Exception as e:
                logger.error(f"Erreur création média {i+1} pour projet {project.id}: {e}")
        
        return stats
    
    @staticmethod
    def _generate_simple_placeholder(project, width=800, height=600):
        """Génère un placeholder simple"""
        # Couleur de fond basée sur le hash du titre
        hash_value = hash(project.title) % 16777215
        bg_color = f'#{hash_value:06x}'
        
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Ajouter le titre au centre
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Calculer la position du texte
        bbox = draw.textbbox((0, 0), project.title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), project.title, fill='white', font=font)
        
        # Convertir en bytes
        img_io = io.BytesIO()
        image.save(img_io, format='JPEG', quality=85, optimize=True)
        img_io.seek(0)
        
        return ContentFile(img_io.getvalue())
    
    @staticmethod
    def _get_category_colors(category_name):
        """Retourne des couleurs basées sur la catégorie"""
        color_schemes = {
            'Agriculture': {'background': '#8FBC8F', 'primary': '#228B22', 'secondary': '#32CD32'},
            'Technologie': {'background': '#4682B4', 'primary': '#191970', 'secondary': '#87CEEB'},
            'Santé': {'background': '#DC143C', 'primary': '#8B0000', 'secondary': '#FFB6C1'},
            'Éducation': {'background': '#DAA520', 'primary': '#B8860B', 'secondary': '#FFFFE0'},
            'Commerce': {'background': '#9370DB', 'primary': '#4B0082', 'secondary': '#DDA0DD'},
            'Énergie': {'background': '#FF8C00', 'primary': '#FF4500', 'secondary': '#FFE4E1'},
            'Transport': {'background': '#2F4F4F', 'primary': '#708090', 'secondary': '#F0F8FF'},
            'Tourisme': {'background': '#20B2AA', 'primary': '#008B8B', 'secondary': '#F0FFFF'},
            'Technologie financière': {'background': '#6B8E23', 'primary': '#556B2F', 'secondary': '#F5FFFA'},
        }
        
        return color_schemes.get(category_name, {
            'background': '#696969', 
            'primary': '#2F4F4F', 
            'secondary': '#F5F5F5'
        })
    
    @staticmethod
    def _get_category_keywords(category_name):
        """Retourne des mots-clés pour Unsplash basés sur la catégorie"""
        keywords_map = {
            'Agriculture': 'agriculture,farming,crops',
            'Technologie': 'technology,innovation,startup',
            'Santé': 'healthcare,medical,health',
            'Éducation': 'education,learning,knowledge',
            'Commerce': 'business,commerce,trade',
            'Énergie': 'energy,renewable,power',
            'Transport': 'transportation,logistics,mobility',
            'Tourisme': 'tourism,travel,destination',
            'Technologie financière': 'fintech,finance,banking',
        }
        
        return keywords_map.get(category_name, 'business,startup,innovation')
    
    @staticmethod
    def _add_geometric_shapes(draw, width, height, colors):
        """Ajoute des formes géométriques décoratives"""
        # Cercle en haut à droite
        draw.ellipse([width-150, 0, width, 150], fill=colors['primary'])
        
        # Rectangle en bas à gauche
        draw.rectangle([0, height-100, 200, height], fill=colors['secondary'])
        
        # Triangle ou losange au centre
        center_x, center_y = width // 2, height // 2
        points = [
            (center_x - 50, center_y),
            (center_x, center_y - 50),
            (center_x + 50, center_y),
            (center_x, center_y + 50)
        ]
        draw.polygon(points, fill=colors['primary'])
    
    @staticmethod
    def _add_text_to_image(draw, project, width, height, colors):
        """Ajoute le texte du projet à l'image"""
        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            subtitle_font = ImageFont.truetype("arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Titre principal
        title_text = project.title
        if len(title_text) > 40:
            title_text = title_text[:37] + "..."
        
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height // 2 + 100
        
        draw.text((x, y), title_text, fill='white', font=title_font)
        
        # Sous-titre (catégorie)
        if project.category:
            category_text = f"Catégorie: {project.category.name_fr}"
            bbox = draw.textbbox((0, 0), category_text, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = height // 2 + 160
            
            draw.text((x, y), category_text, fill='white', font=subtitle_font) 