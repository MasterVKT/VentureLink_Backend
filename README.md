# VentureLink - API Backend

API backend pour l'application VentureLink, une plateforme connectant entrepreneurs et investisseurs.

## Technologies utilisées

- Django 4.2+
- Django REST Framework
- PostgreSQL (production) / SQLite (développement)
- Redis pour le cache et Celery
- Firebase Auth pour l'authentification
- Swagger/OpenAPI pour la documentation API

## Configuration de l'environnement de développement

### 🏗️ Système Multi-Environnements

Ce projet utilise un système multi-environnements pour séparer les configurations :

- **Development** : Configuration locale avec SQLite et outils de debug
- **Test** : Configuration optimisée pour les tests automatisés
- **Production** : Configuration sécurisée avec PostgreSQL et HTTPS

L'environnement est sélectionné automatiquement via la variable `DJANGO_ENV` :

```bash
# Windows
set DJANGO_ENV=development
# Linux/Mac
export DJANGO_ENV=development
```

📖 **[Guide complet des environnements](docs/ENVIRONMENTS.md)**

### Prérequis

- Python 3.10+
- pip et virtualenv
- Redis (pour le cache et Celery en production)

### Installation

1. Cloner le dépôt :

```bash
git clone https://github.com/your-organization/venturelink-backend.git
cd venturelink-backend
```

2. Créer et activer un environnement virtuel :

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python -m venv env
source env/bin/activate
```

3. Installer les dépendances :

```bash
pip install -r requirements/development.txt
```

4. Configurer les variables d'environnement :

**Option A** : Copier l'exemple et personnaliser
```bash
# Windows
copy docs\env-development.example .env
# Linux/Mac
cp docs/env-development.example .env
```

**Option B** : Créer un fichier `.env` à la racine du projet avec les variables suivantes :

```
DJANGO_ENV=development
DJANGO_SECRET_KEY=your-secret-key-here

# Firebase (optionnel en développement)
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
```

5. Configurer Firebase Admin SDK (optionnel) :

Placez votre fichier `firebase-admin-sdk.json` dans le dossier `config/`.
Si vous n'avez pas Firebase, laissez le fichier avec les placeholders.

6. Exécuter les migrations :

```bash
python manage.py migrate
```

7. Créer un superutilisateur :

```bash
python manage.py createsuperuser
```

8. Lancer le serveur de développement :

```bash
python manage.py runserver
```

## Documentation API

La documentation API est disponible aux URLs suivantes après avoir lancé le serveur :

- Swagger UI : [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- ReDoc : [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)

## Tests

Pour exécuter les tests :

```bash
# Exécuter tous les tests
pytest

# Avec rapports de couverture
pytest --cov=apps
```

## Déploiement

### Environnements

Le projet supporte trois environnements :

- Développement : Configuration locale
- Test : Pour les tests automatisés
- Production : Environnement de production

Pour sélectionner l'environnement, définissez la variable d'environnement `DJANGO_ENV` :

```bash
# Windows
set DJANGO_ENV=production

# Linux/macOS
export DJANGO_ENV=production
```

### Production

Pour le déploiement en production, utilisez les paramètres suivants :

1. Installer les dépendances de production :

```bash
pip install -r requirements/production.txt
```

2. Configurer les variables d'environnement spécifiques à la production

3. Collecter les fichiers statiques :

```bash
python manage.py collectstatic --no-input
```

4. Exécuter avec gunicorn :

```bash
gunicorn venture_link_project.wsgi:application
```

## Structure du projet

```
venture_link_project/
├── manage.py
├── venture_link_project/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/
│   ├── users/
│   ├── projects/
│   ├── messaging/
│   └── notifications/
├── config/
│   └── firebase-admin-sdk.json
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── test.txt
├── static/
├── media/
├── templates/
└── logs/
```

## État d'avancement du développement

### Fonctionnalités implémentées

1. **Structure du projet**
   - Configuration multi-environnements (développement, test, production)
   - Utilisation de modèles abstraits réutilisables (TimeStampedModel, UUIDModel)
   - Organisation modulaire des applications
   - Intégration Firebase

2. **Authentification et Utilisateurs**
   - Modèles d'utilisateurs personnalisés avec profils
   - Authentification par email avec JWT
   - Système de gestion des rôles (Entrepreneur, Investisseur, etc.)
   - API d'inscription, connexion et gestion de profil

3. **Projets**
   - Modèles complets pour la gestion des projets
   - Catégories et tags pour classification
   - Système de médias et documents associés
   - Besoins en compétences et financement
   - API CRUD avec permissions et filtres avancés

4. **Investissements**
   - Modèles pour gérer différents types d'investissements (equity, loan)
   - Système de paiements et transactions
   - Échéanciers de remboursement pour les prêts
   - API sécurisée avec permissions spécifiques

5. **Messagerie**
   - Conversations directes, de groupe et liées aux projets
   - Système de messages avec pièces jointes
   - Fonctionnalités de lecture/accusés de réception
   - API complète avec permissions de participants
   - Gestion d'archivage et de suppression

6. **Core et utilitaires**
   - Gestion multi-devises avec conversion
   - Utilitaires d'envoi d'emails
   - Gestion d'exceptions personnalisées
   - Middleware de sécurité et d'authentification

### Tests

Des tests unitaires ont été créés pour vérifier le bon fonctionnement des principales fonctionnalités :
- Tests des modèles (projects, investments, messaging)
- Tests des vues et API (endpoints REST)
- Tests des services métier (conversation_service, message_service, etc.)

Les tests de l'application messaging comprennent :
- Tests des vues : test_views.py - Tests des endpoints de conversations et messages
- Tests des services : test_services.py - Tests des services de gestion des conversations et messages
- Tests des modèles : test_models.py - Tests des modèles de messages, conversations et attachements

### Prochaines étapes

1. **Résoudre les problèmes d'importation** pour permettre l'exécution des tests unitaires
2. **Implémentation des notifications** :
   - Finir l'intégration avec Firebase Cloud Messaging
   - Implémenter le service d'envoi de notifications
   - Développer le système de préférences de notification
3. **Compléter les fonctionnalités sociales** :
   - Finir l'implémentation des questions et réponses
   - Ajouter les systèmes de notation et évaluation
4. **Analytics** :
   - Ajouter les modèles de métriques
   - Créer les tâches périodiques pour les calculs statistiques
5. **Documentation** :
   - Finaliser la documentation API
   - Ajouter des exemples d'utilisation

## Commandes utiles

```bash
# Activer l'environnement virtuel
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
..\Scripts\Activate

# Exécuter les migrations
python manage.py migrate

# Créer un super utilisateur
python manage.py createsuperuser

# Exécuter le serveur de développement
python manage.py runserver

# Exécuter les tests
python manage.py test
``` 