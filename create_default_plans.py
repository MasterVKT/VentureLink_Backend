#!/usr/bin/env python
"""
Script pour créer les plans d'abonnement par défaut VentureLink
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

from apps.payments.models import SubscriptionPlan

def create_default_plans():
    """Crée les plans d'abonnement par défaut."""
    
    plans_data = [
        {
            'id': 'free',
            'name': 'Plan Gratuit',
            'description': 'Plan de base gratuit pour découvrir VentureLink',
            'price_eur': 0.00,
            'price_xaf': 0.00,
            'price_usd': 0.00,
            'duration_days': 365,  # 1 an
            'features': [
                'Accès aux projets publics',
                'Création de 1 projet',
                '5 messages par mois',
                'Support communautaire'
            ],
            'max_projects': 1,
            'max_investments': 3,
            'max_messages': 5,
            'ai_matching': False,
            'priority_support': False,
            'advanced_analytics': False,
            'custom_branding': False,
            'is_active': True,
            'is_popular': False,
            'is_free': True,
            'sort_order': 1,
            'trial_days': 0,
        },
        {
            'id': 'basic_monthly',
            'name': 'Basic Mensuel',
            'description': 'Plan de base pour les entrepreneurs débutants',
            'price_eur': 9.99,
            'price_xaf': 6560.00,
            'price_usd': 10.99,
            'duration_days': 30,
            'features': [
                'Accès complet aux projets',
                'Création de 5 projets',
                '50 messages par mois',
                'Support email',
                'Statistiques de base'
            ],
            'max_projects': 5,
            'max_investments': 10,
            'max_messages': 50,
            'ai_matching': False,
            'priority_support': False,
            'advanced_analytics': False,
            'custom_branding': False,
            'is_active': True,
            'is_popular': False,
            'is_free': False,
            'sort_order': 2,
            'trial_days': 7,
        },
        {
            'id': 'premium_monthly',
            'name': 'Premium Mensuel',
            'description': 'Plan avancé pour les entrepreneurs sérieux',
            'price_eur': 29.99,
            'price_xaf': 19680.00,
            'price_usd': 32.99,
            'duration_days': 30,
            'features': [
                'Accès illimité aux projets',
                'Projets illimités',
                'Messages illimités',
                'Matching IA avancé',
                'Support prioritaire',
                'Analyses avancées',
                'Personnalisation interface'
            ],
            'max_projects': 0,  # Illimité
            'max_investments': 0,  # Illimité
            'max_messages': 0,  # Illimité
            'ai_matching': True,
            'priority_support': True,
            'advanced_analytics': True,
            'custom_branding': True,
            'is_active': True,
            'is_popular': True,  # Plan populaire
            'is_free': False,
            'sort_order': 3,
            'trial_days': 14,
        },
        {
            'id': 'premium_yearly',
            'name': 'Premium Annuel',
            'description': 'Plan premium avec 2 mois gratuits',
            'price_eur': 299.99,  # 10 mois au lieu de 12
            'price_xaf': 196800.00,
            'price_usd': 329.99,
            'duration_days': 365,
            'features': [
                'Toutes les fonctionnalités Premium',
                'Économie de 2 mois',
                'Support téléphonique',
                'Accès bêta aux nouvelles fonctionnalités',
                'Consultation stratégique mensuelle'
            ],
            'max_projects': 0,  # Illimité
            'max_investments': 0,  # Illimité
            'max_messages': 0,  # Illimité
            'ai_matching': True,
            'priority_support': True,
            'advanced_analytics': True,
            'custom_branding': True,
            'is_active': True,
            'is_popular': False,
            'is_free': False,
            'sort_order': 4,
            'trial_days': 30,
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            id=plan_data['id'],
            defaults=plan_data
        )
        
        if created:
            created_count += 1
            print(f"✅ Plan créé: {plan.name}")
        else:
            # Mettre à jour le plan existant
            for key, value in plan_data.items():
                setattr(plan, key, value)
            plan.save()
            updated_count += 1
            print(f"🔄 Plan mis à jour: {plan.name}")
    
    print(f"\n📊 Résumé:")
    print(f"   - Plans créés: {created_count}")
    print(f"   - Plans mis à jour: {updated_count}")
    print(f"   - Total plans: {SubscriptionPlan.objects.count()}")
    
    # Afficher tous les plans
    print(f"\n📋 Plans disponibles:")
    for plan in SubscriptionPlan.objects.all().order_by('sort_order'):
        print(f"   - {plan.id}: {plan.name} ({plan.format_price('EUR')})")

if __name__ == "__main__":
    create_default_plans() 