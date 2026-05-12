#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Crear carpeta media persistente
mkdir -p /var/data/media

# Copiar media inicial desde GitHub hacia el Disk
cp -rn media/. /var/data/media/ || true