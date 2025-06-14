from django.contrib import admin

from apps.projects.models.project import Project, ProjectCategory, ProjectTag
from apps.projects.models.project_media import ProjectMedia
from apps.projects.models.project_needs import ProjectNeeds, ProjectSkillsNeeded
from apps.projects.models.project_interaction import (
    ProjectInterest, ProjectFavorite, ProjectQuestion, ProjectQuestionAnswer
)


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_fr', 'name_en', 'is_active')
    search_fields = ('name_fr', 'name_en')
    list_filter = ('is_active',)


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ('name_fr', 'name_en', 'is_active')
    search_fields = ('name_fr', 'name_en')
    list_filter = ('is_active',)


class ProjectMediaInline(admin.TabularInline):
    model = ProjectMedia
    extra = 0


class ProjectNeedsInline(admin.TabularInline):
    model = ProjectNeeds
    extra = 0


class ProjectSkillsNeededInline(admin.TabularInline):
    model = ProjectSkillsNeeded
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'stage', 'status', 'is_draft', 'is_premium', 'is_featured', 'is_verified', 'verified_at')
    list_filter = ('category', 'stage', 'status', 'is_draft', 'is_premium', 'is_featured', 'is_verified', 'verified_by')
    search_fields = ('title', 'short_description', 'full_description')
    readonly_fields = ('views_count', 'interests_count', 'favorites_count', 'verified_at', 'verified_by', 'created_at', 'updated_at')
    filter_horizontal = ('tags',)
    inlines = [ProjectMediaInline, ProjectNeedsInline, ProjectSkillsNeededInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'short_description', 'full_description', 'category', 'tags')
        }),
        ('Détails du projet', {
            'fields': ('stage', 'funding_min', 'funding_max', 'funding_currency', 'location_country', 'location_city', 'video_url')
        }),
        ('État et visibilité', {
            'fields': ('creator', 'status', 'is_draft', 'is_premium', 'is_featured')
        }),
        ('Vérification (Administrateurs)', {
            'fields': ('is_verified', 'verified_at', 'verified_by', 'verification_notes'),
            'classes': ('collapse',)
        }),
        ('Statistiques', {
            'fields': ('views_count', 'interests_count', 'favorites_count', 'comments_count'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['verify_projects', 'unverify_projects']
    
    def verify_projects(self, request, queryset):
        """Action pour vérifier des projets en masse."""
        count = 0
        for project in queryset:
            if not project.is_verified:
                project.verify_project(request.user, "Vérification en masse via l'administration")
                count += 1
        
        self.message_user(request, f'{count} projet(s) vérifié(s) avec succès.')
    verify_projects.short_description = "Vérifier les projets sélectionnés"
    
    def unverify_projects(self, request, queryset):
        """Action pour dévérifier des projets en masse."""
        count = 0
        for project in queryset:
            if project.is_verified:
                project.unverify_project(request.user, "Dévérification en masse via l'administration")
                count += 1
        
        self.message_user(request, f'{count} projet(s) dévérifié(s) avec succès.')
    unverify_projects.short_description = "Retirer la vérification des projets sélectionnés"


@admin.register(ProjectMedia)
class ProjectMediaAdmin(admin.ModelAdmin):
    list_display = ('project', 'media_type', 'title', 'is_primary', 'order')
    list_filter = ('media_type', 'is_primary')
    search_fields = ('project__title', 'title', 'description')


@admin.register(ProjectNeeds)
class ProjectNeedsAdmin(admin.ModelAdmin):
    list_display = ('project', 'resource_type', 'title', 'is_critical', 'is_satisfied')
    list_filter = ('resource_type', 'is_critical', 'is_satisfied')
    search_fields = ('project__title', 'title', 'description')


@admin.register(ProjectSkillsNeeded)
class ProjectSkillsNeededAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'priority', 'required_level', 'is_satisfied')
    list_filter = ('priority', 'required_level', 'is_satisfied')
    search_fields = ('project__title', 'name', 'description')


@admin.register(ProjectInterest)
class ProjectInterestAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'status', 'is_anonymous', 'created_at')
    list_filter = ('status', 'is_anonymous')
    search_fields = ('project__title', 'user__email', 'message')


@admin.register(ProjectFavorite)
class ProjectFavoriteAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'created_at')
    search_fields = ('project__title', 'user__email', 'notes')


@admin.register(ProjectQuestion)
class ProjectQuestionAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'is_public', 'is_answered', 'created_at')
    list_filter = ('is_public', 'is_answered')
    search_fields = ('project__title', 'user__email', 'question')


@admin.register(ProjectQuestionAnswer)
class ProjectQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answered_by', 'created_at')
    search_fields = ('question__question', 'answered_by__email', 'answer') 