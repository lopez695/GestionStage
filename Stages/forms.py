from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .models import (
    CustomUser, Offre, Candidature, Message, Rapport, 
    CommentaireRapport, Etudiant, Enseignant, Entreprise,
    Stage, DocumentStage, VisiteStage, EvaluationStage, Task
)

User = get_user_model()

# Formulaires d'authentification
class ConnexionForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur", 
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Mot de passe"
    )

class InscriptionForm(UserCreationForm):
    telephone = forms.CharField(
        max_length=20, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    # Champs spécifiques pour les étudiants
    numero_etudiant = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    promotion = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    specialite = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'role', 'telephone', 'photo',
            'numero_etudiant', 'promotion', 'specialite',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'ETUDIANT':
            for field_name in ['numero_etudiant', 'promotion', 'specialite']:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, "Ce champ est obligatoire pour les étudiants.")
        return cleaned_data

# Formulaires de profil
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'photo', 'cv', 'adresse']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'cv': forms.FileInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EtudiantForm(forms.ModelForm):
    class Meta:
        model = Etudiant
        fields = [
            'telephone', 'adresse', 'ville', 'numero_etudiant', 
            'promotion', 'specialite', 'enseignant_referent', 
            'etablissement', 'niveau'
        ]
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_etudiant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 12345678'
            }),
            'promotion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2023-2024'
            }),
            'specialite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Informatique'
            }),
            'enseignant_referent': forms.Select(attrs={'class': 'form-select'}),
            'etablissement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Université Paris'
            }),
            'niveau': forms.Select(
                attrs={'class': 'form-select'},
                choices=Etudiant.NIVEAU_CHOICES
            ),
        }
        labels = {
            'numero_etudiant': "Numéro étudiant",
            'promotion': "Promotion",
            'specialite': "Spécialité",
            'enseignant_referent': "Enseignant référent",
            'etablissement': "Établissement",
            'niveau': "Niveau d'étude"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['enseignant_referent'].queryset = Enseignant.objects.all().order_by('user__last_name')
        self.fields['enseignant_referent'].required = False
        self.fields['etablissement'].required = False

class EnseignantForm(forms.ModelForm):
    class Meta:
        model = Enseignant
        fields = ['photo', 'nom', 'prenom', 'departement', 'mail', 'bureau', 'grade', 'telephone']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'departement': forms.TextInput(attrs={'class': 'form-control'}),
            'mail': forms.EmailInput(attrs={'class': 'form-control'}),
            'bureau': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['nom', 'secteur', 'adresse', 'site_web', 'logo', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'secteur': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_site_web(self):
        site_web = self.cleaned_data.get('site_web')
        if site_web:
            validator = URLValidator()
            try:
                validator(site_web)
            except:
                raise forms.ValidationError("Veuillez entrer une URL valide")
        return site_web

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Offre

class OffreForm(forms.ModelForm):
    class Meta:
        model = Offre
        exclude = ['entreprise', 'date_publication']  # On exclut ces champs auto-gérés
        widgets = {
            'date_limite': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'competences_requises': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs non obligatoires
        self.fields['remuneration'].required = False
        self.fields['date_debut'].required = False
        
        # Ajout des classes Bootstrap à tous les champs
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'
    
    def clean_date_limite(self):
        date_limite = self.cleaned_data.get('date_limite')
        if date_limite and date_limite < timezone.now().date():
            raise ValidationError("La date limite ne peut pas être dans le passé")
        return date_limite
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_limite = cleaned_data.get('date_limite')
        
        if date_debut and date_limite and date_debut > date_limite:
            raise ValidationError("La date de début doit être antérieure à la date limite")
        
        return cleaned_data

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['cv', 'lettre_motivation', 'commentaire']
        widgets = {
            'cv': forms.FileInput(attrs={'class': 'form-control'}),
            'lettre_motivation': forms.FileInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('cv') and not cleaned_data.get('lettre_motivation'):
            raise forms.ValidationError("Vous devez fournir au moins un fichier (CV ou lettre de motivation).")
        return cleaned_data

from django import forms
from .models import Stage

class StageForm(forms.ModelForm):
    candidature = forms.ModelChoiceField(
        queryset=Candidature.objects.all(),
        required=False)
    class Meta:
        model = Stage
        fields = '__all__'
        widgets = {
            'candidature': forms.Select(attrs={'class': 'form-select'}),
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'offre': forms.Select(attrs={'class': 'form-select'}),
            'sujet': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tuteur_entreprise': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RapportForm(forms.ModelForm):
    class Meta:
        model = Rapport
        fields = ['fichier', 'statut', 'commentaires']
        widgets = {
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CommentaireForm(forms.ModelForm):
    class Meta:
        model = CommentaireRapport
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = DocumentStage
        fields = ['type_document', 'nom', 'fichier']
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }

class VisiteForm(forms.ModelForm):
    class Meta:
        model = VisiteStage
        fields = ['type_visite', 'date', 'notes']
        widgets = {
            'type_visite': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = EvaluationStage
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 20, 
                'step': 0.5
            }),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

# Formulaires divers
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['destinataire', 'contenu']
        widgets = {
            'destinataire': forms.Select(attrs={'class': 'form-select'}),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Écris ton message ici...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['destinataire'].queryset = User.objects.exclude(id=user.id)

class ContactEntrepriseForm(forms.Form):
    nom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=100
    )
    prenom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=100,
        required=False
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    sujet = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=200
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }