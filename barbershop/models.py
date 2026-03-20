from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('gerant', 'Gérant'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='gerant')

class Client(models.Model):

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, unique=True)
    adresse = models.CharField(max_length=200, blank=True, null=True)
    date_inscription = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Service(models.Model):

    nom = models.CharField(max_length=100)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    prix = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nom


class FileAttente(models.Model):
    STATUS_CHOICES = [
        ('en_file', 'En File'),
        ('termine', 'Terminé'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=[('en_file','En File'), ('sorti','Sorti')],
        default='en_file'
    )
    date_creation = models.DateTimeField(default=timezone.now)
    paiement_effectue = models.BooleanField(default=False)  # <-- nouveau champ


    def __str__(self):
        return f"{self.client} - {self.service}"


class Paiement(models.Model):

    file = models.ForeignKey(FileAttente, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=8, decimal_places=2)
    date_paiement = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='non_paye')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Dès qu'un paiement est effectue, on met à jour FileAttente
        if self.status == 'effectue':
            self.file.paiement_effectue = True
            self.file.save()

    def __str__(self):
        return f"{self.file.client} - {self.montant}"
    
class SalonSettings(models.Model):
    nom_salon = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    couleur_theme = models.CharField(max_length=7, default="#0d6efd")  # couleur bootstrap
    heures_ouverture = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom_salon