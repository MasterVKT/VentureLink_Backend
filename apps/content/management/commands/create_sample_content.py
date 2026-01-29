"""
Commande Django pour créer des publications de test (app content) et ajouter des commentaires
pour les publications et les projets existants.
"""
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from apps.content.models.publication import Publication, PublicationMedia
from apps.content.models.comment import Comment
from apps.projects.models import Project
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crée des publications de test avec médias et commentaires, ainsi que des commentaires sur les projets'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Supprime les publications et commentaires existants avant création')
        parser.add_argument('--publications', type=int, default=4, help='Nombre de publications à créer')
        parser.add_argument('--comments', type=int, default=3, help='Nombre de commentaires par publication et par projet')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des anciennes publications et commentaires…'))
            Comment.objects.all().delete()
            PublicationMedia.objects.all().delete()
            Publication.objects.all().delete()

        # S'assurer qu'un utilisateur staff existe pour les publications
        author, _ = User.objects.get_or_create(
            email='admin.content@test.venturelink.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Content',
                'is_staff': True,
                'is_superuser': False,
                'user_type': 'ADMIN',
                'is_active': True,
            }
        )

        users = list(User.objects.exclude(email=author.email))
        if not users:
            self.stdout.write(self.style.ERROR('Aucun utilisateur standard trouvé pour créer des commentaires.'))
            return

        publications_data = [
            {
                'title': 'Les 5 erreurs à éviter en levant des fonds',
                'summary': 'Découvrez les pièges courants lors d\'une levée de fonds et comment les contourner.',
                'content': 'Lever des fonds est une étape cruciale… (contenu détaillé)…',
                'publication_type': 'TIPS',
                'domain': 'FINANCE_INVESTMENT',
                'tags': 'Levée de fonds,Investissement,Startup'
            },
            {
                'title': 'Étude de cas : Comment EcoTrack a réduit son churn de 40 %',
                'summary': 'Retour d\'expérience détaillé sur l\'optimisation produit et la fidélisation client.',
                'content': 'Dans cet article, nous analysons en profondeur…',
                'publication_type': 'CASE_STUDY',
                'domain': 'BUSINESS_STRATEGY',
                'tags': 'Churn,Rétention,Product Management'
            },
            {
                'title': '10 outils IA pour booster la productivité des entrepreneurs',
                'summary': 'Un tour d\'horizon des meilleurs outils basés sur l\'IA pour gagner du temps.',
                'content': 'L\'intelligence artificielle transforme notre quotidien…',
                'publication_type': 'INFORMATIONAL',
                'domain': 'TECHNOLOGY',
                'tags': 'IA,Outils,Productivité'
            },
            {
                'title': 'Guide complet du pitch deck parfait',
                'summary': 'Structure, design, storytelling : tout ce qu\'il faut pour convaincre les investisseurs.',
                'content': 'Un pitch deck efficace doit raconter une histoire claire…',
                'publication_type': 'TUTORIAL',
                'domain': 'ENTREPRENEURSHIP',
                'tags': 'Pitch,Investisseurs,Storytelling'
            },
        ]

        # Limiter selon l'argument
        pubs_to_create = publications_data[:options['publications']]
        created_pubs = []
        for data in pubs_to_create:
            pub = Publication.objects.create(
                author=author,
                title=data['title'],
                summary=data['summary'],
                content=data['content'],
                publication_type=data['publication_type'],
                domain=data['domain'],
                tags=data['tags'],
                status='PUBLISHED',
                published_at=timezone.now(),
                views_count=0,
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Publication créée : {pub.title}'))
            self._add_media(pub)
            self._add_comments(pub, users, options['comments'])
            created_pubs.append(pub)

        # Ajouter des commentaires aux projets existants
        projects = Project.objects.filter(is_draft=False)[:options['publications']]
        if projects:
            for project in projects:
                self._add_comments(project, users, options['comments'])
            self.stdout.write(self.style.SUCCESS(f'✅ Commentaires ajoutés à {len(projects)} projets'))

        self.stdout.write(self.style.SUCCESS('🎉 Création de contenu de test terminée.'))

    # ------------------------
    def _add_media(self, pub):
        """Ajoute 2 images et 1 document à la publication"""
        img_urls = [
            'https://picsum.photos/seed/{}/800/500'.format(pub.id.hex[:6]),
            'https://picsum.photos/seed/{}b/800/500'.format(pub.id.hex[:6]),
        ]
        for idx, url in enumerate(img_urls):
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    filename = f'publication_{pub.id}_image_{idx+1}.jpg'
                    content = ContentFile(resp.content, filename)
                    PublicationMedia.objects.create(
                        publication=pub,
                        file=content,
                        media_type='IMAGE',
                        title=f'Illustration {idx+1}',
                        order=idx,
                        is_featured=(idx == 0),
                    )
                    self.stdout.write(f'   📸 Image {idx+1} ajoutée')
            except Exception as exc:
                self.stdout.write(f'   ⚠️  Erreur téléchargement image : {exc}')

        # Document
        doc_content = f"""RÉSUMÉ – {pub.title}\n\n{pub.summary}\n\n{pub.content[:500]}…"""
        filename = f'publication_{pub.id}_doc.txt'
        PublicationMedia.objects.create(
            publication=pub,
            file=ContentFile(doc_content.encode('utf-8'), filename),
            media_type='DOCUMENT',
            title='Document complémentaire',
            order=2,
        )
        self.stdout.write('   📄 Document ajouté')

    def _add_comments(self, target_obj, users, nb_comments):
        """Ajoute des commentaires génériques à une publication ou un projet"""
        ctype = ContentType.objects.get_for_model(type(target_obj))
        for i in range(nb_comments):
            user = users[i % len(users)]
            Comment.objects.create(
                content_type=ctype,
                object_id=str(target_obj.id),
                author=user,
                content=f"Super contenu ! Merci pour ces infos ({i+1}).",
            )
        # Mettre à jour le compteur sur l'objet si attribut présent
        if hasattr(target_obj, 'comments_count'):
            target_obj.comments_count += nb_comments
            target_obj.save(update_fields=['comments_count']) 