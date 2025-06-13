#!/bin/bash
# Script de configuration du serveur pour VentureLink API

set -e  # Arrêter en cas d'erreur

echo "===== Configuration du serveur VentureLink API ====="

# Vérifier les privilèges root
if [ "$(id -u)" != "0" ]; then
   echo "Ce script doit être exécuté en tant que root" 1>&2
   exit 1
fi

# Variables
APP_DIR=${APP_DIR:-"/app"}
APP_USER=${APP_USER:-"venturelink"}
APP_GROUP=${APP_GROUP:-"venturelink"}
DOMAIN=${DOMAIN:-"api.venturelink.com"}
DB_NAME=${DB_NAME:-"venture_link"}
DB_USER=${DB_USER:-"venturelink_user"}
DB_PASSWORD=${DB_PASSWORD:-"$(openssl rand -base64 12)"}

echo "Domaine: $DOMAIN"
echo "Dossier application: $APP_DIR"
echo "Utilisateur: $APP_USER"

# Mettre à jour le système
echo "Mise à jour du système..."
apt-get update
apt-get upgrade -y

# Installer les dépendances
echo "Installation des dépendances..."
apt-get install -y \
    python3 python3-venv python3-dev \
    postgresql postgresql-contrib \
    nginx redis-server \
    certbot python3-certbot-nginx \
    git curl build-essential \
    supervisor fail2ban \
    libpq-dev

# Créer l'utilisateur et le groupe
echo "Création de l'utilisateur $APP_USER..."
if ! id -u $APP_USER > /dev/null 2>&1; then
    useradd -m -s /bin/bash $APP_USER
    groupadd -f $APP_GROUP
    usermod -a -G $APP_GROUP $APP_USER
fi

# Créer les dossiers nécessaires
echo "Création des dossiers..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/media
mkdir -p $APP_DIR/staticfiles
mkdir -p $APP_DIR/backups

# Configurer les permissions
echo "Configuration des permissions..."
chown -R $APP_USER:$APP_GROUP $APP_DIR
chmod -R 755 $APP_DIR

# Configurer PostgreSQL
echo "Configuration de PostgreSQL..."
sudo -u postgres bash << EOF
psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
psql -c "CREATE DATABASE $DB_NAME WITH OWNER $DB_USER;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
EOF

echo "Mot de passe PostgreSQL généré: $DB_PASSWORD"
echo "Notez ce mot de passe en lieu sûr!"

# Configurer Nginx
echo "Configuration de Nginx..."
if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
    rm /etc/nginx/sites-available/$DOMAIN
fi

# Copier la configuration Nginx
cp $APP_DIR/config/nginx/venturelink.conf /etc/nginx/sites-available/$DOMAIN
sed -i "s/api.venturelink.com/$DOMAIN/g" /etc/nginx/sites-available/$DOMAIN

# Activer le site
if [ -f "/etc/nginx/sites-enabled/$DOMAIN" ]; then
    rm /etc/nginx/sites-enabled/$DOMAIN
fi
ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Configurer SSL avec Certbot
echo "Configuration de SSL avec Certbot..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

# Configurer systemd
echo "Configuration des services systemd..."
cp $APP_DIR/config/systemd/venturelink-api.service /etc/systemd/system/
cp $APP_DIR/config/systemd/venturelink-celery.service /etc/systemd/system/
cp $APP_DIR/config/systemd/venturelink-celerybeat.service /etc/systemd/system/

# Recharger systemd
systemctl daemon-reload

# Configurer les sauvegardes automatiques
echo "Configuration des sauvegardes automatiques..."
(crontab -l 2>/dev/null; echo "0 3 * * * $APP_DIR/config/backup.sh > /dev/null 2>&1") | crontab -

# Configurer fail2ban pour protéger Nginx
echo "Configuration de fail2ban..."
cat > /etc/fail2ban/jail.d/nginx-http-auth.conf << EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
EOF

# Redémarrer les services
echo "Redémarrage des services..."
systemctl restart postgresql
systemctl restart redis-server
systemctl restart nginx
systemctl restart fail2ban

echo "===== Configuration terminée ====="
echo "L'API VentureLink est prête à être déployée sur $DOMAIN"
echo "Mot de passe PostgreSQL: $DB_PASSWORD"
echo ""
echo "Pour déployer l'application, exécutez:"
echo "sudo -u $APP_USER $APP_DIR/config/deploy.sh"
echo ""
echo "Pour démarrer les services, exécutez:"
echo "systemctl start venturelink-api venturelink-celery venturelink-celerybeat"
echo ""
echo "Pour activer les services au démarrage, exécutez:"
echo "systemctl enable venturelink-api venturelink-celery venturelink-celerybeat" 