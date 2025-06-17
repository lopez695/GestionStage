from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    ETUDIANT = 'ETUDIANT'
    ENTREPRISE = 'ENTREPRISE'
    ENSEIGNANT = 'ENSEIGNANT'

    ROLE_CHOICES = [
        (ETUDIANT, 'Étudiant'),
        (ENTREPRISE, 'Entreprise'),
        (ENSEIGNANT, 'Enseignant'),
    ]
    
    est_visible_enseignant = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='photos_profil/', null=True, blank=True)
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)
    adresse = models.CharField(max_length=255, blank=True)  # Ajout de max_length manquant
    is_online = models.BooleanField(default=False) 
    entreprise = models.OneToOneField(
        'Entreprise', 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='utilisateur'
    )
    
    def get_full_name(self):
        return f"{self.nom} {self.prenom}".strip()

    @property
    def est_entreprise(self):
        return hasattr(self, 'entreprise') and self.entreprise is not None

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def nom_complet(self): # If you prefer this name
        return self.get_full_name()
    
    



class Etudiant(models.Model):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'), 
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('D', 'Doctorat'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100, default="Nom non spécifié", verbose_name="Nom de famille")
    prenom = models.CharField(max_length=100, default="Prénom non spécifié", verbose_name="Prénom")
    photo = models.ImageField(upload_to='etudiants_photos/', null=True, blank=True)
    numero_etudiant = models.CharField(max_length=20, unique=True)
    promotion = models.CharField(max_length=50, blank=True, null=True)
    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    enseignant_referent = models.ForeignKey(
        'Enseignant', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Enseignant référent"
    )
    etablissement = models.CharField(
        max_length=100, 
        default="Non renseigné",
        verbose_name="Établissement"
    )
    niveau = models.CharField(
        max_length=2,
        choices=NIVEAU_CHOICES,
        default='L1',
        verbose_name="Niveau d'étude"
    )

    def __str__(self):
        niveau_display = dict(self.NIVEAU_CHOICES).get(self.niveau, 'Inconnu')
        return f"{self.user.get_full_name()} ({self.numero_etudiant})- {niveau_display}"

