from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Candidature, Stage

@receiver(post_save, sender=Candidature)
def create_stage_on_accept(sender, instance, created, **kwargs):
    if instance.statut == 'accepte':
        stage_existe = Stage.objects.filter(candidature=instance).exists()
        if not stage_existe:
            Stage.objects.create(
                candidature=instance,
                etudiant=instance.etudiant,
                enseignant=instance.offre.enseignant,  # ou autre logique
                date_debut=instance.offre.date_debut,
                date_fin=instance.offre.date_fin,
                tuteur_entreprise=instance.offre.tuteur_entreprise,
            )
