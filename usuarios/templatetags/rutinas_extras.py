from django import template

register = template.Library()

@register.filter
def get_item(dicc, key):
    """Obtiene un valor de un diccionario usando la clave"""
    return dicc.get(key, [])
