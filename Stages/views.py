# Standard Library Imports
import json
import os
from datetime import timedelta


# Django Imports
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q, Max, Count, Prefetch
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import Http404, JsonResponse, FileResponse
from django.core.mail import send_mail
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Local Imports
from .forms import (
    ConnexionForm, ContactEntrepriseForm, CustomUserForm, EtudiantForm,
    EntrepriseForm, EnseignantForm, InscriptionForm, OffreForm,
    CandidatureForm, MessageForm, RapportForm, CommentaireForm,
    StageForm, DocumentForm, VisiteForm, EvaluationForm, TaskForm
)
from .models import (
    CustomUser, Enseignant, Entreprise, Offre, Candidature, Message,
    Notification, Stage, EvaluationStage, Etudiant,
    Rapport, CommentaireRapport, DocumentStage, VisiteStage, Task,
    CalendarEvent
)

CustomUser = get_user_model()

# ==================== Vues d'authentification ====================

def accueil(request):
    return render(request, 'stages/accueil.html')

def inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            if user.role == CustomUser.ETUDIANT:
                Etudiant.objects.create(
                    user=user,
                    numero_etudiant=form.cleaned_data.get('numero_etudiant'),
                    promotion=form.cleaned_data.get('promotion'),
                    specialite=form.cleaned_data.get('specialite')
                )
            elif user.role == CustomUser.ENTREPRISE:
                Entreprise.objects.create(user=user)
            elif user.role == CustomUser.ENSEIGNANT:
                Enseignant.objects.create(user=user)
                
            return redirect('accueil')
    else:
        form = InscriptionForm()
    return render(request, 'stages/inscription.html', {'form': form})

def connexion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accueil')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'stages/connexion.html')

def deconnexion(request):
    logout(request)
    return redirect('accueil')

# ==================== Tableaux de bord ====================

@login_required
def dashboard_entreprise(request):
    if request.user.role != CustomUser.ENTREPRISE:
        return redirect('accueil')
    
    try:
        entreprise = request.user.entreprise_profile
        offres = entreprise.offres.all()
        return render(request, 'stages/dashboard_entreprise.html', {
            'entreprise': entreprise,
            'offres': offres,
        })
    except Entreprise.DoesNotExist:
        return redirect('accueil')

@login_required
def dashboard_etudiant(request):
    if request.user.role != CustomUser.ETUDIANT:
        return redirect('accueil')
    
    etudiant = request.user.etudiant
    
    stages_en_cours = Stage.objects.filter(
        candidature__etudiant=etudiant,
        statut='EN_COURS',
        date_debut__lte=timezone.now().date()
    ).select_related('candidature__offre__entreprise', 'enseignant').prefetch_related('documents', 'rapports')
    
    stages_termines = Stage.objects.filter(
        candidature__etudiant=etudiant,
        statut='TERMINE'
    ).order_by('-date_fin')
    
    stages_avenir = Stage.objects.filter(
        candidature__etudiant=etudiant,
        date_debut__gt=timezone.now().date()
    ).order_by('date_debut')
    
    documents_recents = DocumentStage.objects.filter(
        stage__candidature__etudiant=etudiant
    ).order_by('-date_upload')[:3]
    
    rapports_recents = Rapport.objects.filter(
        stage__candidature__etudiant=etudiant
    ).order_by('-date_soumission')[:3]
    
    tasks = Task.objects.filter(student=request.user).order_by('-due_date')[:5]
    
    notifications = Notification.objects.filter(
        utilisateur=request.user,
        lue=False
    ).order_by('-date_creation')[:5]
    
    context = {
        'etudiant': etudiant,
        'stages_en_cours': stages_en_cours,
        'stages_termines': stages_termines,
        'stages_avenir': stages_avenir,
        'documents_recents': documents_recents,
        'rapports_recents': rapports_recents,
        'tasks': tasks,
        'notifications': notifications,
        'page_active': 'dashboard',
        'aujourdhui': timezone.now().date(),
    }
    
    return render(request, 'stages/dashboard_etudiant.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Stage, Etudiant, Rapport, Enseignant, CustomUser

@login_required
def dashboard_enseignant(request):
    if request.user.role != CustomUser.ENSEIGNANT:
        messages.warning(request, "Accès non autorisé.")
        return redirect('accueil')

    try:
        enseignant = request.user.enseignant  # Relation OneToOneField depuis CustomUser vers Enseignant
    except Enseignant.DoesNotExist:
        messages.error(request, "Profil enseignant introuvable.")
        return redirect('accueil')

    context = {
        'nb_stages': Stage.objects.filter(enseignant=enseignant).count(),
        'nb_etudiants': Etudiant.objects.filter(enseignant_referent=enseignant).count(),
        'nb_rapports': Rapport.objects.filter(stage__enseignant=enseignant, statut='soumis').count(),
        'derniers_stages': Stage.objects.filter(enseignant=enseignant).order_by('-date_debut')[:5]
    }
    return render(request, 'stages/dashboard_enseignant.html', context)


# ==================== Vues pour la messagerie simplifiée ====================


# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models
from .models import Message

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models
from .models import Message

from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Message
import json

def envoyer_message(request, destinataire_id=None):
    User = get_user_model()
    
    # Gestion de la requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                destinataire_id = data.get('destinataire')
                contenu = data.get('contenu')
                
                if not destinataire_id or not contenu:
                    return JsonResponse({'success': False, 'error': 'Données manquantes'}, status=400)
                
                destinataire = get_object_or_404(User, id=destinataire_id)
                
                # Création du message
                message = Message.objects.create(
                    expediteur=request.user,
                    destinataire=destinataire,
                    contenu=contenu
                )
                
                # Préparation de la réponse
                response_data = {
                    'success': True,
                    'message': {
                        'id': message.id,
                        'contenu': message.contenu,
                        'date_envoi': message.date_envoi.strftime("%H:%M"),
                        'expediteur': {
                            'id': message.expediteur.id,
                            'nom_complet': f"{message.expediteur.first_name} {message.expediteur.last_name}"
                        },
                        'lu': message.lu
                    }
                }
                return JsonResponse(response_data)
            
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # Code original pour le chargement initial
    # MODIFICATION ICI : Exclure les superutilisateurs avec .filter(is_superuser=False)
    contacts = User.objects.exclude(id=request.user.id).filter(is_superuser=False).only(
        'id', 'first_name', 'last_name', 'photo', 'is_online'
    ).order_by('first_name')
    
    destinataire = None
    messages = []
    
    if destinataire_id:
        destinataire = get_object_or_404(User, id=destinataire_id)
        
        messages = Message.objects.filter(
            models.Q(expediteur=request.user, destinataire=destinataire) |
            models.Q(expediteur=destinataire, destinataire=request.user)
        ).select_related('expediteur', 'destinataire').order_by('date_envoi')
        
        # Marquer les messages comme lus
        if destinataire:
            Message.objects.filter(
                expediteur=destinataire,
                destinataire=request.user,
                lu=False
            ).update(lu=True)
    
    # Si c'est une requête AJAX GET (pour rafraîchir les messages)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
        messages_data = [{
            'id': msg.id,
            'contenu': msg.contenu,
            'date_envoi': msg.date_envoi.strftime("%H:%M"),
            'expediteur': {
                'id': msg.expediteur.id,
                'nom_complet': f"{msg.expediteur.first_name} {msg.expediteur.last_name}",
                'is_me': msg.expediteur == request.user
            },
            'lu': msg.lu
        } for msg in messages]
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'destinataire': {
                'id': destinataire.id if destinataire else None,
                'nom_complet': f"{destinataire.first_name} {destinataire.last_name}" if destinataire else None,
                'is_online': destinataire.is_online if destinataire else False
            }
        })
    
    return render(request, 'stages/envoyer_message.html', {
        'contacts': contacts,
        'destinataire': destinataire,
        'messages': messages,
        'user': request.user
    })

