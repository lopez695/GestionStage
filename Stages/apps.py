from django.apps import AppConfig


class StagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Stages'


# apps.py
def ready(self):
    import Stages.signals

