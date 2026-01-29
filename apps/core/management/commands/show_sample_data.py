"""
Commande Django pour afficher un résumé des données de test créées.
"""
from django.core.management.base import BaseCommand
from apps.projects.models import Project, ProjectMedia, ProjectCategory, ProjectTag
from apps.users.models import User


class Command(BaseCommand):
    help = 'Affiche un résumé des données de test créées'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RÉSUMÉ DES DONNÉES DE TEST VENTURELINK ===\n'))
        
        # Statistiques générales
        users_count = User.objects.filter(email__contains='test.venturelink').count()
        categories_count = ProjectCategory.objects.count()
        tags_count = ProjectTag.objects.count()
        projects_count = Project.objects.count()
        media_count = ProjectMedia.objects.count()
        
        self.stdout.write(f'👥 Utilisateurs de test: {users_count}')
        self.stdout.write(f'📂 Catégories: {categories_count}')
        self.stdout.write(f'🏷️  Tags: {tags_count}')
        self.stdout.write(f'🚀 Projets: {projects_count}')
        self.stdout.write(f'📁 Médias: {media_count}\n')
        
        # Détail des utilisateurs
        self.stdout.write(self.style.WARNING('=== UTILISATEURS DE TEST ==='))
        for user in User.objects.filter(email__contains='test.venturelink'):
            status_icons = []
            if user.is_verified:
                status_icons.append('✅')
            if user.is_premium:
                status_icons.append('⭐')
            status = ' '.join(status_icons) if status_icons else ''
            
            self.stdout.write(f'👤 {user.get_full_name()} ({user.user_type}) {status}')
            self.stdout.write(f'   📧 {user.email}')
            self.stdout.write(f'   📍 {user.location}')
        
        self.stdout.write('')
        
        # Détail des catégories
        self.stdout.write(self.style.WARNING('=== CATÉGORIES DE PROJETS ==='))
        for category in ProjectCategory.objects.all():
            project_count = category.projects.count()
            self.stdout.write(f'📂 {category.name_fr} ({category.name_en}) - {project_count} projets')
        
        self.stdout.write('')
        
        # Détail des projets
        self.stdout.write(self.style.WARNING('=== PROJETS CRÉÉS ==='))
        for project in Project.objects.all():
            images = project.media.filter(media_type='IMAGE').count()
            docs = project.media.filter(media_type='DOCUMENT').count()
            videos = project.media.filter(media_type='VIDEO').count()
            
            self.stdout.write(f'🎯 {project.title}')
            self.stdout.write(f'   👤 Créateur: {project.creator.get_full_name()}')
            self.stdout.write(f'   📊 {project.get_stage_display()} | {project.get_status_display()}')
            self.stdout.write(f'   📂 Catégorie: {project.category.name_fr}')
            self.stdout.write(f'   💰 {project.funding_min}€ - {project.funding_max}€ ({project.funding_currency})')
            self.stdout.write(f'   📍 {project.location_city}, {project.location_country}')
            self.stdout.write(f'   📁 Médias: {images} images, {docs} documents, {videos} vidéos')
            
            # Tags
            tags = ', '.join([tag.name_fr for tag in project.tags.all()])
            if tags:
                self.stdout.write(f'   🏷️  Tags: {tags}')
            
            self.stdout.write('')
        
        # Résumé des médias
        self.stdout.write(self.style.WARNING('=== TYPES DE MÉDIAS ==='))
        for media_type in ['IMAGE', 'DOCUMENT', 'VIDEO']:
            count = ProjectMedia.objects.filter(media_type=media_type).count()
            icon = {'IMAGE': '📸', 'DOCUMENT': '📄', 'VIDEO': '🎥'}[media_type]
            self.stdout.write(f'{icon} {media_type}: {count} fichiers')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✨ Les données de test sont prêtes pour vos tests !'))
        self.stdout.write(self.style.SUCCESS('🔗 Vous pouvez maintenant tester l\'API et le frontend avec ces données.'))
        self.stdout.write('')
        self.stdout.write('💡 Suggestions de tests:')
        self.stdout.write('   - Authentification avec les utilisateurs de test')
        self.stdout.write('   - Recherche et filtrage des projets')
        self.stdout.write('   - Visualisation des médias (images et documents)')
        self.stdout.write('   - Test des différents stades et statuts de projets')
        self.stdout.write('   - Test des fonctionnalités premium vs standard') 