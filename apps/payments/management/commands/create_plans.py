"""
Commande de gestion pour créer les plans d'abonnement par défaut.
Sprint 3 - B3.4 : Système Abonnements
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Créer les plans d'abonnement par défaut (FREE, BASIC, PREMIUM)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mettre à jour les plans existants au lieu de les ignorer',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force_update = options['force']

        plans = [
            {
                'id': 'free',
                'name': 'FREE',
                'description': 'Plan gratuit — idéal pour démarrer sur VentureLink.',
                # Prix multi-devises
                'price_xaf': 0,
                'price_eur': 0,
                'price_usd': 0,
                # Durée
                'duration_days': 36500,  # Illimité (100 ans)
                # Limites
                'max_projects': 2,
                'max_investments': 5,
                'max_messages': 10,
                # Fonctionnalités booléennes
                'ai_matching': False,
                'priority_support': False,
                'advanced_analytics': False,
                'custom_branding': False,
                # Features JSON
                'features': [
                    '2 projets maximum',
                    '5 investissements maximum',
                    '10 messages par mois',
                    'Accès basique à la plateforme',
                ],
                # Configuration
                'is_active': True,
                'is_popular': False,
                'is_free': True,
                'sort_order': 1,
                'trial_days': 0,
                'mycoolpay_plan_id': None,
            },
            {
                'id': 'basic_monthly',
                'name': 'BASIC_MONTHLY',
                'description': 'Plan Basic mensuel — pour les entrepreneurs actifs.',
                'price_xaf': 5000,
                'price_eur': 8,
                'price_usd': 9,
                'duration_days': 30,
                'max_projects': 5,
                'max_investments': 20,
                'max_messages': 50,
                'ai_matching': True,
                'priority_support': False,
                'advanced_analytics': True,
                'custom_branding': False,
                'features': [
                    '5 projets maximum',
                    '20 investissements maximum',
                    '50 messages par mois',
                    'Matching IA',
                    'Analyses et statistiques',
                ],
                'is_active': True,
                'is_popular': False,
                'is_free': False,
                'sort_order': 2,
                'trial_days': 7,
                'mycoolpay_plan_id': None,
            },
            {
                'id': 'basic_yearly',
                'name': 'BASIC_YEARLY',
                'description': 'Plan Basic annuel — économisez 2 mois par rapport au mensuel.',
                'price_xaf': 50000,
                'price_eur': 80,
                'price_usd': 90,
                'duration_days': 365,
                'max_projects': 5,
                'max_investments': 20,
                'max_messages': 50,
                'ai_matching': True,
                'priority_support': False,
                'advanced_analytics': True,
                'custom_branding': False,
                'features': [
                    '5 projets maximum',
                    '20 investissements maximum',
                    '50 messages par mois',
                    'Matching IA',
                    'Analyses et statistiques',
                    '2 mois offerts vs mensuel',
                ],
                'is_active': True,
                'is_popular': False,
                'is_free': False,
                'sort_order': 3,
                'trial_days': 7,
                'mycoolpay_plan_id': None,
            },
            {
                'id': 'premium_monthly',
                'name': 'PREMIUM_MONTHLY',
                'description': 'Plan Premium mensuel — accès illimité à toutes les fonctionnalités.',
                'price_xaf': 15000,
                'price_eur': 23,
                'price_usd': 25,
                'duration_days': 30,
                'max_projects': 0,       # 0 = illimité
                'max_investments': 0,    # 0 = illimité
                'max_messages': 200,
                'ai_matching': True,
                'priority_support': True,
                'advanced_analytics': True,
                'custom_branding': True,
                'features': [
                    'Projets illimités',
                    'Investissements illimités',
                    '200 messages par mois',
                    'Matching IA avancé',
                    'Analyses et statistiques avancées',
                    'Support prioritaire',
                    'Personnalisation de la marque',
                ],
                'is_active': True,
                'is_popular': True,
                'is_free': False,
                'sort_order': 4,
                'trial_days': 14,
                'mycoolpay_plan_id': None,
            },
            {
                'id': 'premium_yearly',
                'name': 'PREMIUM_YEARLY',
                'description': 'Plan Premium annuel — le meilleur rapport qualité/prix.',
                'price_xaf': 150000,
                'price_eur': 230,
                'price_usd': 250,
                'duration_days': 365,
                'max_projects': 0,
                'max_investments': 0,
                'max_messages': 200,
                'ai_matching': True,
                'priority_support': True,
                'advanced_analytics': True,
                'custom_branding': True,
                'features': [
                    'Projets illimités',
                    'Investissements illimités',
                    '200 messages par mois',
                    'Matching IA avancé',
                    'Analyses et statistiques avancées',
                    'Support prioritaire',
                    'Personnalisation de la marque',
                    '2 mois offerts vs mensuel',
                ],
                'is_active': True,
                'is_popular': False,
                'is_free': False,
                'sort_order': 5,
                'trial_days': 14,
                'mycoolpay_plan_id': None,
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for plan_data in plans:
            plan_id = plan_data['id']

            if force_update:
                # Mettre à jour ou créer
                plan, created = SubscriptionPlan.objects.update_or_create(
                    id=plan_id,
                    defaults=plan_data,
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Plan créé : {plan.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  🔄 Plan mis à jour : {plan.name}')
                    )
            else:
                # Créer seulement si inexistant
                plan, created = SubscriptionPlan.objects.get_or_create(
                    id=plan_id,
                    defaults=plan_data,
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Plan créé : {plan.name}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.HTTP_INFO(f'  ⏭️  Plan déjà existant (ignoré) : {plan.name}')
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Terminé — {created_count} créé(s), '
            f'{updated_count} mis à jour, '
            f'{skipped_count} ignoré(s).'
        ))
        self.stdout.write('')
        self.stdout.write('Pour forcer la mise à jour des plans existants :')
        self.stdout.write('  python manage.py create_plans --force')
