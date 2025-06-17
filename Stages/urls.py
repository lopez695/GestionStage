from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import CalendarView, CalendarEventsAPI

urlpatterns = [
    # Accueil & Authentification
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
   
    # Profils
    path('profil_etudiant/', views.profil_etudiant, name='my_profile'),
    path('profil_etudiant/<int:etudiant_id>/', views.profil_etudiant, name='profil_etudiant'),
    path('modifier_profil/', views.modifier_profil, name='modifier_profil'),
    path('entreprise/<int:entreprise_id>/', views.profil_entreprise, name='profil_entreprise'),
    path('entreprise/<int:pk>/', views.detail_entreprise, name='detail_entreprise'),
    path('entreprise/modifier/', views.modifier_profil_entreprise, name='modifier_profil_entreprise'),
    path('enseignant/profil/', views.profil_enseignant, name='profil_enseignant'),
    path('enseignant/modifier/', views.modifier_profil_enseignant, name='modifier_profil_enseignant'),

    # Dashboards
    path('entreprise/', views.dashboard_entreprise, name='dashboard_entreprise'),
    path('etudiant/', views.dashboard_etudiant, name='dashboard_etudiant'),
    path('enseignant/', views.dashboard_enseignant, name='dashboard_enseignant'),

    # Offres de stage
    path('offres/', views.liste_offres, name='offres'),
    path('offres/<int:offre_id>/', views.detail_offre, name='detail_offre'),

   
    path('entreprise/candidatures/', views.toutes_candidatures, name='toutes_candidatures'),


    path('creer-offre/', views.creer_offre, name='creer_offre'),
    path('offres/<int:offre_id>/postuler/', views.postuler, name='postuler'),
    path('offres/<int:offre_id>/modifier/', views.modifier_offre, name='modifier_offre'),
    path('offres/<int:offre_id>/supprimer/', views.supprimer_offre, name='supprimer_offre'),
    path('offres/<int:offre_id>/candidater/', views.nouvelle_candidature, name='nouvelle_candidature'),
    path('offres/<int:offre_id>/candidatures/', views.liste_candidatures, name='liste_candidatures'),

    # Candidatures
    path('mes-candidatures/', views.mes_candidatures, name='mes_candidatures'),
    path('mes-candidatures/<int:candidature_id>/', views.detail_candidature, name='detail_candidature'),
    path('candidatures/<int:candidature_id>/accepter/', views.accepter_candidature, name='accepter_candidature'),
    path('candidatures/<int:candidature_id>/refuser/', views.refuser_candidature, name='refuser_candidature'),
    path('candidature/<int:candidature_id>/modifier/', views.modifier_candidature, name='modifier_candidature'),
    path('candidature/<int:candidature_id>/maj_cv/', views.maj_cv, name='maj_cv'),
    path('candidature/<int:candidature_id>/maj_lettre/', views.maj_lettre_motivation, name='maj_lettre_motivation'),

    # Stages
    path('stages/', views.liste_stages, name='liste_stages'),
    
    path('stages/<int:stage_id>/', views.detail_stage, name='detail_stage'),
    path('stages/creer/<int:etudiant_id>/', views.creer_stage, name='creer_stage'),

    path('stages/<int:stage_id>/suivi/', views.suivi_stage, name='suivi_stage'),
    path('stages/<int:stage_id>/terminer/', views.terminer_stage, name='terminer_stage'),
    path('stages/<int:stage_id>/modifier/', views.modifier_stage, name='modifier_stage'),
    path('stages/<int:stage_id>/valider/', views.valider_stage, name='valider_stage'),
    path('stages/<int:stage_id>/documents/', views.liste_documents_stage, name='liste_documents_stage'),
    path('stages/<int:stage_id>/accepter/', views.accepter_stage, name='accepter_stage'),
    path('stages/<int:stage_id>/refuser/', views.refuser_stage, name='refuser_stage'),

    # Rapports
    path('mes_rapports/', views.mes_rapports, name='mes_rapports'),
    path('rapports/', views.liste_rapports, name='liste_rapports'),
    path('rapport/soumettre/<int:stage_id>/', views.soumettre_rapport, name='soumettre_rapport'),
    path('rapport/<int:rapport_id>/', views.detail_rapport, name='detail_rapport'),
    path('rapport/evaluer/<int:rapport_id>/', views.evaluer_rapport, name='evaluer_rapport'),
    path('rapport/<int:rapport_id>/commenter/', views.ajouter_commentaire_rapport, name='ajouter_commentaire_rapport'),

    # Documents de stage
    path('documents/upload/<int:stage_id>/', views.upload_document_stage, name='upload_document_stage'),
    path('documents/<int:document_id>/supprimer/', views.supprimer_document_stage, name='supprimer_document_stage'),
    path('documents/<int:document_id>/telecharger/', views.telecharger_document_stage, name='telecharger_document_stage'),

    # Visites de stage
    path('visites/', views.liste_visites, name='liste_visites'),
    path('visites/creer/<int:stage_id>/', views.creer_visite, name='creer_visite'),
    path('visites/<int:visite_id>/', views.detail_visite, name='detail_visite'),
    path('visites/<int:visite_id>/modifier/', views.modifier_visite, name='modifier_visite'),
    path('visites/<int:visite_id>/supprimer/', views.supprimer_visite, name='supprimer_visite'),

    # Evaluations de stage
    path('evaluations/<int:stage_id>/', views.detail_evaluation, name='detail_evaluation'),
    path('evaluations/<int:stage_id>/creer/', views.creer_evaluation, name='creer_evaluation'),
    path('evaluations/<int:evaluation_id>/modifier/', views.modifier_evaluation, name='modifier_evaluation'),

    # Messagerie simplifiée
    path('messagerie/envoyer/<int:destinataire_id>/', views.envoyer_message, name='envoyer_message'),

    path('messagerie/reception/', views.boite_reception, name='boite_reception'),
    
    path('messagerie/<int:message_id>/', views.detail_message, name='detail_message'),
    

    # Notifications
    path('notifications/', views.liste_notifications, name='notifications'),

    # Contact
    path('contact/', views.contact, name='contact'),
    path('entreprise/<int:entreprise_id>/contacter/', views.contact_entreprise, name='contact_entreprise'),

    # Recherche
    path('recherche/', views.recherche, name='recherche'),

    # Enseignant - gestion des étudiants
    path('enseignant/etudiants/', views.liste_etudiants, name='liste_etudiants'),

    # Calendrier et tâches
    path('calendrier/', CalendarView.as_view(), name='calendrier'),
    path('calendrier/evenements/', CalendarEventsAPI.as_view(), name='calendar_events'),
    path('calendrier/evenements/<int:event_id>/', CalendarEventsAPI.as_view(), name='calendar_event_detail'),
    path('taches/', views.task_list, name='task_list'),
    path('taches/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('taches/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Note: path('messagerie/envoyes/', views.messages_envoyes, name='messages_envoyes'),
# Note: path('messagerie/<int:message_id>/repondre/', views.repondre_message, name='repondre_message'),