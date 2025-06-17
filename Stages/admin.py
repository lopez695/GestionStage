from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Etudiant, Enseignant, Entreprise, Offre, 
    Candidature, Stage, Rapport, CommentaireRapport, 
    Message, Notification, DocumentStage, VisiteStage,
    EvaluationStage, TacheEtudiant, CalendarEvent, Task
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone', 'photo', 'cv', 'adresse')}),
        ('Rôle', {'fields': ('role', 'est_visible_enseignant')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'numero_etudiant', 'niveau', 'specialite', 'enseignant_referent')
    list_filter = ('niveau', 'specialite', 'enseignant_referent')
    search_fields = ('nom', 'prenom', 'numero_etudiant', 'user__email')
    raw_id_fields = ('user', 'enseignant_referent')
    fieldsets = (
        (None, {
            'fields': ('user', 'nom', 'prenom', 'photo', 'numero_etudiant')
        }),
        ('Informations académiques', {
            'fields': ('promotion', 'specialite', 'niveau', 'etablissement', 'enseignant_referent')
        }),
        ('Coordonnées', {
            'fields': ('telephone', 'adresse', 'ville')
        }),
    )

class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'departement', 'grade', 'mail')
    search_fields = ('nom', 'prenom', 'departement', 'user__email')
    list_filter = ('departement', 'grade')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nom', 'prenom', 'photo')
        }),
        ('Informations professionnelles', {
            'fields': ('departement', 'grade', 'bureau')
        }),
        ('Coordonnées', {
            'fields': ('mail', 'telephone')
        }),
    )

class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'secteur', 'email', 'site_web')
    search_fields = ('nom', 'secteur', 'user__email')
    list_filter = ('secteur',)
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nom', 'logo', 'description')
        }),
        ('Informations', {
            'fields': ('secteur', 'adresse', 'email', 'site_web')
        }),
    )

class OffreAdmin(admin.ModelAdmin):
    list_display = ('titre', 'entreprise', 'date_publication', 'date_limite', 'est_active')
    list_filter = ('est_active', 'entreprise', 'date_limite')
    search_fields = ('titre', 'description', 'entreprise__nom')
    raw_id_fields = ('entreprise',)
    date_hierarchy = 'date_publication'
    fieldsets = (
        (None, {
            'fields': ('entreprise', 'titre', 'description', 'competences_requises')
        }),
        ('Dates', {
            'fields': ('date_limite', 'duree_semaines')
        }),
        ('Statut', {
            'fields': ('est_active',)
        }),
    )

class CandidatureAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'offre', 'statut', 'date_postulation')
    list_filter = ('statut', 'offre__entreprise')
    search_fields = ('etudiant__user__username', 'offre__titre')
    raw_id_fields = ('etudiant', 'offre')
    date_hierarchy = 'date_postulation'
    fieldsets = (
        (None, {
            'fields': ('etudiant', 'offre', 'statut')
        }),
        ('Documents', {
            'fields': ('cv', 'lettre_motivation')
        }),
        ('Commentaires', {
            'fields': ('commentaire',)
        }),
    )

from django.contrib import admin
from .models import Stage

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'offre', 'sujet', 'date_debut', 'date_fin', 'valide_par_admin']
    list_filter = ['valide_par_admin']
    search_fields = ['etudiant__nom', 'offre__titre', 'sujet']
    raw_id_fields = ('etudiant', 'offre')


class RapportAdmin(admin.ModelAdmin):
    list_display = ('stage', 'statut', 'date_soumission', 'note')
    list_filter = ('statut',)
    search_fields = ('stage__candidature__etudiant__user__username',)
    raw_id_fields = ('stage',)
    date_hierarchy = 'date_soumission'
    fieldsets = (
        (None, {
            'fields': ('stage', 'fichier', 'statut')
        }),
        ('Évaluation', {
            'fields': ('note', 'commentaires')
        }),
    )

