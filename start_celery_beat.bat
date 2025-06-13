@echo off
echo Démarrage de Celery Beat pour VentureLink avec configuration Windows...
call ..\Scripts\activate
celery -A celery_config beat -l info --max-interval=10.0 