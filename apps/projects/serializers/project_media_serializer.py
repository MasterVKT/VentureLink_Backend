"""
Serializers for project media models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.projects.models.project_media import ProjectMedia


class ProjectMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectMedia model.
    """
    file_url = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMedia
        fields = [
            'id', 'file', 'file_url', 'media_type', 'title',
            'description', 'is_primary', 'order', 'size', 'uploader',
            'uploader_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'size', 'uploader']

    def get_file_url(self, obj):
        """Return the absolute URL of the file."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def get_uploader_name(self, obj):
        """Return the uploader's name if available."""
        if obj.uploader:
            return obj.uploader.get_full_name()
        return None


class ProjectMediaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating project media with compression and validation.
    """
    
    # Taille maximale : 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB en bytes
    
    # Dimensions maximales pour les images
    MAX_IMAGE_SIZE = (1920, 1920)
    
    # Qualité de compression JPEG
    JPEG_QUALITY = 85

    class Meta:
        model = ProjectMedia
        fields = [
            'file', 'media_type', 'title',
            'description', 'is_primary', 'order'
        ]

    def validate_file(self, value):
        """
        Valider et compresser l'image uploadée.
        
        - Vérifie la taille maximale (10MB)
        - Vérifie que c'est une image valide
        - Compresse automatiquement les images JPEG/PNG
        """
        # Vérifier la taille (max 10MB)
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                _('L\'image ne doit pas dépasser 10MB. Taille actuelle : %(size).2f MB') % {
                    'size': value.size / (1024 * 1024)
                }
            )
        
        # Vérifier que c'est une image (seulement pour IMAGE type)
        media_type = self.initial_data.get('media_type', ProjectMedia.MEDIA_TYPE_IMAGE)
        if media_type == ProjectMedia.MEDIA_TYPE_IMAGE:
            try:
                from PIL import Image
                # Ouvrir et vérifier l'image
                img = Image.open(value)
                img.verify()  # Vérifie que c'est une image valide
                
                # Réouvrir l'image après verify()
                value.seek(0)
                img = Image.open(value)
                
                # Vérifier le format
                if img.format not in ['JPEG', 'PNG', 'WEBP', 'GIF']:
                    raise serializers.ValidationError(
                        _('Format d\'image non supporté. Formats acceptés : JPEG, PNG, WEBP, GIF')
                    )
                
                # Compresser si c'est une image (pas GIF animé)
                if img.format != 'GIF':
                    compressed_file = self._compress_image(img, value)
                    if compressed_file:
                        return compressed_file
                
            except Exception as e:
                raise serializers.ValidationError(
                    _('Fichier image invalide : %(error)s') % {'error': str(e)}
                )
        
        return value

    def _compress_image(self, img, original_file):
        """
        Compresser une image avec les spécifications suivantes :
        - Redimensionnement max 1920x1920
        - Conversion en JPEG si nécessaire
        - Qualité 85%
        """
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import InMemoryUploadedFile
        import sys
        
        # Redimensionner si trop grande
        if img.size[0] > self.MAX_IMAGE_SIZE[0] or img.size[1] > self.MAX_IMAGE_SIZE[1]:
            img.thumbnail(self.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Convertir RGBA en RGB si nécessaire (pour JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc pour les images avec transparence
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Sauvegarder avec compression
        output = BytesIO()
        img.save(output, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
        output.seek(0)
        
        # Créer un nouveau fichier compressé
        filename = f"{original_file.name.split('.')[0]}.jpg"
        compressed_file = InMemoryUploadedFile(
            output,
            'ImageField',
            filename,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
        return compressed_file

    def create(self, validated_data):
        """
        Create and return a new project media instance.
        """
        project_id = self.context.get('project_id')
        request = self.context.get('request')
        
        if not project_id:
            raise serializers.ValidationError(_('L\'ID du projet est requis.'))

        # Get the file to calculate size
        file = validated_data.get('file')
        size = file.size if file else None

        # Create media instance with size and uploader
        media = ProjectMedia.objects.create(
            project_id=project_id,
            size=size,
            uploader=request.user if request else None,
            **validated_data
        )
        
        return media


class ProjectMediaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating project media.
    """
    
    class Meta:
        model = ProjectMedia
        fields = [
            'title', 'description', 
            'is_primary', 'order'
        ] 