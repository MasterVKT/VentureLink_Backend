# Instructions GitHub Copilot - VentureLink Backend

Ce fichier contient l'ensemble des règles et directives pour GitHub Copilot lors du développement du projet VentureLink Backend.

## 📋 Vue d'ensemble du projet

**VentureLink** est une plateforme backend Django/DRF connectant entrepreneurs et investisseurs, avec authentification Firebase, système de messagerie, notifications push, paiements via My-CoolPay API, et abonnements premium.

### Technologies principales
- Django 4.2+ avec Django REST Framework
- PostgreSQL (production) / SQLite (développement)
- Redis pour cache et Celery (tâches asynchrones)
- Firebase Admin SDK (authentification et notifications)
- My-CoolPay API (gestion des paiements)
- Docker & Docker Compose

---

## 🎯 Principes de développement

### 1. Suivre le plan de développement
- **Référence obligatoire** : Consulter `docs/Plan_de_Developpement_Backend_VentureLink.txt` avant toute implémentation
- **Ordre des phases** : Respecter strictement l'ordre des sprints et phases définis
- **Vérification systématique** : Avant chaque action, valider la conformité avec le plan

### 2. Conformité aux spécifications
Toujours vérifier la cohérence avec les documents de référence dans `docs/` :
- `Architecture Backend VentureLink.txt` - Architecture et patterns
- `Contrats_API_RESTFul_VentureLink.txt` - Contrats d'API
- `Conventions_et_Standards_VentureLink.txt` - Standards de code
- `Documentation_des_Services_Firebase_VentureLink.txt` - Configuration Firebase
- `Flux_Intégration_VentureLink.txt` - Flux d'intégration
- `Format_Données_Echangees_VentureLink.txt` - Formats de données

### 3. Validation préalable
- **Avant de répondre** : S'assurer de disposer de toutes les informations nécessaires
- **En cas de doute** : Poser des questions plutôt que faire des suppositions
- **Après chaque action** : Fournir une synthèse de ce qui a été fait et ce qui reste à faire

---

## 🏗️ Architecture et standards de code

### Organisation du projet

```
venture_link_project/
├── apps/                    # Applications Django modulaires
│   ├── core/               # Fonctionnalités partagées
│   ├── users/              # Gestion utilisateurs
│   ├── projects/           # Gestion projets
│   ├── messaging/          # Système de messagerie
│   ├── notifications/      # Notifications push
│   ├── payments/           # Intégration My-CoolPay
│   ├── analytics/          # Analytics et statistiques
│   ├── investments/        # Gestion investissements
│   └── content/            # Contenu et médias
├── config/                 # Configuration externe
├── docs/                   # Documentation
└── requirements/           # Dépendances par environnement
```

### Conventions de nommage

#### API et endpoints
- **Format URL de base** : `/api/v1/`
- **Routes** : Pluriel, minuscules (`users`, `projects`, `conversations`)
- **Query params** : `snake_case` (`sort_by`, `order_direction`)
- **Identifiants** : UUID dans URLs (`/projects/{uuid}`)

✅ Exemples corrects :
```
/api/v1/projects
/api/v1/projects/{id}/media
/api/v1/users/{id}/ratings
```

❌ À éviter :
```
/api/v1/Project           # Majuscule
/api/v1/user-profile      # Singulier
```

#### Code Python/Django
- **Modèles Django** : `PascalCase` singulier (`User`, `Project`, `Conversation`)
- **Champs de modèles** : `snake_case` (`first_name`, `created_at`)
- **Relations** : `snake_case` explicite (`project_owner`, `recipient_user`)
- **Clés étrangères** : `<nom_modèle>_id` (`user_id`, `project_id`)

#### Code frontend (Flutter)
- **Classes/composants** : `PascalCase` (`ProjectCard`, `MessageList`)
- **Variables/fonctions** : `camelCase` (`getUserProfile()`, `projectsList`)
- **Constantes** : `UPPER_SNAKE_CASE` (`API_BASE_URL`, `DEFAULT_TIMEOUT`)
- **Fichiers** : `snake_case` pour fichiers simples (`auth_service.dart`)

### Principes architecturaux

