"""
Management command to display environment configuration status.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Display current environment configuration status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🔍 VentureLink Environment Status\n'))
        
        # Environment detection
        env = os.environ.get('DJANGO_ENV', 'development')
        self.stdout.write(f"📍 Current Environment: {self.style.SUCCESS(env.upper())}")
        
        # Django settings
        self.stdout.write(f"\n🔧 Django Configuration:")
        debug_color = self.style.WARNING if settings.DEBUG else self.style.SUCCESS
        self.stdout.write(f"   DEBUG: {debug_color(str(settings.DEBUG))}")
        secret_color = self.style.SUCCESS if settings.SECRET_KEY else self.style.ERROR
        secret_text = '✓ Set' if settings.SECRET_KEY else '✗ Missing'
        self.stdout.write(f"   SECRET_KEY: {secret_color(secret_text)}")
        
        # Database
        db_config = settings.DATABASES['default']
        self.stdout.write(f"\n💾 Database:")
        engine_name = db_config['ENGINE'].split('.')[-1]
        self.stdout.write(f"   Engine: {self.style.MIGRATE_LABEL(engine_name)}")
        if 'sqlite' in db_config['ENGINE']:
            self.stdout.write(f"   Path: {db_config['NAME']}")
        else:
            self.stdout.write(f"   Host: {db_config.get('HOST', 'Not set')}")
            self.stdout.write(f"   Port: {db_config.get('PORT', 'Not set')}")
        
        # Firebase
        self.stdout.write(f"\n🔥 Firebase:")
        firebase_enabled = getattr(settings, 'FIREBASE_ENABLED', True)
        if hasattr(settings, 'FIREBASE_CONFIG'):
            project_id = settings.FIREBASE_CONFIG.get('projectId', '')
            if project_id:
                self.stdout.write(f"   Status: {self.style.SUCCESS('✓ Configured')}")
                self.stdout.write(f"   Project ID: {project_id}")
            else:
                self.stdout.write(f"   Status: {self.style.WARNING('⚠ Not configured')}")
        else:
            self.stdout.write(f"   Status: {self.style.ERROR('✗ No configuration')}")
        
        if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH'):
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if os.path.exists(cred_path):
                # Check if file contains placeholders
                try:
                    with open(cred_path, 'r') as f:
                        content = f.read()
                        if 'placeholder' in content.lower():
                            self.stdout.write(f"   Credentials: {self.style.WARNING('⚠ Placeholder file')}")
                        else:
                            self.stdout.write(f"   Credentials: {self.style.SUCCESS('✓ Valid file found')}")
                except Exception:
                    self.stdout.write(f"   Credentials: {self.style.ERROR('✗ Cannot read file')}")
            else:
                self.stdout.write(f"   Credentials: {self.style.ERROR('✗ File not found')}")
        
        # Cache
        self.stdout.write(f"\n🗄️ Cache:")
        cache_backend = settings.CACHES['default']['BACKEND'].split('.')[-1]
        self.stdout.write(f"   Backend: {self.style.MIGRATE_LABEL(cache_backend)}")
        
        # Email
        self.stdout.write(f"\n📧 Email:")
        email_backend = settings.EMAIL_BACKEND.split('.')[-1]
        self.stdout.write(f"   Backend: {self.style.MIGRATE_LABEL(email_backend)}")
        
        # CORS
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            self.stdout.write(f"\n🌐 CORS:")
            for origin in settings.CORS_ALLOWED_ORIGINS[:3]:  # Show first 3
                self.stdout.write(f"   {origin}")
            if len(settings.CORS_ALLOWED_ORIGINS) > 3:
                self.stdout.write(f"   ... and {len(settings.CORS_ALLOWED_ORIGINS) - 3} more")
        
        # Recommendations
        self.stdout.write(f"\n💡 Recommendations:")
        
        if env == 'development':
            if not firebase_enabled or not hasattr(settings, 'FIREBASE_CONFIG') or not settings.FIREBASE_CONFIG.get('projectId'):
                self.stdout.write(f"   • {self.style.WARNING('Firebase is optional in development')}")
            self.stdout.write(f"   • {self.style.SUCCESS('Use SQLite for local development')}")
            
        elif env == 'production':
            if settings.DEBUG:
                self.stdout.write(f"   • {self.style.ERROR('WARNING: DEBUG should be False in production!')}")
            if 'sqlite' in db_config['ENGINE']:
                self.stdout.write(f"   • {self.style.ERROR('WARNING: Use PostgreSQL in production!')}")
            if not firebase_enabled:
                self.stdout.write(f"   • {self.style.ERROR('WARNING: Firebase should be configured in production!')}")
        
        self.stdout.write(f"\n✅ Environment check complete!")
        
        # Show helpful commands
        self.stdout.write(f"\n🛠️ Useful Commands:")
        self.stdout.write(f"   python manage.py check              # Django system check")
        self.stdout.write(f"   python manage.py migrate            # Apply database migrations") 
        self.stdout.write(f"   python manage.py runserver          # Start development server")
        if env != 'test':
            self.stdout.write(f"   DJANGO_ENV=test python manage.py test  # Run tests") 