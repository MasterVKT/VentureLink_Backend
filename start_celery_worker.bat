@echo off
echo Démarrage du worker Celery pour VentureLink avec configuration Windows...
call ..\Scripts\activate
celery -A celery_config worker --pool=solo --concurrency=1 --without-gossip --without-mingle --without-heartbeat -l info 