class CommentaireRapportAdmin(admin.ModelAdmin):
    list_display = ('rapport', 'auteur', 'date_creation')
    search_fields = ('rapport__stage__candidature__etudiant__user__username', 'auteur__username')
    raw_id_fields = ('rapport', 'auteur')
    date_hierarchy = 'date_creation'
    fieldsets = (
        (None, {
            'fields': ('rapport', 'auteur', 'contenu')
        }),
    )

class MessageAdmin(admin.ModelAdmin):
    list_display = ('expediteur', 'destinataire', 'date_envoi', 'lu')
    list_filter = ('lu',)
    search_fields = ('expediteur__username', 'destinataire__username', 'contenu')
    raw_id_fields = ('expediteur', 'destinataire')
    date_hierarchy = 'date_envoi'
    fieldsets = (
        (None, {
            'fields': ('expediteur', 'destinataire', 'contenu', 'lu')
        }),
    )

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'message', 'lue', 'date_creation')
    list_filter = ('lue',)
    search_fields = ('utilisateur__username', 'message')
    raw_id_fields = ('utilisateur',)
    date_hierarchy = 'date_creation'
    fieldsets = (
        (None, {
            'fields': ('utilisateur', 'message', 'lien', 'lue')
        }),
    )

class DocumentStageAdmin(admin.ModelAdmin):
    list_display = ('stage', 'type_document', 'nom', 'date_upload')
    list_filter = ('type_document',)
    search_fields = ('stage__candidature__etudiant__user__username', 'nom')
    raw_id_fields = ('stage', 'auteur')
    date_hierarchy = 'date_upload'
    fieldsets = (
        (None, {
            'fields': ('stage', 'type_document', 'nom', 'fichier', 'auteur')
        }),
    )

class VisiteStageAdmin(admin.ModelAdmin):
    list_display = ('stage', 'type_visite', 'date')
    list_filter = ('type_visite',)
    search_fields = ('stage__candidature__etudiant__user__username', 'notes')
    raw_id_fields = ('stage',)
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('stage', 'type_visite', 'date', 'notes')
        }),
    )

class EvaluationStageAdmin(admin.ModelAdmin):
    list_display = ('stage', 'note', 'date_evaluation')
    search_fields = ('stage__candidature__etudiant__user__username', 'commentaire')
    raw_id_fields = ('stage',)
    date_hierarchy = 'date_evaluation'
    fieldsets = (
        (None, {
            'fields': ('stage', 'note', 'commentaire')
        }),
    )

class TacheEtudiantAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'title', 'due_date', 'complete')
    list_filter = ('complete',)
    search_fields = ('etudiant__username', 'title')
    raw_id_fields = ('etudiant',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('etudiant', 'title', 'description', 'due_date', 'complete')
        }),
    )

class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'start', 'end')
    list_filter = ('type',)
    search_fields = ('title', 'user__username', 'description')
    raw_id_fields = ('user', 'participants')
    date_hierarchy = 'start'
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'type', 'description')
        }),
        ('Dates', {
            'fields': ('start', 'end')
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
    )

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'due_date', 'completed', 'is_overdue')
    list_filter = ('completed',)
    search_fields = ('title', 'student__username', 'description')
    raw_id_fields = ('student',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('student', 'title', 'description', 'due_date', 'completed')
        }),
    )

    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'En retard'

# Enregistrement des modèles admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Etudiant, EtudiantAdmin)
admin.site.register(Enseignant, EnseignantAdmin)
admin.site.register(Entreprise, EntrepriseAdmin)
admin.site.register(Offre, OffreAdmin)
admin.site.register(Candidature, CandidatureAdmin)

admin.site.register(Rapport, RapportAdmin)
admin.site.register(CommentaireRapport, CommentaireRapportAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(DocumentStage, DocumentStageAdmin)
admin.site.register(VisiteStage, VisiteStageAdmin)
admin.site.register(EvaluationStage, EvaluationStageAdmin)
admin.site.register(TacheEtudiant, TacheEtudiantAdmin)
admin.site.register(CalendarEvent, CalendarEventAdmin)
admin.site.register(Task, TaskAdmin)