class Enseignant(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    photo = models.ImageField(
        upload_to='enseignants_photos/',
        blank=True,
        null=True,
        verbose_name="Photo de profil")
    departement = models.CharField(max_length=100)
    mail = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Adresse e-mail")
    bureau = models.CharField(max_length=50, blank=True)
    grade = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    nom = models.CharField(
        max_length=100,
        default="Nom non spécifié",
        verbose_name="Nom de famille"
    )
    prenom = models.CharField(
        max_length=100,
        default="Prénom non spécifié",
        verbose_name="Prénom"
    )
    
    def __str__(self):
        return f"{self.nom.upper()} {self.prenom.capitalize()}"

class Entreprise(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='entreprise_profile')
    nom = models.CharField(max_length=100)
    secteur = models.CharField(max_length=100)
    adresse = models.CharField(max_length=100)
    email = models.EmailField(
        verbose_name="Email de contact",
        blank=True,
        null=True
    )
    site_web = models.URLField(blank=True)
    logo = models.ImageField(upload_to='logos_entreprises/', null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Offre(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='offres')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    competences_requises = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    date_limite = models.DateField()
    est_active = models.BooleanField(default=True)
    duree_semaines = models.PositiveIntegerField(help_text="Durée en semaines")
    
    TYPE_STAGE_CHOICES = [
        ('plein_temps', 'Plein temps'),
        ('partiel', 'Partiel'), 
        ('alternance', 'Alternance')
    ]
    type_stage = models.CharField(
        max_length=50,
        choices=TYPE_STAGE_CHOICES,
        default='plein_temps'
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début prévisionnelle",
        null=True,
        blank=True
    )
    
    remuneration = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Rémunération mensuelle"
    )

    class Meta:
        ordering = ['-date_publication']

class Candidature(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    ACCEPTEE = 'ACCEPTEE'
    REFUSEE = 'REFUSEE'

    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (ACCEPTEE, 'Acceptée'),
        (REFUSEE, 'Refusée'),
    ]
    candidature = models.OneToOneField(
        'Candidature',  # Assurez-vous que Candidature est importé ou correctement référencé
        on_delete=models.CASCADE,
        related_name='stage',
        null=True,
        blank=True
    )

    etudiant = models.ForeignKey(
        'Etudiant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True, 
        related_name='candidatures'
    )
    offre = models.ForeignKey(Offre, on_delete=models.CASCADE, related_name='candidatures')
    cv = models.FileField(upload_to='candidatures/cv/', max_length=250, blank=True, null=True)
    lettre_motivation = models.FileField(upload_to='candidatures/lettres/', max_length=250, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=EN_ATTENTE)
    date_postulation = models.DateTimeField(auto_now_add=True)
    date_acceptation = models.DateTimeField(auto_now_add=True, null=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"{self.etudiant.user.get_full_name()} - {self.offre.titre}"

    class Meta:
        unique_together = ['etudiant', 'offre']

class Stage(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    tuteur_entreprise = models.CharField(max_length=255, null=True, blank=True)
    offre = models.ForeignKey(Offre, on_delete=models.CASCADE)
    sujet = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    tuteur_entreprise = models.CharField(max_length=255, blank=True, null=True)
    valide_par_admin = models.BooleanField(default=False)  # <- EXISTE DANS LE MODELE
    date_validation = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now, editable=False)


class Rapport(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    stage = models.OneToOneField(Stage, on_delete=models.CASCADE, related_name='rapport_stage')
    fichier = models.FileField(upload_to='rapports/')
    date_soumission = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    commentaires = models.TextField(blank=True)
    note = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )

    def __str__(self):
        return f"Rapport de {self.stage.candidature.etudiant.user.get_full_name()}"

    class Meta:
        ordering = ['-date_soumission']

class CommentaireRapport(models.Model):
    rapport = models.ForeignKey(Rapport, on_delete=models.CASCADE, related_name='commentaires_rapport')
    auteur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur rapport {self.rapport.id}"

class Message(models.Model):
    expediteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_recus')
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def get_sender_name(self):
        return f"{self.expediteur.first_name} {self.expediteur.last_name}"
    
    def is_read(self):
        return self.lu

    class Meta:
        ordering = ['date_envoi']
    def __str__(self):
        return f"{self.expediteur} → {self.destinataire} : {self.contenu[:30]}"    

    

class Notification(models.Model):
    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    lien = models.CharField(max_length=200, blank=True)
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.utilisateur.username}: {self.message[:50]}"

    class Meta:
        ordering = ['-date_creation']

class DocumentStage(models.Model):
    TYPE_CHOICES = [
        ('convention', 'Convention de stage'),
        ('rapport', 'Rapport de stage'),
        ('journal', 'Journal de bord'),
        ('autre', 'Autre document'),
    ]

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nom = models.CharField(max_length=100)
    fichier = models.FileField(upload_to='documents_stage/')
    date_upload = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def type_icon(self):
        icons = {
            'convention': 'file-contract',
            'rapport': 'file-alt',
            'journal': 'book',
            'autre': 'file'
        }
        return icons.get(self.type_document, 'file')

    @property
    def type_color(self):
        colors = {
            'convention': 'primary',
            'rapport': 'success',
            'journal': 'info',
            'autre': 'secondary'
        }
        return colors.get(self.type_document, 'secondary')

    def __str__(self):
        return f"{self.get_type_document_display()} - {self.nom}"

class VisiteStage(models.Model):
    TYPE_CHOICES = [
        ('presentation', 'Présentation entreprise'),
        ('suivi', 'Visite de suivi'),
        ('finale', 'Visite finale'),
    ]

    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='visites')
    type_visite = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateTimeField()
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_visite_display()} - {self.stage}"

    class Meta:
        ordering = ['-date']

class EvaluationStage(models.Model):
    stage = models.OneToOneField(Stage, on_delete=models.CASCADE, related_name='evaluation')
    note = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(20)])
    commentaire = models.TextField()
    date_evaluation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Évaluation {self.stage} - {self.note}/20"

class TacheEtudiant(models.Model):
    etudiant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='taches')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.etudiant.get_full_name()}"

    class Meta:
        ordering = ['complete', 'due_date']

class CalendarEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('cours', 'Cours'),
        ('reunion', 'Réunion pédagogique'),
        ('rendezvous', 'Rendez-vous étudiant'),
        ('soutenance', 'Soutenance'),
        ('autre', 'Autre activité'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calendar_events'
    )
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()
    type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='cours'
    )
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='events_participating',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start']
        verbose_name = "Événement calendrier"
        verbose_name_plural = "Événements calendrier"

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.start.strftime('%d/%m/%Y %H:%M')}"

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

    def __str__(self):
        return self.title