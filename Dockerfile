FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installer les dépendances
COPY requirements/production.txt requirements/base.txt requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copier le projet
COPY . .

# Créer l'utilisateur non-root
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Collecter les fichiers statiques
RUN python manage.py collectstatic --no-input

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD gunicorn --bind 0.0.0.0:8000 venture_link_project.wsgi:application 