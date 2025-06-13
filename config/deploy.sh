#!/bin/bash
# Script de déploiement pour VentureLink API

set -e  # Arrêter en cas d'erreur

# Variables d'environnement
APP_DIR=${APP_DIR:-"/app"}
VENV_DIR=${VENV_DIR:-"$APP_DIR/venv"}
DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"venture_link_project.settings.production"}
LOG_DIR=${LOG_DIR:-"$APP_DIR/logs"}

# Créer les dossiers nécessaires
mkdir -p $LOG_DIR

echo "---- Déploiement de VentureLink API ----"
echo "Dossier application : $APP_DIR"
echo "Dossier venv : $VENV_DIR"
echo "Settings Django : $DJANGO_SETTINGS_MODULE"
echo "Dossier logs : $LOG_DIR"

# Se déplacer dans le dossier de l'application
cd $APP_DIR

# Activer l'environnement virtuel
if [ -d "$VENV_DIR" ]; then
    echo "Activation de l'environnement virtuel..."
    source $VENV_DIR/bin/activate
else
    echo "Création d'un nouvel environnement virtuel..."
    python3 -m venv $VENV_DIR
    source $VENV_DIR/bin/activate
    
    echo "Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements/production.txt
fi

# Vérifier les dépendances
echo "Mise à jour des dépendances..."
pip install -r requirements/production.txt

# Exporter les variables d'environnement
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Exécuter les migrations
echo "Exécution des migrations..."
python manage.py migrate --noinput

# Vérifier l'état du projet
echo "Vérification de l'état du projet..."
python manage.py check --deploy

# Démarrer Gunicorn
echo "Démarrage de Gunicorn..."
gunicorn venture_link_project.wsgi:application -c config/gunicorn.conf.py

echo "Déploiement terminé !" 