1. **DRY** (Don't Repeat Yourself) : Éviter la duplication de code
2. **SOC** (Separation of Concerns) : Séparer clairement les responsabilités
3. **KISS** (Keep It Simple, Stupid) : Privilégier les solutions simples
4. **YAGNI** (You Aren't Gonna Need It) : N'implémenter que le nécessaire
5. **API-first** : Conception orientée API

### Structure des applications Django

Pour chaque app, utiliser cette organisation en couches :

```
app_name/
├── models/              # Modèles (logique métier)
├── serializers/         # Sérialiseurs DRF
├── views/               # ViewSets et vues API
├── services/            # Logique métier complexe
├── urls.py              # Routing URL
└── tests/               # Tests unitaires
```

---

## 🔐 Sécurité et authentification

### Authentification
- **Méthode** : JWT (JSON Web Token) avec Firebase Auth
- **Header** : `Authorization: Bearer <token>`
- **Durée token** : 1 heure
- **Durée refresh token** : 2 semaines
- **Validation** : Toujours vérifier côté serveur

### Protection CSRF
- Tokens CSRF pour toutes les requêtes modifiant des données
- Header frontend : `X-CSRFToken: <token>`

### Données sensibles
- ❌ **Jamais** renvoyer mots de passe ou tokens de sécurité
- ✅ Hasher tous les mots de passe avec algorithmes robustes
- ✅ Valider et nettoyer toutes les entrées utilisateur

---

## 📦 Gestion des environnements

### Multi-environnements
Le projet utilise un système multi-environnements via `DJANGO_ENV` :
- **development** : SQLite, DEBUG=True, outils de debug
- **test** : Configuration optimisée pour tests automatisés
- **production** : PostgreSQL, DEBUG=False, sécurité renforcée

### Variables d'environnement
- Utiliser `.env` pour les configurations locales
- Référence : `docs/ENVIRONMENTS.md`
- Exemples : `docs/env-development.example`, `docs/env-production.example`

---

## 💳 Intégration paiements My-CoolPay

### Configuration
- **Documentation** : `docs/My-CoolPay API Docs.pdf`
- **Environnements** :
  - Développement : Bac à sable
  - Production : Clé API réelle
- **Structure du code** : Faciliter la transition dev → production

### Implémentation
- Utiliser le module `apps/payments/`
- Séparer configuration sandbox/production
- Gérer les webhooks pour notifications de paiement
- Valider et logger toutes les transactions

---

## 🌍 Internationalisation (i18n)

### Principes
- L'application est destinée à être **internationalisée**
- Utiliser les mécanismes Django i18n (`gettext`, `ugettext_lazy`)
- Préparer les modèles pour le multi-langue si nécessaire
- Gérer les formats de date/heure selon la locale

### Devises multiples
- Permettre la sélection de devise par l'utilisateur
- Implémenter la **conversion automatique** à l'affichage
- Stocker les montants dans une devise de référence (ex: USD)
- Utiliser un service de taux de change (API externe)

---

## 🔧 Environnement de développement

### Terminal préféré
- **Windows** : Command Prompt (cmd) par défaut
- PowerShell peut être utilisé si jugé plus approprié
- Décision laissée à l'outil AI selon le contexte

### Environnement virtuel Python

#### Activation PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
..\Scripts\Activate
```

#### Activation Command Prompt
```cmd
..\Scripts\activate.bat
```

#### Installation de paquets
- ⚠️ **Toujours** vérifier que l'environnement virtuel est activé
- Utiliser `pip install` uniquement dans le venv
- Mettre à jour `requirements/` selon l'environnement

---

## 📝 Gestion des erreurs

### Format standard
```json
{
  "error": {
    "status_code": 400,
    "error_code": "VALIDATION_ERROR",
    "message": "Les données fournies sont invalides.",
    "details": [
      {
        "field": "email",
        "message": "Adresse email déjà utilisée."
      }
    ]
  }
}
```

### Codes d'erreur normalisés

| Code | Description |
|------|-------------|
| `AUTHENTICATION_FAILED` | Échec d'authentification |
| `INVALID_CREDENTIALS` | Identifiants invalides |
| `TOKEN_EXPIRED` | Token expiré |
| `TOKEN_INVALID` | Token invalide |
| `PERMISSION_DENIED` | Permission refusée |
| `RESOURCE_NOT_FOUND` | Ressource introuvable |
| `VALIDATION_ERROR` | Erreur de validation |
| `RATE_LIMIT_EXCEEDED` | Limite de taux dépassée |
| `SUBSCRIPTION_REQUIRED` | Abonnement Premium requis |
| `LIMIT_REACHED` | Limite atteinte (projets, messages, etc.) |
| `RESOURCE_CONFLICT` | Conflit de ressource |
| `INTERNAL_SERVER_ERROR` | Erreur interne du serveur |

### Codes HTTP

| Code | Utilisation |
|------|-------------|
| 200 | OK - Requête réussie |
| 201 | Created - Ressource créée |
| 204 | No Content - Succès sans contenu |
| 400 | Bad Request - Validation ou requête mal formée |
| 401 | Unauthorized - Authentification requise |
| 403 | Forbidden - Autorisation insuffisante |
| 404 | Not Found - Ressource introuvable |
| 409 | Conflict - Conflit avec l'état actuel |
| 422 | Unprocessable Entity - Données valides mais inutilisables |
| 429 | Too Many Requests - Rate limiting |
| 500 | Internal Server Error - Erreur interne |

---

## 📊 Versionnement de l'API

### Stratégie
- **Versionnement par URL** : `/api/v1/`, `/api/v2/`
- **Changements majeurs** : Nouvelle version (v2, v3)
- **Changements mineurs** : Compatibles avec version existante
- **Correctifs** : Déployés dans version existante

### Compatibilité
- Maintenir compatibilité pour au moins **une version majeure antérieure**
- ❌ Ne jamais supprimer un champ existant dans version mineure
- ✅ Utiliser la dépréciation avant suppression

### Documentation des changements
Maintenir un changelog avec ce format :

```markdown
## v1.2.0 (2025-02-15)

### Ajouts
- Endpoint `/projects/{id}/analytics` pour statistiques détaillées

### Modifications
- Ajout du champ `view_count` dans la réponse `/projects/{id}`

### Corrections
- Correction du tri par date dans `/conversations`

### Déprécié
- Champ `title` dans `/projects` (utiliser `name` à la place)
```

---

## 🧪 Tests

### Stratégie de tests
- **Tests unitaires** : Pour chaque modèle, sérialiseur, vue
- **Tests d'intégration** : Pour les flux complets
- **Framework** : pytest avec django-pytest
- **Coverage** : Minimum 80% de couverture de code

### Organisation
```
app_name/tests/
├── test_models.py
├── test_serializers.py
├── test_views.py
└── test_services.py
```

### Bonnes pratiques
- Utiliser des fixtures pour les données de test
- Tester les cas normaux ET les cas d'erreur
- Isoler les tests (pas de dépendances entre tests)
- Mocker les services externes (Firebase, My-CoolPay)

---

## 🔄 Celery et tâches asynchrones

### Configuration
- **Broker** : Redis
- **Backend** : Redis ou Django DB
- **Guides** : `docs/celery_windows_guide.md`

### Types de tâches
- Envoi de notifications push (Firebase Cloud Messaging)
- Envoi d'emails
- Génération de rapports
- Traitement de médias
- Nettoyage de données

### Bonnes pratiques
- Garder les tâches idempotentes
- Gérer les échecs et retry
- Logger toutes les opérations
- Définir des timeouts appropriés

---

## 🔔 Notifications

### Firebase Cloud Messaging (FCM)
- Utiliser Firebase Admin SDK
- Configuration : `config/firebase-admin-sdk.json`
- Types : Notifications push, in-app, emails

### Préférences utilisateur
- Permettre la gestion des préférences de notification
- Respecter les choix de l'utilisateur
- Catégories : Projets, messages, investissements, système

---

## 📁 Gestion des médias

### Stockage
- **Développement** : Système de fichiers local (`media/`)
- **Production** : CDN ou S3-compatible
- Limites par type d'utilisateur (Standard vs Premium)

### Upload
- Valider types de fichiers (images, vidéos, documents)
- Limiter tailles selon type d'utilisateur
- Générer thumbnails pour images
- Optimiser automatiquement les médias

### Organisation
```
media/
├── projects/
│   ├── images/
│   ├── videos/
│   └── documents/
├── profiles/
│   └── avatars/
└── messages/
    └── attachments/
```

---

## 🔍 Logs et monitoring

### Logs
- Utiliser le système de logging Django
- Niveaux : DEBUG, INFO, WARNING, ERROR, CRITICAL
- Fichiers de logs rotatifs
- Emplacement : `logs/`

### Monitoring production
- Sentry pour tracking des erreurs
- Prometheus pour métriques
- Health checks endpoints

---

## 🤝 Communication avec le frontend

### Principe général
- Les modifications backend doivent **minimiser** l'impact sur le frontend
- Maintenir la rétrocompatibilité autant que possible

### En cas de modifications nécessaires
Fournir une documentation **détaillée, précise et structurée** comprenant :

1. **Endpoints modifiés**
   - Ancienne URL → Nouvelle URL
   - Anciens paramètres → Nouveaux paramètres
   
2. **Formats de données modifiés**
   - Structure ancienne → Structure nouvelle
   - Nouveaux champs requis
   - Champs dépréciés

3. **Nouveaux headers ou authentification**
   
4. **Actions à effectuer côté frontend**
   - Checklist des modifications
   - Ordre d'implémentation
   - Points de validation

5. **Exemples de requêtes/réponses**
   - Avant/après avec curl ou format équivalent

### Format de documentation
```markdown
## Modification : [Titre de la modification]

### Résumé
[Description concise du changement]

### Endpoints affectés
- `GET /api/v1/projects/{id}` - [Nature du changement]

### Changements de structure

#### Avant
```json
{
  "field_old": "value"
}
```

#### Après
```json
{
  "field_new": "value",
  "additional_field": "value"
}
```

### Actions requises frontend
1. [ ] Mettre à jour le modèle de données
2. [ ] Modifier les appels API
3. [ ] Mettre à jour l'affichage UI
4. [ ] Tester les flux utilisateur

### Tests suggérés
- Test 1 : [Description]
- Test 2 : [Description]

### Migration des données
[Si applicable, comment migrer les données existantes]
```

---

## 📚 Documentation

### Documentation API
- Swagger/OpenAPI automatique via DRF
- URL : `/api/docs/`
- Garder à jour avec chaque modification

### Documentation du code
- Docstrings Python pour toutes les fonctions/classes publiques
- Format : Google Style ou NumPy Style
- Exemples d'utilisation dans les docstrings

Exemple :
```python
def create_project(user, project_data):
    """
    Crée un nouveau projet pour un utilisateur.
    
    Args:
        user (User): L'utilisateur propriétaire du projet
        project_data (dict): Les données du projet
        
    Returns:
        Project: L'instance du projet créé
        
    Raises:
        ValidationError: Si les données sont invalides
        PermissionDenied: Si l'utilisateur n'a pas les droits
        
    Example:
        >>> project = create_project(
        ...     user=current_user,
        ...     project_data={'name': 'Mon Projet', 'category': 'tech'}
        ... )
    """
    # Implémentation
```

---

## ⚙️ Configuration Firebase

### Firebase Admin SDK
- Fichier de configuration : `config/firebase-admin-sdk.json`
- **Ne jamais commiter** ce fichier (dans `.gitignore`)
- Utiliser variables d'environnement pour CI/CD

### Services Firebase utilisés
- **Firebase Auth** : Authentification utilisateurs
- **Firebase Cloud Messaging (FCM)** : Notifications push
- **Firebase Storage** : Optionnel pour médias (évaluer vs S3)

### google-services.json
- Fichier utilisé dans le frontend
- Référence pour cohérence auth backend/frontend

---

## 🚀 Déploiement

### Docker
- `Dockerfile` pour l'image backend
- `docker-compose.yml` pour environnement complet
- Multi-stage builds pour optimisation

### CI/CD
- GitHub Actions configuré
- Checks : Linting (flake8, black), tests, sécurité
- Déploiement automatique selon branches

### Scripts utilitaires
- `config/setup_server.sh` : Configuration serveur
- `config/backup.sh` : Backup base de données
- `config/deploy.sh` : Script de déploiement

---

## 📋 Checklist avant commit

- [ ] Code conforme aux conventions de nommage
- [ ] Docstrings ajoutées pour fonctions publiques
- [ ] Tests unitaires écrits et passants
- [ ] Pas de données sensibles dans le code
- [ ] Migrations Django créées si modèles modifiés
- [ ] Documentation API mise à jour si endpoints modifiés
- [ ] Variables d'environnement utilisées pour configs sensibles
- [ ] Logs appropriés ajoutés
- [ ] Gestion des erreurs implémentée
- [ ] Code vérifié avec linter (flake8, pylint)

---

## 🎯 Workflow de développement

### 1. Avant de commencer
- Lire le plan de développement
- Identifier le sprint et la tâche concernés
- Vérifier les spécifications dans `docs/`

### 2. Pendant le développement
- Respecter les conventions de code
- Écrire les tests en parallèle du code
- Commiter régulièrement avec messages clairs
- Documenter le code et les APIs

### 3. Après le développement
- Vérifier tous les tests passent
- Mettre à jour la documentation
- Créer/mettre à jour les migrations
- Fournir une synthèse des modifications

### 4. En cas de modifications frontend nécessaires
- Documenter de façon exhaustive
- Fournir des exemples concrets
- Créer une checklist d'actions
- Proposer un plan de migration

---

## 🐛 Débogage et troubleshooting

### Logs Django
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Message de debug")
logger.info("Information")
logger.warning("Avertissement")
logger.error("Erreur")
logger.critical("Erreur critique")
```

### Debug dans développement
- Activer `DEBUG = True` dans settings development
- Utiliser Django Debug Toolbar
- Consulter les logs dans `logs/`

### Outils utiles
- `python manage.py shell` : Console Django interactive
- `python manage.py dbshell` : Console base de données
- `python manage.py check` : Vérification configuration

---

## 💡 Bonnes pratiques spécifiques

### Abonnements et limites
- **Standard** : Limites définies (projets, messages, etc.)
- **Premium** : Limites étendues ou illimitées
- Valider les limites à chaque opération
- Messages d'erreur clairs pour limites atteintes

### Sécurité des données
- Valider TOUTES les entrées utilisateur
- Utiliser les validateurs Django
- Sanitiser les données avant stockage
- Utiliser les permissions DRF appropriées

### Performance
- Utiliser `select_related()` et `prefetch_related()` pour optimiser les requêtes
- Paginer les résultats (DRF PageNumberPagination)
- Mettre en cache les requêtes fréquentes (Redis)
- Indexer les champs recherchés fréquemment

### Modèles de données
- Toujours inclure `created_at` et `updated_at`
- Utiliser UUID comme identifiants primaires
- Soft delete plutôt que hard delete (flag `is_deleted`)
- Ajouter des contraintes de base de données

---

## 📖 Ressources et références

### Documentation interne
Tous les documents dans `docs/` :
- Plans de développement
- Architecture technique
- Contrats API
- Guides d'intégration
- Configurations

### Documentation externe
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Celery Documentation](https://docs.celeryproject.org/)
- My-CoolPay API Docs (voir `docs/My-CoolPay API Docs.pdf`)

---

## 🎨 Style de code

### Python
- **PEP 8** : Standard de style Python
- **Formatage** : Black (ligne max 88 caractères)
- **Linting** : flake8, pylint
- **Imports** : isort pour organisation

### Ordre des imports
```python
# Standard library
import os
import sys

# Third-party
import django
from rest_framework import serializers

# Local
from apps.users.models import User
from apps.core.utils import custom_function
```

### Docstrings
```python
class MyClass:
    """
    Brève description de la classe.
    
    Description plus détaillée si nécessaire.
    
    Attributes:
        attribute1: Description de l'attribut
        attribute2: Description de l'attribut
    """
    
    def my_method(self, param1, param2):
        """
        Brève description de la méthode.
        
        Args:
            param1: Description du paramètre
            param2: Description du paramètre
            
        Returns:
            Description du retour
            
        Raises:
            ExceptionType: Quand elle est levée
        """
        pass
```

---

## 🔒 Sécurité - Checklist

### Authentification et autorisation
- [ ] JWT correctement implémenté avec expiration
- [ ] Refresh tokens gérés sécuritairement
- [ ] Permissions DRF utilisées sur tous les endpoints
- [ ] Firebase Auth intégré correctement

### Validation des données
- [ ] Toutes les entrées utilisateur validées
- [ ] Sérialiseurs DRF avec validations appropriées
- [ ] Contraintes de base de données définies
- [ ] Sanitization des données HTML/JavaScript

### Protection contre les attaques
- [ ] Protection CSRF activée
- [ ] Rate limiting implémenté
- [ ] SQL injection prévenue (ORM Django)
- [ ] XSS prévenu (échappement automatique templates)

### Données sensibles
- [ ] Mots de passe hashés (jamais en clair)
- [ ] Clés API dans variables d'environnement
- [ ] HTTPS obligatoire en production
- [ ] Logs ne contiennent pas de données sensibles

---

## 🌟 Synthèse des points clés

### À toujours faire
✅ Suivre le plan de développement
✅ Vérifier la conformité aux spécifications
✅ Poser des questions si incertitude
✅ Fournir une synthèse après chaque action
✅ Penser internationalisation et multi-devises
✅ Minimiser l'impact sur le frontend
✅ Documenter exhaustivement
✅ Écrire des tests
✅ Respecter les conventions de nommage
✅ Utiliser l'environnement virtuel Python

### À ne jamais faire
❌ Faire des suppositions sans validation
❌ Ignorer le plan de développement
❌ Commiter des données sensibles
❌ Supprimer des champs API sans dépréciation
❌ Oublier les migrations Django
❌ Négliger la sécurité
❌ Casser la rétrocompatibilité sans prévenir
❌ Installer des packages hors du venv

---

## 📞 Support et questions

En cas de questions ou d'ambiguïtés :
1. Consulter la documentation dans `docs/`
2. Vérifier le code existant pour patterns
3. **Poser des questions** plutôt que deviner
4. Proposer des solutions avec justifications

---

**Version** : 1.0  
**Dernière mise à jour** : Janvier 2026  
**Maintenu par** : Équipe Backend VentureLink

---

*Ces instructions sont évolutives et doivent être mises à jour au fur et à mesure de l'avancement du projet.*
