#!/usr/bin/env python
"""
Script de vérification de la cohérence du projet VentureLink.
Vérifie automatiquement les problèmes d'incohérence et génère un rapport.
"""

import os
import sys
import django
from pathlib import Path
import importlib
from collections import defaultdict

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

from django.apps import apps
from django.conf import settings
from django.urls import get_resolver
from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter


class ProjectConsistencyChecker:
    """Vérificateur de cohérence du projet."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def add_issue(self, category, description, severity="ERROR"):
        """Ajouter un problème."""
        self.issues.append({
            'category': category,
            'description': description,
            'severity': severity
        })
    
    def add_warning(self, category, description):
        """Ajouter un avertissement."""
        self.warnings.append({
            'category': category,
            'description': description
        })
    
    def add_info(self, category, description):
        """Ajouter une information."""
        self.info.append({
            'category': category,
            'description': description
        })
    
    def check_url_patterns(self):
        """Vérifier les patterns d'URL."""
        print("🔍 Vérification des patterns d'URL...")
        
        # Vérifier les URLs principales
        resolver = get_resolver()
        url_patterns = []
        
        def extract_patterns(patterns, prefix=""):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    extract_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    url_patterns.append(prefix + str(pattern.pattern))
        
        extract_patterns(resolver.url_patterns)
        
        # Vérifier les doublons
        pattern_counts = defaultdict(int)
        for pattern in url_patterns:
            pattern_counts[pattern] += 1
        
        for pattern, count in pattern_counts.items():
            if count > 1:
                self.add_issue(
                    "URL_PATTERNS", 
                    f"Pattern d'URL dupliqué: {pattern} (trouvé {count} fois)"
                )
        
        self.add_info("URL_PATTERNS", f"Total: {len(url_patterns)} patterns d'URL trouvés")
    
    def check_serializers(self):
        """Vérifier les sérialiseurs."""
        print("🔍 Vérification des sérialiseurs...")
        
        serializer_count = 0
        incomplete_serializers = []
        
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('apps.'):
                try:
                    serializers_module = importlib.import_module(f"{app_config.name}.serializers")
                    
                    # Parcourir les sous-modules
                    if hasattr(serializers_module, '__path__'):
                        for file_path in Path(serializers_module.__path__[0]).glob("*.py"):
                            if file_path.name != "__init__.py":
                                module_name = f"{app_config.name}.serializers.{file_path.stem}"
                                try:
                                    module = importlib.import_module(module_name)
                                    for attr_name in dir(module):
                                        attr = getattr(module, attr_name)
                                        if (isinstance(attr, type) and 
                                            issubclass(attr, serializers.Serializer) and
                                            attr != serializers.Serializer and
                                            attr != serializers.ModelSerializer):
                                            
                                            serializer_count += 1
                                            
                                            # Vérifier si le sérialiseur a une classe Meta
                                            if not hasattr(attr, 'Meta'):
                                                incomplete_serializers.append(f"{module_name}.{attr_name}")
                                
                                except ImportError:
                                    pass
                    
                except ImportError:
                    pass
        
        self.add_info("SERIALIZERS", f"Total: {serializer_count} sérialiseurs trouvés")
        
        for serializer in incomplete_serializers:
            self.add_issue("SERIALIZERS", f"Sérialiseur incomplet (pas de classe Meta): {serializer}")
    
    def check_views(self):
        """Vérifier les vues."""
        print("🔍 Vérification des vues...")
        
        view_count = 0
        views_without_permission = []
        
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('apps.'):
                try:
                    views_module = importlib.import_module(f"{app_config.name}.views")
                    
                    # Parcourir les sous-modules
                    if hasattr(views_module, '__path__'):
                        for file_path in Path(views_module.__path__[0]).glob("*.py"):
                            if file_path.name != "__init__.py":
                                module_name = f"{app_config.name}.views.{file_path.stem}"
                                try:
                                    module = importlib.import_module(module_name)
                                    for attr_name in dir(module):
                                        attr = getattr(module, attr_name)
                                        if (isinstance(attr, type) and 
                                            issubclass(attr, viewsets.ViewSet) and
                                            attr != viewsets.ViewSet and
                                            attr != viewsets.GenericViewSet and
                                            attr != viewsets.ModelViewSet):
                                            
                                            view_count += 1
                                            
                                            # Vérifier les permissions
                                            if not hasattr(attr, 'permission_classes'):
                                                views_without_permission.append(f"{module_name}.{attr_name}")
                                
                                except ImportError:
                                    pass
                
                except ImportError:
                    pass
        
        self.add_info("VIEWS", f"Total: {view_count} vues trouvées")
        
        for view in views_without_permission:
            self.add_warning("VIEWS", f"Vue sans permission_classes explicite: {view}")
    
    def check_models(self):
        """Vérifier les modèles."""
        print("🔍 Vérification des modèles...")
        
        models = apps.get_models()
        model_count = len(models)
        
        models_without_str = []
        models_without_verbose_name = []
        
        for model in models:
            # Vérifier la méthode __str__
            if not hasattr(model, '__str__') or model.__str__ is object.__str__:
                models_without_str.append(f"{model._meta.app_label}.{model.__name__}")
            
            # Vérifier verbose_name
            if not hasattr(model._meta, 'verbose_name') or model._meta.verbose_name == model.__name__:
                models_without_verbose_name.append(f"{model._meta.app_label}.{model.__name__}")
        
        self.add_info("MODELS", f"Total: {model_count} modèles trouvés")
        
        for model in models_without_str:
            self.add_warning("MODELS", f"Modèle sans méthode __str__ personnalisée: {model}")
        
        for model in models_without_verbose_name:
            self.add_warning("MODELS", f"Modèle sans verbose_name: {model}")
    
    def check_installed_apps(self):
        """Vérifier les applications installées."""
        print("🔍 Vérification des applications installées...")
        
        installed_apps = settings.INSTALLED_APPS
        custom_apps = [app for app in installed_apps if app.startswith('apps.')]
        
        self.add_info("INSTALLED_APPS", f"Total: {len(installed_apps)} applications installées")
        self.add_info("INSTALLED_APPS", f"Applications personnalisées: {len(custom_apps)}")
        
        # Vérifier que toutes les apps personnalisées existent
        for app in custom_apps:
            try:
                apps.get_app_config(app.split('.')[-1])
            except LookupError:
                self.add_issue("INSTALLED_APPS", f"Application introuvable: {app}")
    
    def check_middleware(self):
        """Vérifier les middleware."""
        print("🔍 Vérification des middleware...")
        
        middleware = settings.MIDDLEWARE
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ]
        
        for required in required_middleware:
            if required not in middleware:
                self.add_issue("MIDDLEWARE", f"Middleware requis manquant: {required}")
        
        self.add_info("MIDDLEWARE", f"Total: {len(middleware)} middleware configurés")
    
    def run_checks(self):
        """Exécuter toutes les vérifications."""
        print("🚀 Démarrage de la vérification de cohérence du projet VentureLink...\n")
        
        self.check_installed_apps()
        self.check_middleware()
        self.check_url_patterns()
        self.check_models()
        self.check_serializers()
        self.check_views()
        
        return self.generate_report()
    
    def generate_report(self):
        """Générer le rapport de vérification."""
        print("\n" + "="*80)
        print("📊 RAPPORT DE VÉRIFICATION DE COHÉRENCE")
        print("="*80)
        
        # Statistiques
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_info = len(self.info)
        
        print(f"\n📈 STATISTIQUES:")
        print(f"   🔴 Problèmes critiques: {total_issues}")
        print(f"   🟡 Avertissements: {total_warnings}")
        print(f"   ℹ️  Informations: {total_info}")
        
        # Problèmes critiques
        if self.issues:
            print(f"\n🔴 PROBLÈMES CRITIQUES ({total_issues}):")
            for issue in self.issues:
                print(f"   [{issue['category']}] {issue['description']}")
        
        # Avertissements
        if self.warnings:
            print(f"\n🟡 AVERTISSEMENTS ({total_warnings}):")
            for warning in self.warnings:
                print(f"   [{warning['category']}] {warning['description']}")
        
        # Informations
        if self.info:
            print(f"\nℹ️  INFORMATIONS ({total_info}):")
            for info in self.info:
                print(f"   [{info['category']}] {info['description']}")
        
        # Conclusion
        print(f"\n{'='*80}")
        if total_issues == 0:
            print("✅ PROJET COHÉRENT - Aucun problème critique détecté!")
        else:
            print(f"❌ ATTENTION - {total_issues} problème(s) critique(s) détecté(s)")
        
        if total_warnings > 0:
            print(f"⚠️  {total_warnings} avertissement(s) à considérer")
        
        print("="*80)
        
        return {
            'issues': total_issues,
            'warnings': total_warnings,
            'info': total_info,
            'details': {
                'issues': self.issues,
                'warnings': self.warnings,
                'info': self.info
            }
        }


if __name__ == "__main__":
    checker = ProjectConsistencyChecker()
    result = checker.run_checks()
    
    # Code de sortie
    sys.exit(1 if result['issues'] > 0 else 0) 