@login_required
def boite_reception(request):
    messages_recus = Message.objects.filter(
        destinataire=request.user
    ).select_related('expediteur').order_by('-date_envoi')
    
    # Marquer les messages comme lus lorsqu'ils sont affichés
    messages_recus.filter(lu=False).update(lu=True)
    
    return render(request, 'stages/boite_reception.html', {
        'messages': messages_recus,
        'page_active': 'messagerie'
    })

@login_required
def messages_envoyes(request):
    messages_envoyes = Message.objects.filter(
        expediteur=request.user
    ).select_related('destinataire').order_by('-date_envoi')
    
    return render(request, 'stages/messages_envoyes.html', {
        'messages': messages_envoyes,
        'page_active': 'messagerie'
    })

@login_required
def detail_message(request, message_id):
    message = get_object_or_404(
        Message.objects.select_related('expediteur', 'destinataire'),
        id=message_id,
        destinataire=request.user
    )
    
    if not message.lu:
        message.lu = True
        message.save()
    
    return render(request, 'stages/detail_message.html', {
        'message': message,
        'page_active': 'messagerie'
    })

@login_required
def repondre_message(request, message_id):
    message_original = get_object_or_404(Message, id=message_id, destinataire=request.user)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            nouveau_message = form.save(commit=False)
            nouveau_message.expediteur = request.user
            nouveau_message.destinataire = message_original.expediteur
            nouveau_message.save()
            messages.success(request, "Réponse envoyée avec succès")
            return redirect('boite_reception')
    else:
        form = MessageForm(initial={
            'destinataire': message_original.expediteur,
            'contenu': f"\n\n--- Message original ---\n{message_original.contenu}"
        })
    
    return render(request, 'stages/envoyer_message.html', {
        'form': form,
        'message_original': message_original,
        'page_active': 'messagerie'
    })

# ==================== Vues pour les offres et candidatures ====================

@login_required
def creer_offre(request):
    if request.user.role != CustomUser.ENTREPRISE:
        return redirect('accueil')
    
    entreprise = request.user.entreprise_profile
    if request.method == 'POST':
        form = OffreForm(request.POST)
        if form.is_valid():
            offre = form.save(commit=False)
            offre.entreprise = entreprise
            offre.save()
            messages.success(request, "Offre créée avec succès")
            return redirect('dashboard_entreprise')
    else:
        form = OffreForm()
    return render(request, 'stages/creer_offre.html', {'form': form})

from django.contrib import messages

@login_required
def modifier_offre(request, offre_id):
    offre = get_object_or_404(Offre, id=offre_id, entreprise=request.user.entreprise_profile)
    
    if request.method == 'POST':
        form = OffreForm(request.POST, instance=offre)
        if form.is_valid():
            form.save()
            messages.success(request, "L'offre a été mise à jour avec succès")
            return redirect('dashboard_entreprise')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous")
    else:
        form = OffreForm(instance=offre)
    
    return render(request, 'Stages/modifier_offre.html', {
        'form': form,
        'offre': offre,
        'today': timezone.now().date()  # Pour validation JS
    })


@login_required
def supprimer_offre(request, offre_id):
    offre = get_object_or_404(Offre, id=offre_id, entreprise=request.user.entreprise_profile)
    if request.method == 'POST':
        offre.delete()
        return redirect('dashboard_entreprise')
    return redirect('modifier_offre', offre_id=offre_id)

def liste_offres(request):
    user = request.user
    offres = Offre.objects.filter(
        est_active=True,
        date_limite__gte=timezone.now().date()
    ).order_by('-date_publication')

    if 'q' in request.GET:
        query = request.GET['q']
        offres = offres.filter(
            Q(titre__icontains=query) | 
            Q(description__icontains=query) |
            Q(entreprise__nom__icontains=query))
    
    if 'secteur' in request.GET and request.GET['secteur']:
        offres = offres.filter(entreprise__secteur=request.GET['secteur'])

    candidatures_dict = {}
    if user.is_authenticated and hasattr(user, 'etudiant'):
        etudiant = user.etudiant
        candidatures = Candidature.objects.filter(etudiant=etudiant).values_list('offre_id', flat=True)
        candidatures_dict = {offre_id: True for offre_id in candidatures}

    secteurs = Offre.objects.filter(
        est_active=True,
        date_limite__gte=timezone.now().date()
    ).values_list('entreprise__secteur', flat=True).distinct()

    return render(request, 'stages/liste_offres.html', {
        'offres': offres,
        'candidatures_dict': candidatures_dict,
        'secteurs': secteurs,
    })

def detail_offre(request, offre_id):
    offre = get_object_or_404(Offre, id=offre_id)
    deja_postule = False

    if request.user.is_authenticated and request.user.role == CustomUser.ETUDIANT:
        try:
            etudiant = request.user.etudiant
            deja_postule = offre.candidatures.filter(etudiant=etudiant).exists()
        except Etudiant.DoesNotExist:
            deja_postule = False

    return render(request, 'stages/detail_offre.html', {
        'offre': offre,
        'deja_postule': deja_postule
    })

