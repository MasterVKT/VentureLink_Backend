# 🔧 Guide de Dépannage - Authentification VentureLink

## Problème : Impossible de se connecter avec le compte superutilisateur

---

## ✅ Solution Rapide (5 minutes)

### Étape 1 : Créer le compte superutilisateur

Ouvrez un terminal et exécutez :

```bash
# Se placer dans le dossier Backend
cd c:\Users\USER\VentureLink\VentureLink_BackEnd

# Activer le virtual environment
venv\Scripts\activate

# Exécuter le script de création
python create_superuser.py
```

**Informations de connexion par défaut :**
- 📧 Email : `admin@venturelink.com`
- 🔑 Mot de passe : `Admin123!`

---

### Étape 2 : Vérifier que le Backend est en cours d'exécution

```bash
# Dans le dossier VentureLink_BackEnd (avec venv activé)
python manage.py runserver
```

Le serveur doit afficher :
```
Starting development server at http://127.0.0.1:8000/
```

---

### Étape 3 : Tester l'API avec Postman ou curl

**Tester l'authentification :**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@venturelink.com\",\"password\":\"Admin123!\"}"
```

**Réponse attendue :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Étape 4 : Vérifier la configuration Flutter

Dans votre application Flutter, assurez-vous que l'URL de l'API est correcte :

**Fichier :** `lib/core/config/app_config.dart`

```dart
static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
```

⚠️ **Important pour Android :**
- `127.0.0.1` ou `localhost` ne fonctionne PAS sur émulateur Android
- Utilisez `10.0.2.2` à la place :

```dart
static String get _devApiBaseUrl {
  if (kIsWeb) {
    return 'http://127.0.0.1:8000';
  }
  
  if (Platform.isAndroid) {
    return 'http://10.0.2.2:8000';  // ← Important!
  }
  
  return 'http://127.0.0.1:8000';
}
```

---

## 🔍 Diagnostic Détaillé

### Problème 1 : Erreur de connexion réseau

**Symptôme :** "Erreur de connexion réseau" ou "Impossible de se connecter au serveur"

**Causes possibles :**
1. Le serveur Django n'est pas en cours d'exécution
2. Le port 8000 est déjà utilisé
3. Problème de firewall

**Solution :**

```bash
# Vérifier si le serveur tourne
netstat -ano | findstr :8000

# Si rien n'apparaît, lancer le serveur
cd c:\Users\USER\VentureLink\VentureLink_BackEnd
venv\Scripts\activate
python manage.py runserver

# Si le port est occupé, tuer le processus
taskkill /F /PID <PID>
```

---

### Problème 2 : Erreur d'authentification (401)

**Symptôme :** "Identifiants invalides" ou "Erreur d'authentification"

**Causes possibles :**
1. Le compte n'existe pas dans la base de données
2. Le mot de passe est incorrect
3. Le compte est désactivé

**Solution :**

```bash
# Se connecter à la base de données
cd c:\Users\USER\VentureLink\VentureLink_BackEnd
venv\Scripts\activate
python manage.py shell

# Vérifier l'utilisateur
from django.contrib.auth import get_user_model
User = get_user_model()

# Voir tous les utilisateurs
for u in User.objects.all():
    print(f"{u.email} - Actif: {u.is_active} - Staff: {u.is_staff} - Superuser: {u.is_superuser}")

# Vérifier un utilisateur spécifique
user = User.objects.get(email="admin@venturelink.com")
print(f"Actif: {user.is_active}")
print(f"Staff: {user.is_staff}")
print(f"Superuser: {user.is_superuser}")

# Réinitialiser le mot de passe
user.set_password("Admin123!")
user.save()
```

---

### Problème 3 : Erreur 500 du serveur

**Symptôme :** "Erreur du serveur" ou "Internal Server Error"

**Solution :**

1. **Vérifier les logs Django :**

```bash
# Lancer le serveur en mode debug
python manage.py runserver --verbosity 2
```

2. **Vérifier la base de données :**

```bash
# Appliquer les migrations
python manage.py migrate

# Vérifier l'état des migrations
python manage.py showmigrations
```

3. **Vérifier les variables d'environnement :**

Le fichier `.env` doit contenir :

```env
DEBUG=True
SECRET_KEY=12345678
DATABASE_NAME=venturelink_db
DATABASE_USER=venturelink_user
DATABASE_PASSWORD=eeeeee
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

