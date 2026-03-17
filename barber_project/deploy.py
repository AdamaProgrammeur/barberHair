# deploy.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barber_project.settings')
django.setup()

from django.core.management import call_command

# Crée les migrations
call_command('makemigrations')
call_command('migrate')

print("✅ Migrations appliquées avec succès !")