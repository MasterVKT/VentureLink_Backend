#!/bin/bash
# Script de sauvegarde pour VentureLink API

set -e  # Arrêter en cas d'erreur

# Variables d'environnement
APP_DIR=${APP_DIR:-"/app"}
BACKUP_DIR=${BACKUP_DIR:-"$APP_DIR/backups"}
DB_NAME=${DB_NAME:-"venture_link"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-""}
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
S3_BACKUP_BUCKET=${S3_BACKUP_BUCKET:-""}
KEEP_LOCAL_BACKUPS=${KEEP_LOCAL_BACKUPS:-7}  # Nombre de sauvegardes locales à conserver

# Créer le dossier de sauvegarde s'il n'existe pas
mkdir -p $BACKUP_DIR

# Définir le nom du fichier de sauvegarde avec la date et l'heure
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
COMPRESSED_BACKUP_FILE="${BACKUP_FILE}.gz"

echo "---- Sauvegarde de la base de données VentureLink ----"
echo "Base de données : $DB_NAME"
echo "Fichier de sauvegarde : $COMPRESSED_BACKUP_FILE"

# Exporter les variables d'environnement pour pg_dump
export PGPASSWORD=$DB_PASSWORD

# Créer la sauvegarde
echo "Création de la sauvegarde..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -F p > $BACKUP_FILE

# Compresser la sauvegarde
echo "Compression de la sauvegarde..."
gzip $BACKUP_FILE

# Si une configuration S3 est fournie, téléverser la sauvegarde sur S3
if [ -n "$S3_BACKUP_BUCKET" ]; then
    echo "Téléversement de la sauvegarde sur S3..."
    aws s3 cp $COMPRESSED_BACKUP_FILE "s3://$S3_BACKUP_BUCKET/${DB_NAME}/"
    
    if [ $? -eq 0 ]; then
        echo "Téléversement sur S3 réussi."
    else
        echo "Erreur lors du téléversement sur S3."
    fi
fi

# Nettoyer les anciennes sauvegardes locales
echo "Nettoyage des anciennes sauvegardes locales..."
ls -t $BACKUP_DIR/*.gz | tail -n +$((KEEP_LOCAL_BACKUPS+1)) | xargs -r rm

echo "Sauvegarde terminée avec succès!" 