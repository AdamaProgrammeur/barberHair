from django import forms
from .models import Client, Service, FileAttente, Paiement



class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'telephone', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom', 'required': True}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre prénom', 'required': True}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone', 'required': True}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre adresse', 'required': True}),
        }

    
    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        qs = Client.objects.filter(telephone=telephone)
        
        # Si modification, on exclut l'instance actuelle
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise forms.ValidationError("Un client avec ce numéro existe déjà !")
        return telephone

from django import forms
from .models import SalonSettings

class SalonSettingsForm(forms.ModelForm):
    class Meta:
        model = SalonSettings
        fields = '__all__'
        widgets = {
            'heures_ouverture': forms.TextInput(attrs={'placeholder': 'Ex: 08:00 - 20:00'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }




class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['nom', 'prix', 'image']

        widgets = {

            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du service',
                'required': True
            }),

            'prix': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prix du service',
                'required': True
            }),

            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),

        }

class FileAttenteForm(forms.ModelForm):
    class Meta:
        model = FileAttente
        fields = ['client', 'service', 'date_creation']
        widgets = {
            'date_creation': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }




class PaiementForm(forms.ModelForm):

    class Meta:
        model = Paiement
        fields = ['file', 'montant', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # afficher seulement les files non payées
        self.fields['file'].queryset = FileAttente.objects.filter(
            paiement__status='non_paye'
        ) | FileAttente.objects.filter(paiement__isnull=True)

        self.fields['file'].widget.attrs.update({'class': 'form-select'})
        self.fields['montant'].widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-select'})