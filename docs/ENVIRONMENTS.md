# Guide des Environnements VentureLink

Ce projet utilise un système multi-environnements pour séparer les configurations selon le contexte d'exécution.

## 🏗️ Structure des Environnements

```
venture_link_project/settings/
├── __init__.py          # Sélection automatique de l'environnement
├── base.py              # Configuration commune à tous les environnements
├── development.py       # Configuration développement local
├── test.py              # Configuration pour les tests automatisés
└── production.py        # Configuration serveur de production
```

## 🎯 Sélection de l'Environnement

L'environnement est sélectionné automatiquement via la variable `DJANGO_ENV` :

```bash
# Développement (par défaut)
export DJANGO_ENV=development
# ou
set DJANGO_ENV=development  # Windows

# Tests
export DJANGO_ENV=test

# Production
export DJANGO_ENV=production
```

## 📋 Configurations par Environnement

### 🛠️ Développement (`development.py`)

**Objectif** : Faciliter le développement local avec outils de debug

**Caractéristiques** :
- `DEBUG = True` : Affichage détaillé des erreurs
- Base de données SQLite locale
- Emails affichés dans la console
- Django Debug Toolbar activé
- API browsable activée
- CORS permissif pour frontend local
- Cache dummy (pas de cache réel)
- Firebase optionnel

**Variables d'environnement requises** : Aucune (valeurs par défaut)

### 🧪 Tests (`test.py`)

**Objectif** : Exécution rapide et isolée des tests

**Caractéristiques** :
- Base de données en mémoire
- Firebase complètement désactivé
- Logs minimaux
- Cache dummy
- Emails désactivés
- Test runner personnalisé

**Variables d'environnement requises** : Aucune

### 🚀 Production (`production.py`)

**Objectif** : Performance et sécurité maximales

**Caractéristiques** :
- `DEBUG = False` : Pas d'informations sensibles exposées
- Base de données PostgreSQL
- HTTPS forcé avec HSTS
- Cookies sécurisés
- Cache Redis
- Sessions en cache
- Logs dans fichiers
- Emails SMTP réels
- CORS restrictif
- Firebase obligatoire

**Variables d'environnement requises** :
```bash
# Base de données
DB_NAME=venturelink
DB_USER=venturelink_user
DB_PASSWORD=your_secure_password
DB_HOST=db.example.com
DB_PORT=5432

# Email
EMAIL_HOST=smtp.mailgun.org
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_password

# Redis
REDIS_URL=redis://redis.example.com:6379/0

# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-key.json
```

## 🔄 Commandes Utiles

### Vérifier l'environnement actuel
```bash
python manage.py diffsettings
```

### Forcer un environnement spécifique
```bash
# Linux/Mac
DJANGO_ENV=production python manage.py check

# Windows
set DJANGO_ENV=production && python manage.py check
```

### Tests avec environnement de test
```bash
DJANGO_ENV=test python manage.py test
```

## 🔧 Variables d'Environnement Communes

Ces variables fonctionnent dans tous les environnements :

```bash
# Django
DJANGO_SECRET_KEY=your-super-secret-key
DJANGO_ENV=development|test|production

# Optionnelles
REDIS_URL=redis://localhost:6379/0
EXCHANGE_RATE_API_KEY=your_api_key
CURRENCY_CACHE_TIMEOUT=86400
```

## 📁 Fichiers .env Recommandés

Créez ces fichiers à la racine du projet (ils sont dans .gitignore) :

- `.env.development` : Variables pour développement
- `.env.test` : Variables pour tests  
- `.env.production` : Variables pour production (à sécuriser)

## ⚠️ Bonnes Pratiques

1. **Jamais de secrets dans le code** : Utilisez des variables d'environnement
2. **Testez chaque environnement** : `python manage.py check` sur chacun
3. **Variables par défaut** : Toujours fournir des valeurs par défaut sécurisées
4. **Documentation** : Documentez chaque nouvelle variable d'environnement
5. **Validation** : Vérifiez les variables critiques au démarrage

## 🚨 Dépannage

### "ModuleNotFoundError: No module named 'venture_link_project.settings'"
- Vérifiez que `__init__.py` existe dans le dossier settings
- Vérifiez la variable DJANGO_SETTINGS_MODULE dans manage.py

### "Environment variable not set"
- Créez un fichier .env avec les variables requises
- Ou exportez les variables dans votre shell

### Firebase errors en développement
- Normal si vous n'avez pas configuré Firebase
- Définissez `FIREBASE_ENABLED=False` pour désactiver complètement 