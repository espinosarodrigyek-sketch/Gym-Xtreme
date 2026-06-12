"""
Template tags para filtros
"""
from django import template
from datetime import datetime

register = template.Library()


@register.simple_tag
def filtros_activos(request):
    """
    Retorna diccionario de filtros activos en la petición actual
    Usage: {% filtros_activos as filtros %}
    """
    filtros = {}
    for key, value in request.GET.items():
        if value and value.strip():
            filtros[key] = value
    return filtros


@register.simple_tag
def tiene_filtros(request):
    """
    Retorna True si hay filtros activos
    Usage: {% tiene_filtros as tiene %}
    """
    for value in request.GET.values():
        if value and value.strip():
            return True
    return False


@register.simple_tag
def formato_fecha(valor, formato='%d/%m/%Y'):
    """
    Formatea una fecha
    Usage: {{ fecha|formato_fecha }}
    """
    if not valor:
        return ''
    
    if isinstance(valor, str):
        try:
            valor = datetime.strptime(valor, '%Y-%m-%d')
        except ValueError:
            return valor
    
    if hasattr(valor, 'strftime'):
        return valor.strftime(formato)
    
    return valor


@register.inclusion_tag('partials/filtros.html')
def render_filtros(request, **kwargs):
    """
    Renderiza el componente de filtros
    
    Usage:
        {% render_filtros request 
            mostrar_buscar=True
            mostrar_fecha=True
            mostrar_estado=True
            opciones_estado=opciones_estado
            filtros_custom=filtros_custom
            mostrar_export=True
        %}
    """
    contexto = {
        'request': request,
        'buscar': request.GET.get('buscar', ''),
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
        'estado': request.GET.get('estado', ''),
        'mostrar_buscar': kwargs.get('mostrar_buscar', True),
        'mostrar_fecha': kwargs.get('mostrar_fecha', True),
        'mostrar_estado': kwargs.get('mostrar_estado', False),
        'mostrar_export': kwargs.get('mostrar_export', False),
        'opciones_estado': kwargs.get('opciones_estado', []),
        'filtros_custom': kwargs.get('filtros_custom', []),
        'placeholder_buscar': kwargs.get('placeholder_buscar', 'Buscar...'),
    }
    
    # Calcular si hay filtros activos
    tiene = False
    for value in request.GET.values():
        if value and value.strip():
            tiene = True
            break
    contexto['tiene_filtros'] = tiene
    
    return contexto


@register.simple_tag
def mantener_parametros(request, exclude=None):
    """
    Genera parámetros GET para mantener en links
    
    Usage: <a href="...?{% mantener_parametros request exclude='page' %}">
    """
    if exclude is None:
        exclude = []
    
    params = []
    for key, value in request.GET.items():
        if key not in exclude and value and value.strip():
            params.append(f'{key}={value}')
    
    return '&'.join(params)
