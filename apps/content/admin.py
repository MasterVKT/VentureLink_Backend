"""
Administration Django pour les modèles de contenu.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.content.models import Comment, CommentLike, Publication, PublicationMedia, PublicationLike


class CommentLikeInline(admin.TabularInline):
    """Inline pour les likes de commentaires."""
    model = CommentLike
    extra = 0
    readonly_fields = ['user', 'created_at']
    can_delete = False


class CommentReplyInline(admin.TabularInline):
    """Inline pour les réponses aux commentaires."""
    model = Comment
    fk_name = 'parent'
    extra = 0
    fields = ['author', 'content', 'is_active', 'created_at']
    readonly_fields = ['author', 'created_at']
    can_delete = False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Administration des commentaires."""
    list_display = ['id', 'content_preview', 'author', 'content_object_link', 'parent', 
                   'likes_count', 'replies_count', 'is_active', 'is_flagged', 'created_at']
    list_filter = ['is_active', 'is_flagged', 'content_type', 'created_at']
    search_fields = ['content', 'author__email', 'author__first_name', 'author__last_name']
    readonly_fields = ['content_type', 'object_id', 'likes_count', 'replies_count', 
                      'depth', 'created_at', 'updated_at']
    raw_id_fields = ['author', 'parent']
    inlines = [CommentLikeInline, CommentReplyInline]
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('author', 'content')
        }),
        (_('Objet commenté'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Hiérarchie'), {
            'fields': ('parent', 'depth')
        }),
        (_('Statistiques'), {
            'fields': ('likes_count', 'replies_count')
        }),
        (_('Modération'), {
            'fields': ('is_active', 'is_flagged', 'flag_count')
        }),
        (_('Métadonnées'), {
            'fields': ('is_edited', 'edited_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Aperçu du contenu."""
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content
    content_preview.short_description = _('Contenu')
    
    def content_object_link(self, obj):
        """Lien vers l'objet commenté."""
        if obj.content_object:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                f'/admin/{obj.content_type.app_label}/{obj.content_type.model}/{obj.object_id}/change/',
                str(obj.content_object)
            )
        return _('Objet supprimé')
    content_object_link.short_description = _('Objet commenté')
    
    actions = ['activate_comments', 'deactivate_comments', 'clear_flags']
    
    def activate_comments(self, request, queryset):
        """Activer les commentaires sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} commentaire(s) activé(s).')
    activate_comments.short_description = _('Activer les commentaires sélectionnés')
    
    def deactivate_comments(self, request, queryset):
        """Désactiver les commentaires sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} commentaire(s) désactivé(s).')
    deactivate_comments.short_description = _('Désactiver les commentaires sélectionnés')
    
    def clear_flags(self, request, queryset):
        """Effacer les signalements."""
        updated = queryset.update(is_flagged=False, flag_count=0)
        self.message_user(request, f'Signalements effacés pour {updated} commentaire(s).')
    clear_flags.short_description = _('Effacer les signalements')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """Administration des likes de commentaires."""
    list_display = ['id', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'comment__content']
    readonly_fields = ['user', 'comment', 'created_at']
    raw_id_fields = ['user', 'comment']
    
    def comment_preview(self, obj):
        """Aperçu du commentaire."""
        if len(obj.comment.content) > 30:
            return obj.comment.content[:30] + "..."
        return obj.comment.content
    comment_preview.short_description = _('Commentaire')


class PublicationMediaInline(admin.TabularInline):
    """Inline pour les médias de publication."""
    model = PublicationMedia
    extra = 0
    max_num = 3
    fields = ['file', 'media_type', 'title', 'order', 'is_featured']
    readonly_fields = ['file_size']


class PublicationLikeInline(admin.TabularInline):
    """Inline pour les likes de publication."""
    model = PublicationLike
    extra = 0
    readonly_fields = ['user', 'created_at']
    can_delete = False


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Administration des publications."""
    list_display = ['title', 'author', 'publication_type', 'domain', 'status', 
                   'is_featured', 'is_sponsored', 'views_count', 'likes_count', 
                   'comments_count', 'published_at']
    list_filter = ['publication_type', 'domain', 'status', 'is_featured', 
                  'is_pinned', 'is_sponsored', 'allow_comments', 'created_at']
    search_fields = ['title', 'content', 'summary', 'tags', 'author__email']
    readonly_fields = ['slug', 'views_count', 'likes_count', 'comments_count', 
                      'shares_count', 'published_at', 'created_at', 'updated_at']
    raw_id_fields = ['author']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PublicationMediaInline, PublicationLikeInline]
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('title', 'summary', 'content')
        }),
        (_('Classification'), {
            'fields': ('publication_type', 'domain', 'tags')
        }),
        (_('Métadonnées'), {
            'fields': ('author', 'status', 'scheduled_for')
        }),
        (_('Paramètres d\'affichage'), {
            'fields': ('is_featured', 'is_pinned', 'allow_comments')
        }),
        (_('Sponsoring'), {
            'fields': ('is_sponsored', 'sponsor_name', 'sponsor_url'),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_description', 'slug'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('views_count', 'likes_count', 'comments_count', 'shares_count'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_publications', 'unpublish_publications', 'feature_publications']
    
    def publish_publications(self, request, queryset):
        """Publier les publications sélectionnées."""
        from django.utils import timezone
        updated = queryset.filter(status=Publication.STATUS_DRAFT).update(
            status=Publication.STATUS_PUBLISHED,
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} publication(s) publiée(s).')
    publish_publications.short_description = _('Publier les publications sélectionnées')
    
    def unpublish_publications(self, request, queryset):
        """Dépublier les publications sélectionnées."""
        updated = queryset.filter(status=Publication.STATUS_PUBLISHED).update(
            status=Publication.STATUS_DRAFT
        )
        self.message_user(request, f'{updated} publication(s) dépubliée(s).')
    unpublish_publications.short_description = _('Dépublier les publications sélectionnées')
    
    def feature_publications(self, request, queryset):
        """Mettre en avant les publications sélectionnées."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} publication(s) mise(s) en avant.')
    feature_publications.short_description = _('Mettre en avant les publications sélectionnées')


@admin.register(PublicationMedia)
class PublicationMediaAdmin(admin.ModelAdmin):
    """Administration des médias de publication."""
    list_display = ['id', 'publication', 'media_type', 'title', 'order', 
                   'is_featured', 'file_size', 'created_at']
    list_filter = ['media_type', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'publication__title']
    readonly_fields = ['file_size', 'created_at']
    raw_id_fields = ['publication']


@admin.register(PublicationLike)
class PublicationLikeAdmin(admin.ModelAdmin):
    """Administration des likes de publication."""
    list_display = ['id', 'user', 'publication', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'publication__title']
    readonly_fields = ['user', 'publication', 'created_at']
    raw_id_fields = ['user', 'publication']