---

### Problème 4 : CORS Error (Flutter Web)

**Symptôme :** "Access to XMLHttpRequest has been blocked by CORS policy"

**Solution :**

Dans `venture_link_project/settings.py`, ajoutez :

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:50000",  # Flutter Web
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 🧪 Tests de Validation

### Test 1 : Vérifier la base de données

```bash
cd c:\Users\USER\VentureLink\VentureLink_BackEnd
venv\Scripts\activate
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Compter les utilisateurs
print(f"Total utilisateurs: {User.objects.count()}")

# Vérifier le superutilisateur
admin = User.objects.filter(email="admin@venturelink.com").first()
if admin:
    print(f"✅ Admin trouvé: {admin.email}")
    print(f"   Actif: {admin.is_active}")
    print(f"   Staff: {admin.is_staff}")
    print(f"   Superuser: {admin.is_superuser}")
else:
    print("❌ Admin non trouvé")
```

---

### Test 2 : Tester l'API Projects

```bash
# Tester sans authentification (doit fonctionner pour liste publique)
curl http://127.0.0.1:8000/api/v1/projects/

# Tester avec authentification
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@venturelink.com\",\"password\":\"Admin123!\"}"

# Utiliser le token pour accéder aux projets
curl http://127.0.0.1:8000/api/v1/projects/ \
  -H "Authorization: Bearer <TOKEN_ACCESS>"
```

---

### Test 3 : Tester l'application Flutter

1. **Lancer l'application Flutter :**

```bash
cd c:\Users\USER\VentureLink\VentureLink_Frontend
flutter run
```

2. **Dans l'application :**
   - Allez à l'écran de connexion
   - Entrez : `admin@venturelink.com`
   - Mot de passe : `Admin123!`
   - Cliquez sur "Se connecter"

3. **Vérifier les logs Flutter :**

```bash
# Dans un autre terminal
flutter logs
```

---

## 📝 Commandes Utiles

### Backend Django

```bash
# Activer le virtual environment
cd c:\Users\USER\VentureLink\VentureLink_BackEnd
venv\Scripts\activate

# Lancer le serveur
python manage.py runserver

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur manuellement
python manage.py createsuperuser

# Voir les logs
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)
```

### Frontend Flutter

```bash
# Nettoyer le projet
flutter clean

# Récupérer les dépendances
flutter pub get

# Lancer l'application
flutter run

# Analyser le code
flutter analyze

# Build pour test
flutter build apk --debug
```

---

## 🎯 Checklist de Résolution

- [ ] Backend Django en cours d'exécution sur le port 8000
- [ ] Base de données PostgreSQL accessible
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Compte superutilisateur créé (`python create_superuser.py`)
- [ ] URL API correcte dans Flutter (`http://127.0.0.1:8000` ou `http://10.0.2.2:8000`)
- [ ] Firewall n'empêche pas la connexion
- [ ] Logs Django ne montrent pas d'erreurs
- [ ] Logs Flutter ne montrent pas d'erreurs réseau

---

## 🆘 En Cas de Problème Persistant

### 1. Redémarrer la base de données PostgreSQL

```bash
# Windows - Services
services.msc
# Chercher "postgresql" et redémarrer
```

### 2. Réinitialiser complètement la base de données

```bash
cd c:\Users\USER\VentureLink\VentureLink_BackEnd
venv\Scripts\activate

# Supprimer toutes les tables
python manage.py dbshell
>>> DROP SCHEMA public CASCADE;
>>> CREATE SCHEMA public;
>>> \q

# Recréer les tables
python manage.py migrate

# Créer le superutilisateur
python create_superuser.py
```

### 3. Vérifier la connectivité réseau

```bash
# Tester si le port 8000 est accessible
telnet 127.0.0.1 8000

# Ou avec PowerShell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8000
```

---

## 📞 Support

Si le problème persiste, fournissez les informations suivantes :

1. **Logs Django** (copier-coller depuis le terminal)
2. **Logs Flutter** (`flutter logs`)
3. **Résultat de** `python create_superuser.py`
4. **Résultat de** `curl http://127.0.0.1:8000/api/v1/projects/`

---

**Document créé le :** Mardi 3 Mars 2026  
**Projet :** VentureLink  
**Version :** 1.0
