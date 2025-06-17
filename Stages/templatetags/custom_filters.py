from django import template
from urllib.parse import urlencode
register = template.Library()

@register.filter
def split_lines(value):
    """Sépare une chaîne en lignes (utile pour les textarea par ex.)"""
    return value.splitlines()


@register.filter
def filter_statut(queryset, statut):
    return queryset.filter(statut=statut)

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Accède à un élément d’un dictionnaire dans un template"""
    return dictionary.get(key, '')

@register.filter(name='split')
def split(value, arg=None):
    """Divise une chaîne selon un séparateur (par défaut sur les espaces)"""
    if arg is None:
        return value.split()
    return value.split(arg)

@register.filter
def cut(value, arg):
    """Supprime toutes les occurrences de arg dans value"""
    return value.replace(arg, '')



@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Preserve les paramètres existants tout en permettant de les modifier
    Usage: ?{% param_replace request page=page_num %}
    """
    request = context['request']
    params = request.GET.copy()
    
    for key, value in kwargs.items():
        if value:
            params[key] = value
        else:
            params.pop(key, None)
    
    return params.urlencode()