@login_required
def postuler(request, offre_id):
    if request.user.role != CustomUser.ETUDIANT:
        return redirect('accueil')
        
    offre = get_object_or_404(Offre, id=offre_id)
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.etudiant = request.user
            candidature.offre = offre
            candidature.save()
        
            Notification.objects.create(
                utilisateur=offre.entreprise.user,
                message=f"Nouvelle candidature pour {offre.titre}",
                lien=f"/candidature/{candidature.id}/"
            )
            messages.success(request, "Candidature envoyée avec succès")
            return redirect('mes_candidatures')
    else:
        form = CandidatureForm()
    return render(request, 'stages/postuler.html', {'form': form, 'offre': offre})

def nouvelle_candidature(request, offre_id):
    offre = get_object_or_404(Offre, id=offre_id)

    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            etudiant = request.user.etudiant

            if Candidature.objects.filter(etudiant=etudiant, offre=offre).exists():
                messages.warning(request, "Vous avez déjà postulé à cette offre.")
                return redirect('detail_offre', offre_id=offre.id)

            candidature = form.save(commit=False)
            candidature.offre = offre
            candidature.etudiant = etudiant

            try:
                candidature.save()
                messages.success(request, "Votre candidature a été envoyée avec succès.")
            except IntegrityError:
                messages.error(request, "Une erreur est survenue, vous avez peut-être déjà postulé.")

            return redirect('detail_offre', offre_id=offre.id)
    else:
        form = CandidatureForm()

    return render(request, 'stages/nouvelle_candidature.html', {'form': form, 'offre': offre})

@login_required
def mes_candidatures(request):
    if request.user.role != CustomUser.ETUDIANT:
        return redirect('accueil')
    
    try:
        etudiant = request.user.etudiant
    except Etudiant.DoesNotExist:
        messages.error(request, "Profil étudiant non trouvé")
        return redirect('accueil')
    
    candidatures = Candidature.objects.filter(etudiant=etudiant).select_related('offre', 'offre__entreprise')
    
    return render(request, 'stages/mes_candidatures.html', {
        'candidatures': candidatures,
        'etudiant': etudiant
    })

@login_required
def modifier_candidature(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id, etudiant=request.user.etudiant)
    
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES, instance=candidature)
        if form.is_valid():
            form.save()
            return redirect('mes_candidatures')
    else:
        form = CandidatureForm(instance=candidature)
    
    return render(request, 'stages/modifier_candidature.html', {
        'candidature': candidature,
        'form': form,
    })

@login_required
def liste_candidatures(request, offre_id):
    offre = get_object_or_404(Offre, id=offre_id, entreprise=request.user.entreprise_profile)
    candidatures = offre.candidatures.all().order_by('-date_postulation')
    
    return render(request, 'Stages/liste_candidatures.html', {
        'offre': offre,
        'candidatures': candidatures,
    })


def toutes_candidatures(request):
    # Récupérer le paramètre de filtrage
    statut = request.GET.get('statut', '')
    
    # Base queryset
    candidatures = Candidature.objects.filter(
        offre__entreprise=request.user.entreprise
    ).select_related('etudiant', 'offre').order_by('-date_postulation')
    
    # Appliquer le filtre si spécifié
    if statut:
        candidatures = candidatures.filter(statut=statut)
    
    # Préparer les stats pour tous les statuts
    stats = {
        'en_attente': Candidature.objects.filter(
            offre__entreprise=request.user.entreprise,
            statut='EN_ATTENTE'
        ).count(),
        'acceptees': Candidature.objects.filter(
            offre__entreprise=request.user.entreprise,
            statut='ACCEPTEE'
        ).count(),
        'refusees': Candidature.objects.filter(
            offre__entreprise=request.user.entreprise,
            statut='REFUSEE'
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(candidatures, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stages/toutes_candidatures.html', {
        'candidatures': page_obj,
        'stats': stats,
        'entreprise': request.user.entreprise
    })




# views.py
from django.http import JsonResponse

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from .models import Candidature, Stage, Notification  # Import de votre modèle

def accepter_candidature(request, candidature_id):
    # Vérification que la méthode est bien POST
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
        return redirect('accueil')

    # Récupération sécurisée de la candidature
    candidature = get_object_or_404(
        Candidature,
        id=candidature_id,
        offre__entreprise__user=request.user  # Seule l'entreprise propriétaire peut accepter
    )

    # Vérification que la candidature n'est pas déjà acceptée
    if candidature.statut == 'ACCEPTEE':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cette candidature a déjà été acceptée'}, status=400)
        messages.warning(request, "Cette candidature a déjà été acceptée")
        return redirect('liste_candidatures', offre_id=candidature.offre.id)

    # Mise à jour de la candidature
    candidature.statut = 'ACCEPTEE'
    candidature.date_acceptation = timezone.now()
    candidature.save()

    # Création du stage si nécessaire
    if not Stage.objects.filter(candidature=candidature).exists():
        stage = Stage.objects.create(
            candidature=candidature,
            enseignant=candidature.etudiant.enseignant_referent,
            tuteur_entreprise=f"{request.user.get_full_name()}",
            date_debut=candidature.offre.date_debut,
            date_fin=candidature.offre.date_fin,
            statut='en_attente',
            valide=False
        )
    else:
        stage = Stage.objects.get(candidature=candidature)

    # Création de la notification
    Notification.objects.create(
        utilisateur=candidature.etudiant.user,  # Destinataire
        message=f"Votre candidature pour '{candidature.offre.titre}' a été acceptée",
        lien=f"/stages/{stage.id}/",  # Lien vers le stage
        lue=False
    )

    # Réponse adaptée (AJAX ou normale)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Candidature acceptée et stage créé',
            'stage_id': stage.id  # Optionnel: renvoyer l'ID du stage créé
        })

    messages.success(request, "Candidature acceptée et notification envoyée")
    return redirect('liste_candidatures', offre_id=candidature.offre.id)



def refuser_candidature(request, candidature_id):
    if request.method == 'POST':
        candidature = get_object_or_404(Candidature, id=candidature_id)
        candidature.statut = 'REFUSEE'
        candidature.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('liste_candidatures', offre_id=candidature.offre.id)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)



@login_required
def detail_candidature(request, candidature_id):
    try:
        if request.user.role == CustomUser.ENTREPRISE:
            candidature = get_object_or_404(
                Candidature,
                id=candidature_id,
                offre__entreprise=request.user.entreprise_profile
            )
        elif request.user.role == CustomUser.ETUDIANT:
            candidature = get_object_or_404(
                Candidature,
                id=candidature_id,
                etudiant=request.user.etudiant
            )
        else:
            return redirect('accueil')
            
    except (Candidature.DoesNotExist, Etudiant.DoesNotExist, AttributeError):
        raise Http404("Candidature non trouvée ou accès non autorisé")
    
    return render(request, 'Stages/detail_candidature.html', {'candidature': candidature})

# ==================== Vues pour les stages ====================

@login_required
def liste_stages(request):
    # Filtre de base
    if request.user.role == 'etudiant':
        stages = Stage.objects.filter(candidature__etudiant=request.user.etudiant_profile)
    elif request.user.role == 'enseignant':
        stages = Stage.objects.filter(enseignant=request.user)
    elif request.user.role == 'entreprise':
        stages = Stage.objects.filter(
            candidature__offre__entreprise=request.user.entreprise_profile,
            candidature__statut='ACCEPTEE'  # Seulement les candidatures acceptées
        )
    else:
        stages = Stage.objects.none()

    # Filtres supplémentaires
    statut = request.GET.get('statut')
    if statut == 'valide':
        stages = stages.filter(valide=True)
    elif statut == 'en_attente':
        stages = stages.filter(valide=False, statut='en_attente')
    elif statut == 'termine':
        stages = stages.filter(statut='TERMINE')
    
    # Pagination
    paginator = Paginator(stages, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stages/liste_stage.html', {
        'stages': page_obj,
        'page_active': 'stages'
    })


@login_required
def detail_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if not (request.user == stage.candidature.etudiant or request.user == stage.enseignant):
        return redirect('dashboard_etudiant' if request.user.role == 'etudiant' else 'dashboard_enseignant')
    
    return render(request, 'stages/detail_stage.html', {
        'stage': stage,
        'rapport': getattr(stage, 'rapport_stage', None),
        'documents': stage.documents.all(),
        'visites': stage.visites.all().order_by('-date'),
        'evaluation': getattr(stage, 'evaluation', None),
        'page_active': 'stages'
    })





@login_required
def modifier_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.enseignant:
        return redirect('detail_stage', stage_id=stage_id)
    
    if request.method == 'POST':
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, "Stage mis à jour avec succès")
            return redirect('detail_stage', stage_id=stage_id)
    else:
        form = StageForm(instance=stage)
    
    return render(request, 'stages/modifier_stage.html', {
        'form': form,
        'stage': stage,
        'page_active': 'stages'
    })

@login_required
def suivi_stage(request, stage_id):
    stage = get_object_or_404(Stage, id=stage_id)
    
    if not (request.user == stage.candidature.etudiant or 
            request.user == stage.enseignant or
            request.user == stage.candidature.offre.entreprise.user):
        raise Http404

    documents = stage.documents.all()
    visites = stage.visites.all().order_by('-date')
    commentaires = CommentaireRapport.objects.filter(rapport__stage=stage)

    if request.method == 'POST' and request.user == stage.enseignant:
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire')
        
        EvaluationStage.objects.update_or_create(
            stage=stage,
            defaults={
                'note': note,
                'commentaire': commentaire
            }
        )
        
        messages.success(request, "Évaluation enregistrée avec succès")
        return redirect('suivi_stage', stage_id=stage.id)

    return render(request, 'Stages/suivi_stage.html', {
        'stage': stage,
        'documents': documents,
        'visites': visites,
        'commentaires': commentaires,
        'today': timezone.now().date()
        
    })

@login_required
def accepter_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.enseignant:
        messages.error(request, "Vous n'avez pas la permission d'accepter ce stage")
        return redirect('liste_stages')
    
    if stage.statut != 'en_attente':
        messages.warning(request, "Ce stage a déjà été traité")
        return redirect('detail_stage', stage_id=stage_id)
    
    stage.statut = 'accepte'
    stage.save()
    
    messages.success(request, f"Le stage de {stage.candidature.etudiant.get_full_name()} a été accepté")
    return redirect('detail_stage', stage_id=stage_id)

@login_required
def refuser_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.enseignant:
        messages.error(request, "Vous n'avez pas la permission de refuser ce stage")
        return redirect('liste_stages')
    
    if stage.statut != 'en_attente':
        messages.warning(request, "Ce stage a déjà été traité")
        return redirect('detail_stage', stage_id=stage_id)
    
    stage.statut = 'refuse'
    stage.save()
    
    messages.success(request, f"Le stage de {stage.candidature.etudiant.get_full_name()} a été refusé")
    return redirect('detail_stage', stage_id=stage_id)

@login_required
def terminer_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if not (request.user == stage.candidature.etudiant or request.user == stage.enseignant):
        messages.error(request, "Vous n'avez pas la permission de finaliser ce stage")
        return redirect('liste_stages')
    
    if stage.statut != 'accepte':
        messages.warning(request, "Seuls les stages acceptés peuvent être finalisés")
        return redirect('detail_stage', stage_id=stage_id)
    
    stage.statut = 'termine'
    stage.date_fin_reelle = timezone.now().date()
    stage.save()
    
    messages.success(request, f"Le stage chez {stage.candidature.offre.entreprise.nom} a été marqué comme terminé")
    return redirect('detail_stage', stage_id=stage_id)

@login_required
def valider_stage(request, stage_id):
    stage = get_object_or_404(Stage, id=stage_id)
    
    if request.user.role != CustomUser.ENSEIGNANT or request.user != stage.enseignant:
        raise PermissionDenied("Seul l'enseignant référent peut valider ce stage")
    
    if stage.statut != 'EN_ATTENTE':
        messages.warning(request, "Ce stage a déjà été traité")
        return redirect('detail_stage', stage_id=stage_id)
    
    if request.method == 'POST':
        stage.statut = 'VALIDE'
        stage.date_validation = timezone.now()
        stage.save()
        
        Notification.objects.create(
            utilisateur=stage.candidature.etudiant,
            message=f"Votre stage chez {stage.candidature.offre.entreprise.nom} a été validé",
            lien=f"/stages/{stage.id}/"
        )
        
        messages.success(request, "Stage validé avec succès")
        return redirect('detail_stage', stage_id=stage_id)
    
    return render(request, 'stages/confirmer_validation.html', {'stage': stage})

# ==================== Vues pour les rapports ====================

@login_required
def soumettre_rapport(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    if request.user != stage.candidature.etudiant:
        raise Http404
        
    if request.method == 'POST':
        form = RapportForm(request.POST, request.FILES)
        if form.is_valid():
            rapport = form.save(commit=False)
            rapport.stage = stage
            rapport.statut = 'soumis'
            rapport.save()
            messages.success(request, "Rapport soumis avec succès")
            return redirect('suivi_stage', stage_id=stage.id)
    else:
        form = RapportForm()
    return render(request, 'Stages/soumettre_rapport.html', {'form': form, 'stage': stage})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Rapport

@login_required
def mes_rapports(request):
    # Récupération des paramètres de filtrage
    selected_statut = request.GET.get('statut')
    selected_promotion = request.GET.get('promotion')
    date_filter = request.GET.get('date_filter')
    search_query = request.GET.get('q', '').strip()
    
    try:
        # Base queryset optimisée avec select_related et prefetch_related
        base_query = Rapport.objects.select_related(
            'stage__candidature__etudiant__user',
            'stage__candidature__offre__entreprise'
        ).order_by('-date_soumission')

        # Filtrage initial selon le rôle
        if request.user.role == 'etudiant':
            rapports = base_query.filter(
                stage__candidature__etudiant__user=request.user
            )
        else:
            rapports = base_query.all()

        # Application des filtres
        filters = Q()
        
        # Filtre par statut
        if selected_statut:
            filters &= Q(statut=selected_statut)
        
        # Filtre par promotion (uniquement pour staff/admin)
        if selected_promotion and request.user.role != 'etudiant':
            filters &= Q(stage__candidature__etudiant__promotion=selected_promotion)
        
        # Filtre par date
        today = timezone.now().date()
        if date_filter == 'today':
            filters &= Q(date_soumission__date=today)
        elif date_filter == 'week':
            start_week = today - timedelta(days=today.weekday())
            filters &= Q(date_soumission__date__gte=start_week)
        elif date_filter == 'month':
            filters &= Q(
                date_soumission__month=today.month,
                date_soumission__year=today.year
            )
        
        # Recherche textuelle
        if search_query:
            filters &= (
                Q(stage__candidature__etudiant__user__first_name__icontains=search_query) |
                Q(stage__candidature__etudiant__user__last_name__icontains=search_query) |
                Q(stage__candidature__offre__entreprise__nom__icontains=search_query) |
                Q(titre__icontains=search_query)
            )
        
        # Application combinée des filtres
        rapports = rapports.filter(filters)

        # Pagination
        paginator = Paginator(rapports, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Récupération des promotions disponibles (optimisé)
        promotions = []
        if request.user.role != 'etudiant':
            promotions = (Rapport.objects
                .exclude(stage__candidature__etudiant__promotion__isnull=True)
                .values_list('stage__candidature__etudiant__promotion', flat=True)
                .distinct()
                .order_by('stage__candidature__etudiant__promotion')
            )

        context = {
            'rapports': page_obj,
            'promotions': promotions,
            'selected_statut': selected_statut,
            'selected_promotion': selected_promotion,
            'date_filter': date_filter,
            'search_query': search_query,
            'page_active': 'rapports',
            'STATUT_CHOICES': Rapport.STATUT_CHOICES,
        }
        
        return render(request, 'stages/mes_rapports.html', context)

    except Exception as e:
        # Gestion des erreurs avec message à l'utilisateur
        from django.contrib import messages
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return render(request, 'stages/mes_rapports.html', {'rapports': []})
    
    

@login_required
def detail_rapport(request, rapport_id):
    rapport = get_object_or_404(Rapport, id=rapport_id)
    
    if not (request.user == rapport.stage.candidature.etudiant or
            request.user == rapport.stage.enseignant or
            request.user == rapport.stage.candidature.offre.entreprise.user):
        raise Http404

    commentaires = rapport.commentaires.all().order_by('-date_creation')
    return render(request, 'stages/detail_rapport.html', {
        'rapport': rapport,
        'commentaires': commentaires
    })

@login_required
def evaluer_rapport(request, rapport_id):
    rapport = get_object_or_404(Rapport, pk=rapport_id)
    if request.user != rapport.stage.enseignant:
        raise Http404
        
    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.rapport = rapport
            commentaire.auteur = request.user
            commentaire.save()
            
            if 'valider' in request.POST:
                rapport.statut = 'valide'
                rapport.save()
                
            messages.success(request, "Commentaire enregistré")
            return redirect('detail_rapport', rapport_id=rapport.id)
    else:
        form = CommentaireForm()
    return render(request, 'rapports/evaluer.html', {'form': form, 'rapport': rapport})

@login_required
def ajouter_commentaire_rapport(request, rapport_id):
    rapport = get_object_or_404(Rapport, pk=rapport_id)
    
    if not (request.user == rapport.stage.candidature.etudiant or request.user == rapport.stage.enseignant):
        return redirect('dashboard_etudiant' if request.user.role == 'etudiant' else 'dashboard_enseignant')
    
    if request.method == 'POST':
        form = CommentaireForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.rapport = rapport
            commentaire.auteur = request.user
            commentaire.save()
            messages.success(request, "Commentaire ajouté avec succès")
            return redirect('detail_rapport', rapport_id=rapport.id)
    else:
        form = CommentaireForm()
    
    return render(request, 'stages/ajouter_commentaire.html', {
        'form': form,
        'rapport': rapport,
        'page_active': 'rapports'
    })

from django.shortcuts import render
from django.db.models import Prefetch
from .models import Rapport

@login_required
def liste_rapports(request):
    try:
        # Correction: Utilisez les relations valides selon l'erreur
        rapports = Rapport.objects.select_related(
            'etudiant',        # Relation valide
            'enseignant',      # Relation valide 
            'offre',           # Relation valide
            'evaluation'       # Relation valide
        ).prefetch_related(
            Prefetch('rapport_stage')  # Relation many-to-many si elle existe
        ).order_by('-date_soumission')

        # Si vous avez besoin d'accéder à la candidature via le stage:
        # rapports = Rapport.objects.select_related(
        #     'stage__candidature__etudiant',
        #     'stage__candidature__offre'
        # )

        context = {'rapports': rapports}
        return render(request, 'rapports/liste.html', context)

    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return render(request, 'Stages/liste_rapports.html', {'rapports': []})

# ==================== Vues pour les documents ====================

@login_required
def liste_documents_stage(request, stage_id):
    try:
        stage = get_object_or_404(Stage, pk=stage_id)
        
        user = request.user
        if user.is_authenticated:
            if user.role == 'etudiant' and user != stage.candidature.etudiant:
                raise PermissionDenied("Vous n'avez pas accès à ces documents")
            elif user.role == 'enseignant' and user != stage.enseignant:
                raise PermissionDenied("Vous n'avez pas accès à ces documents")
            elif user.role not in ['etudiant', 'enseignant']:
                raise PermissionDenied("Rôle non autorisé")
        else:
            return redirect('accueil')
        
        documents = stage.documents.select_related('auteur').order_by('-date_upload')
        
        return render(request, 'stages/liste_documents_stage.html', {
            'stage': stage,
            'documents': documents,
            'page_active': 'documents'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur dans liste_documents_stage: {str(e)}", exc_info=True)
        
        if request.user.is_authenticated:
            if request.user.role == 'etudiant':
                return redirect('dashboard_etudiant')
            elif request.user.role == 'enseignant':
                return redirect('dashboard_enseignant')
        return redirect('accueil')

@login_required
def upload_document_stage(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.candidature.etudiant:
        return redirect('detail_stage', stage_id=stage_id)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.stage = stage
            document.save()
            messages.success(request, "Document téléversé avec succès")
            return redirect('liste_documents_stage', stage_id=stage_id)
    else:
        form = DocumentForm()
    
    return render(request, 'stages/upload_document.html', {
        'form': form,
        'stage': stage,
        'page_active': 'documents'
    })

@login_required
def supprimer_document_stage(request, document_id):
    document = get_object_or_404(DocumentStage, pk=document_id)
    
    if request.user != document.stage.candidature.etudiant:
        return redirect('liste_documents_stage', stage_id=document.stage.id)
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, "Document supprimé avec succès")
        return redirect('liste_documents_stage', stage_id=document.stage.id)
    
    return render(request, 'stages/supprimer_document.html', {
        'document': document,
        'page_active': 'documents'
    })

@login_required
def telecharger_document_stage(request, document_id):
    document = get_object_or_404(DocumentStage, pk=document_id)
    
    if not (request.user == document.stage.candidature.etudiant or request.user == document.stage.enseignant):
        return redirect('dashboard_etudiant' if request.user.role == 'etudiant' else 'dashboard_enseignant')
    
    file_path = document.fichier.path
    
    if not os.path.exists(file_path):
        raise Http404("Le fichier demandé n'existe pas")
    
    with open(file_path, 'rb') as file:
        response = FileResponse(file)
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

# ==================== Vues pour les visites ====================

@login_required
def liste_visites(request):
    if request.user.role == 'etudiant':
        stages = Stage.objects.filter(candidature__etudiant=request.user)
        visites = VisiteStage.objects.filter(stage__in=stages)
    elif request.user.role == 'enseignant':
        visites = VisiteStage.objects.filter(stage__enseignant=request.user)
    else:
        visites = VisiteStage.objects.none()
    
    return render(request, 'stages/liste_visite.html', {
        'visites': visites.order_by('-date'),
        'page_active': 'visites'
    })

@login_required
def creer_visite(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.enseignant:
        return redirect('detail_stage', stage_id=stage_id)
    
    if request.method == 'POST':
        form = VisiteForm(request.POST)
        if form.is_valid():
            visite = form.save(commit=False)
            visite.stage = stage
            visite.save()
            messages.success(request, "Visite planifiée avec succès")
            return redirect('detail_visite', visite_id=visite.id)
    else:
        form = VisiteForm(initial={'date': timezone.now()})
    
    return render(request, 'stages/creer.html', {
        'form': form,
        'stage': stage,
        'page_active': 'visites'
    })

@login_required
def detail_visite(request, visite_id):
    visite = get_object_or_404(VisiteStage, pk=visite_id)
    
    if not (request.user == visite.stage.candidature.etudiant or request.user == visite.stage.enseignant):
        return redirect('dashboard_etudiant' if request.user.role == 'etudiant' else 'dashboard_enseignant')
    
    return render(request, 'stages/detail.html', {
        'visite': visite,
        'page_active': 'visites'
    })

@login_required
def modifier_visite(request, visite_id):
    visite = get_object_or_404(VisiteStage, pk=visite_id)
    
    if request.user != visite.stage.enseignant:
        return redirect('detail_visite', visite_id=visite_id)
    
    if request.method == 'POST':
        form = VisiteForm(request.POST, instance=visite)
        if form.is_valid():
            form.save()
            messages.success(request, "Visite modifiée avec succès")
            return redirect('detail_visite', visite_id=visite_id)
    else:
        form = VisiteForm(instance=visite)
    
    return render(request, 'stages/modifier.html', {
        'form': form,
        'visite': visite,
        'page_active': 'visites'
    })

@login_required
def supprimer_visite(request, visite_id):
    visite = get_object_or_404(VisiteStage, pk=visite_id)
    stage_id = visite.stage.id
    
    if request.user != visite.stage.enseignant:
        return redirect('detail_visite', visite_id=visite_id)
    
    if request.method == 'POST':
        visite.delete()
        messages.success(request, "Visite supprimée avec succès")
        return redirect('detail_stage', stage_id=stage_id)
    
    return render(request, 'stages/supprimer.html', {
        'visite': visite,
        'page_active': 'visites'
    })

# ==================== Vues pour les évaluations ====================

@login_required
def detail_evaluation(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    evaluation = getattr(stage, 'evaluation', None)
    
    if not (request.user == stage.candidature.etudiant or request.user == stage.enseignant):
        return redirect('dashboard_etudiant' if request.user.role == 'etudiant' else 'dashboard_enseignant')
    
    return render(request, 'stages/detail.html', {
        'stage': stage,
        'evaluation': evaluation,
        'page_active': 'evaluations'
    })

@login_required
def creer_evaluation(request, stage_id):
    stage = get_object_or_404(Stage, pk=stage_id)
    
    if request.user != stage.enseignant:
        return redirect('detail_evaluation', stage_id=stage_id)
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.stage = stage
            evaluation.save()
            messages.success(request, "Évaluation enregistrée avec succès")
            return redirect('detail_evaluation', stage_id=stage_id)
    else:
        form = EvaluationForm()
    
    return render(request, 'stages/creer.html', {
        'form': form,
        'stage': stage,
        'page_active': 'evaluations'
    })

@login_required
def modifier_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(EvaluationStage, pk=evaluation_id)
    
    if request.user != evaluation.stage.enseignant:
        return redirect('detail_evaluation', stage_id=evaluation.stage.id)
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            messages.success(request, "Évaluation modifiée avec succès")
            return redirect('detail_evaluation', stage_id=evaluation.stage.id)
    else:
        form = EvaluationForm(instance=evaluation)
    
    return render(request, 'stages/modifier.html', {
        'form': form,
        'evaluation': evaluation,
        'page_active': 'evaluations'
    })

# ==================== Vues pour les profils ====================

from django.shortcuts import render, redirect, get_object_or_404, Http404
from django.contrib.auth.decorators import login_required
from .models import Etudiant, Stage, Candidature

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import Http404
from .models import Etudiant, Stage

@login_required
def profil_etudiant(request, etudiant_id=None):
    # Gestion du cas où aucun ID n'est fourni
    if etudiant_id is None:
        if hasattr(request.user, 'etudiant'):
            return redirect('profil_etudiant', etudiant_id=request.user.id)
        return redirect('accueil')
    
    try:
        # Récupération de l'étudiant avec toutes les relations nécessaires
        etudiant = Etudiant.objects.select_related(
            'user',
            'enseignant_referent__user'
        ).get(user__id=etudiant_id)
    except Etudiant.DoesNotExist:
        raise Http404("Profil étudiant non trouvé")
    
    # Récupération des stages avec optimisation des requêtes
    stages = Stage.objects.filter(
        etudiant=etudiant  # Adaptez ceci selon votre modèle (etudiant ou etudiant.user)
    ).select_related(
        'offre__entreprise',
        'enseignant__user'
    ).order_by('-date_debut')
    
    # Préparation du contexte
    context = {
        'user_profile': etudiant.user,  # Renommé pour éviter la confusion avec request.user
        'etudiant': etudiant,
        'stages': stages,
        'enseignant_referent': etudiant.enseignant_referent.user.get_full_name() if etudiant.enseignant_referent else None
    }
    
    return render(request, 'Stages/profil_etudiant.html', context)
@login_required
def modifier_profil(request):
    etudiant = request.user.etudiant
    
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        etudiant_form = EtudiantForm(request.POST, instance=etudiant)
        
        if user_form.is_valid() and etudiant_form.is_valid():
            user = user_form.save()
            etudiant = etudiant_form.save(commit=False)
            etudiant.user = user
            etudiant.save()
            
            messages.success(request, "Profil mis à jour!")
            return redirect('profil_etudiant', etudiant_id=user.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous")
    else:
        user_form = CustomUserForm(instance=request.user)
        etudiant_form = EtudiantForm(instance=etudiant)
    
    return render(request, 'stages/modifier_profil.html', {
        'user_form': user_form,
        'etudiant_form': etudiant_form
    })

@login_required
def profil_entreprise(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    if not request.user.is_authenticated or (request.user != entreprise.user):
        raise PermissionDenied
    
    offres = Offre.objects.filter(entreprise=entreprise).order_by('-date_publication')
    
    return render(request, 'Stages/profil_entreprise.html', {
        'entreprise': entreprise,
        'offres': offres,
        'user': request.user
    })

@login_required
def modifier_profil_entreprise(request):
    try:
        entreprise = request.user.entreprise_profile
    except Entreprise.DoesNotExist:
        return redirect('accueil')

    if request.method == 'POST':
        form = EntrepriseForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            form.save()
            return redirect('profil_entreprise', entreprise_id=entreprise.id)
    else:
        form = EntrepriseForm(instance=entreprise)

    return render(request, 'stages/modifier_entreprise.html', {
        'form': form,
        'entreprise': entreprise,
    })

def detail_entreprise(request, pk):
    entreprise = get_object_or_404(Entreprise, pk=pk)
    return render(request, 'stages/detail_entreprise.html', {
        'entreprise': entreprise,
        'offres': entreprise.offre_set.all()
    })

@login_required
def profil_enseignant(request):
    try:
        enseignant = request.user.enseignant
    except Enseignant.DoesNotExist:
        return redirect('accueil')
    
    return render(request, 'stages/profil_enseignant.html', {'enseignant': enseignant})

@login_required
def modifier_profil_enseignant(request):
    enseignant = get_object_or_404(Enseignant, user=request.user)
    
    if request.method == 'POST':
        form = EnseignantForm(request.POST, request.FILES, instance=enseignant)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('profil_enseignant')
    else:
        form = EnseignantForm(instance=enseignant)

    return render(request, 'stages/modifier_enseignant.html', {
        'form': form,
        'enseignant': enseignant
    })

# ==================== Vues pour les tâches ====================

@login_required
def task_list(request):
    tasks = Task.objects.filter(student=request.user).order_by('-due_date')
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.student = request.user
            task.save()
            messages.success(request, "Tâche ajoutée avec succès")
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'stages/task_list.html', {
        'tasks': tasks,
        'form': form,
        'page_active': 'tasks'
    })

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, student=request.user)
    
    if not task.completed:
        task.completed = True
        task.save()
        messages.success(request, f"Tâche '{task.title}' marquée comme complétée!")
    else:
        messages.warning(request, f"Cette tâche était déjà complétée")
    
    return redirect('task_list')

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, student=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f"Tâche '{task_title}' supprimée avec succès!")
        return redirect('task_list')
    
    return render(request, 'stages/confirm_delete_task.html', {'task': task})

# ==================== Vues pour le calendrier ====================

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'Stages/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CalendarEventsAPI(LoginRequiredMixin, TemplateView):
    
    def get(self, request, *args, **kwargs):
        events = CalendarEvent.objects.filter(user=request.user).values(
            'id',
            'title',
            'start',
            'end',
            'type',
            'description'
        )
        return JsonResponse(list(events), safe=False)
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            event = CalendarEvent.objects.create(
                user=request.user,
                title=data.get('title'),
                start=data.get('start'),
                end=data.get('end'),
                type=data.get('type', 'autre'),
                description=data.get('description', '')
            )
            return JsonResponse({
                'status': 'success',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'start': event.start,
                    'end': event.end,
                    'type': event.type
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def put(self, request, event_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
            
            event.title = data.get('title', event.title)
            event.start = data.get('start', event.start)
            event.end = data.get('end', event.end)
            event.type = data.get('type', event.type)
            event.description = data.get('description', event.description)
            event.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def delete(self, request, event_id, *args, **kwargs):
        try:
            event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
            event.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# ==================== Vues diverses ====================

def contact(request):
    if request.method == 'POST':
        form = request.POST
        send_mail(
            f"[Contact] {form.get('sujet')} - {form.get('nom')}",
            form.get('message'),
            form.get('email'),
            ['contact@votreuniversite.fr'],
            fail_silently=False,
        )
        messages.success(request, "Votre message a bien été envoyé !")
        return redirect('contact')
    
    return render(request, 'contact.html')

def contact_entreprise(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    email_entreprise = getattr(entreprise, 'email', None)
    if not email_entreprise and hasattr(entreprise, 'user'):
        email_entreprise = getattr(entreprise.user, 'email', None)
    
    if request.method == 'POST':
        form = ContactEntrepriseForm(request.POST)
        if form.is_valid():
            if not email_entreprise:
                messages.error(request, "Impossible d'envoyer le message : l'entreprise n'a pas d'email enregistré")
                return redirect('offres')
            
            nom_complet = form.cleaned_data['nom']
            if form.cleaned_data.get('prenom'):
                nom_complet = f"{form.cleaned_data['prenom']} {nom_complet}"
            
            message_complet = f"""
            Nouveau message de contact via la plateforme
            
            Expéditeur: {nom_complet}
            Email: {form.cleaned_data['email']}
            
            Entreprise cible: {entreprise.nom}
            Sujet: {form.cleaned_data['sujet']}
            
            Message:
            {form.cleaned_data['message']}
            
            ---
            Cet email a été envoyé via la plateforme de stages
            """
            
            try:
                send_mail(
                    subject=f"[Contact Plateforme] {form.cleaned_data['sujet']}",
                    message=message_complet,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email_entreprise],
                    fail_silently=False,
                )
                messages.success(request, 'Votre message a été envoyé avec succès à l\'entreprise.')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de l'envoi du message : {str(e)}")
            
            return redirect('offres')
    
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'nom': request.user.last_name or '',
                'prenom': request.user.first_name or '',
                'email': request.user.email or '',
            }
        form = ContactEntrepriseForm(initial=initial_data)
    
    return render(request, 'stages/contact_entreprise.html', {
        'entreprise': entreprise,
        'form': form,
        'contact_email_available': bool(email_entreprise),
    })

@login_required
def liste_etudiants(request):
    etudiants = get_user_model().objects.filter(
        role='ETUDIANT',
        est_visible_enseignant=True
    ).order_by('last_name')

    if request.method == 'POST' and 'etudiant_id' in request.POST:
        try:
            etudiant_id = int(request.POST['etudiant_id'])
            etudiant = get_user_model().objects.get(
                id=etudiant_id,
                role='ETUDIANT'
            )
            etudiant.est_visible_enseignant = False
            etudiant.save()
            messages.success(request, f"{etudiant.get_full_name()} masqué avec succès")
            return redirect('liste_etudiants')
        except (ValueError, TypeError):
            messages.error(request, "ID étudiant invalide")
        except get_user_model().DoesNotExist:
            messages.error(request, "Étudiant introuvable")
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
        return redirect('liste_etudiants')

    if 'q' in request.GET:
        search_term = request.GET['q'].strip()
        if search_term:
            etudiants = etudiants.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term)
            )

    return render(request, 'Stages/liste_etudiants.html', {
        'etudiants': etudiants,
        'search_term': request.GET.get('q', '')
    })

@login_required
def liste_notifications(request):
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')
    
    notifications.update(lue=True)
    
    return render(request, 'stages/liste_notifications.html', {'notifications': notifications})

def recherche(request):
    query = request.GET.get('q', '')
    
    results = Stage.objects.filter(
        Q(candidature__etudiant__username__icontains=query) |
        Q(candidature__etudiant__last_name__icontains=query) |
        Q(candidature__etudiant__first_name__icontains=query) |
        Q(entreprise__nom__icontains=query) |
        Q(sujet__icontains=query)
    ).distinct().select_related('candidature__etudiant')
    
    return render(request, 'Stages/recherche.html', {
        'results': results,
        'query': query
    })

@login_required
def maj_cv(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id, etudiant=request.user)
    if request.method == 'POST' and request.FILES.get('cv'):
        candidature.cv = request.FILES['cv']
        candidature.save()
    return redirect('detail_candidature', candidature_id=candidature.id)

@login_required
def maj_lettre_motivation(request, candidature_id):
    candidature = get_object_or_404(Candidature, id=candidature_id, etudiant=request.user)
    if request.method == 'POST' and request.FILES.get('lettre_motivation'):
        candidature.lettre_motivation = request.FILES['lettre_motivation']
        candidature.save()
    return redirect('detail_candidature', candidature_id=candidature.id)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from .models import Stage, Candidature
from .forms import StageForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Etudiant, Candidature, Stage, Offre

@login_required
def creer_stage(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    
    # Récupérer les candidatures acceptées de l'étudiant
    candidatures = Candidature.objects.filter(etudiant=etudiant, statut='ACCEPTEE')

    if request.method == 'POST':
        offre_id = request.POST.get('offre')
        sujet = request.POST.get('sujet')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        # Validation basique
        if not (offre_id and sujet and date_debut and date_fin):
            messages.error(request, "Tous les champs sont requis.")
            return redirect('creer_stage', etudiant_id=etudiant.id)

        # Vérifier que l'offre est bien liée à une candidature acceptée
        offre_valide = candidatures.filter(offre__id=offre_id).exists()
        if not offre_valide:
            messages.error(request, "Offre invalide ou non acceptée.")
            return redirect('creer_stage', etudiant_id=etudiant.id)

        offre = get_object_or_404(Offre, id=offre_id)

        # Empêcher les doublons
        if Stage.objects.filter(etudiant=etudiant, offre=offre).exists():
            messages.error(request, "Un stage a déjà été créé pour cette offre.")
            return redirect('creer_stage', etudiant_id=etudiant.id)

        # Création du stage
        Stage.objects.create(
            etudiant=etudiant,
            offre=offre,
            sujet=sujet,
            date_debut=date_debut,
            date_fin=date_fin
        )
        messages.success(request, "Le stage a été créé avec succès.")
        return redirect('profil_etudiant', etudiant_id=etudiant.id)

    context = {
        'etudiant': etudiant,
        'candidatures': candidatures,
        'title': 'Créer un stage pour l\'étudiant'
    }
    return render(request, 'Stages/creer_stage.html', context)
