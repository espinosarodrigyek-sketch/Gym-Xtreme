"""
Mixins y utilitarios para filtros dinámicos reutilizables en Django
"""
from django.db.models import Q
from django.shortcuts import render
from datetime import datetime


class FiltrosMixin:
    """
    Mixin reutilizable para gestionar filtros en vistas de列表
    
    Uso:
        class MiVista(FiltrosMixin, View):
            model = MiModelo
            campos_busqueda = ['nombre', 'email']
            campos_fecha = ['fecha_creacion']
            campos_estado = ['estado']
            campos_select = ['categoria']
    """
    
    # Configuración por defecto (sobrescribir en la vista)
    model = None
    campos_busqueda = []  # Lista de campos para búsqueda textual
    campos_fecha = []    # Lista de campos de fecha
    campos_estado = []   # Lista de campos de estado
    campos_select = []   # Lista de campos para filtros select
    template_filters = 'partials/filtros.html'  # Template de filtros
    
    def get_filtros_context(self, request, queryset):
        """
        Aplica todos los filtros y retorna (queryset, context)
        """
        context = {
            'filtros_activos': {},
            'buscar': '',
            'fecha_inicio': '',
            'fecha_fin': '',
            'estado': '',
        }
        
        # 1. Búsqueda textual
        buscar = request.GET.get('buscar', '').strip()
        if buscar and self.campos_busqueda:
            query = Q()
            for campo in self.campos_busqueda:
                query |= Q(**{f'{campo}__icontains': buscar})
            queryset = queryset.filter(query)
            context['buscar'] = buscar
            context['filtros_activos']['buscar'] = buscar
        
        # 2. Filtros por fecha
        for campo in self.campos_fecha:
            fecha_inicio = request.GET.get(f'{campo}_inicio')
            fecha_fin = request.GET.get(f'{campo}_fin')
            
            if fecha_inicio:
                try:
                    fecha_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                    queryset = queryset.filter(**{f'{campo}__gte': fecha_dt})
                    context['fecha_inicio'] = fecha_inicio
                    context['filtros_activos'][f'{campo}_inicio'] = fecha_inicio
                except ValueError:
                    pass
                    
            if fecha_fin:
                try:
                    fecha_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                    queryset = queryset.filter(**{f'{campo}__lte': fecha_dt})
                    context['fecha_fin'] = fecha_fin
                    context['filtros_activos'][f'{campo}_fin'] = fecha_fin
                except ValueError:
                    pass
        
        # 3. Filtros de estado
        for campo in self.campos_estado:
            estado = request.GET.get(campo)
            if estado:
                queryset = queryset.filter(**{campo: estado})
                context['estado'] = estado
                context['filtros_activos'][campo] = estado
        
        # 4. Filtros select
        for campo in self.campos_select:
            valor = request.GET.get(campo)
            if valor:
                queryset = queryset.filter(**{campo: valor})
                context['filtros_activos'][campo] = valor
        
        # 5.保留 filtros actuales en el context
        for key, value in request.GET.items():
            if value and key not in context['filtros_activos']:
                context['filtros_activos'][key] = value
        
        return queryset, context
    
    def render_con_filtros(self, request, template_name, queryset, extra_context=None):
        """
        Renderiza la plantilla con filtros aplicados
        """
        queryset, filtros_context = self.get_filtros_context(request, queryset)
        
        context = {**filtros_context}
        if extra_context:
            context.update(extra_context)
        
        return render(request, template_name, context)


def aplicar_filtros_basicos(request, queryset, config):
    """
    Función utility para aplicar filtros básicos sin necesidad de mixin
    
    Args:
        request: Objeto request de Django
        queryset: QuerySet base
        config: Dictionary con configuración:
            {
                'buscar': ['campo1', 'campo2'],  # Campos para búsqueda
                'fecha': 'campo_fecha',           # Campo de fecha (opcional)
                'estado': 'campo_estado',        # Campo de estado (opcional)
                'select': {'campo': Modelo.objects.all()},  # Opciones select
            }
    
    Returns:
        tuple: (queryset filtrado, dictionary de contexto)
    """
    context = {'filtros_activos': {}}
    
    # Búsqueda
    buscar = request.GET.get('buscar', '').strip()
    if buscar and config.get('buscar'):
        query = Q()
        for campo in config['buscar']:
            query |= Q(**{f'{campo}__icontains': buscar})
        queryset = queryset.filter(query)
        context['buscar'] = buscar
        context['filtros_activos']['buscar'] = buscar
    
    # Fecha
    fecha_config = config.get('fecha')
    if fecha_config:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio:
            try:
                fecha_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(**{f'{fecha_config}__gte': fecha_dt})
                context['fecha_inicio'] = fecha_inicio
                context['filtros_activos']['fecha_inicio'] = fecha_inicio
            except ValueError:
                pass
                
        if fecha_fin:
            try:
                fecha_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                queryset = queryset.filter(**{f'{fecha_config}__lte': fecha_dt})
                context['fecha_fin'] = fecha_fin
                context['filtros_activos']['fecha_fin'] = fecha_fin
            except ValueError:
                pass
    
    # Estado
    estado_config = config.get('estado')
    if estado_config:
        estado = request.GET.get('estado')
        if estado:
            queryset = queryset.filter(**{estado_config: estado})
            context['estado'] = estado
            context['filtros_activos']['estado'] = estado
    
    # Selects
    select_config = config.get('select', {})
    for campo, opciones in select_config.items():
        valor = request.GET.get(campo)
        if valor:
            queryset = queryset.filter(**{campo: valor})
            context['filtros_activos'][campo] = valor
    
    # Otros filtros GET
    for key, value in request.GET.items():
        if value and key not in context['filtros_activos'] and key not in ['buscar', 'fecha_inicio', 'fecha_fin', 'estado']:
            if hasattr(queryset.model, key):
                queryset = queryset.filter(**{key: value})
                context['filtros_activos'][key] = value
    
    return queryset, context


def generar_query_filtros(request, campos_permitidos=None):
    """
    Genera QuerySet parameters dinámicamente desde request.GET
    
    Args:
        request: Request object
        campos_permitidos: Lista de campos permitidos (None = todos)
    
    Returns:
        dict: Parámetros para filter()
    """
    params = {}
    campos_fecha = ['fecha', 'fecha_inicio', 'fecha_fin', 'created_at', 'updated_at']
    
    for key, value in request.GET.items():
        if not value:
            continue
            
        if campos_permitidos and key not in campos_permitidos:
            continue
            
        # Manejar fechas
        if key in campos_fecha or key.endswith('_fecha'):
            try:
                fecha_dt = datetime.strptime(value, '%Y-%m-%d').date()
                if key == 'fecha_inicio':
                    params[f'{key.replace("_inicio", "")}__gte'] = fecha_dt
                elif key == 'fecha_fin':
                    params[f'{key.replace("_fin", "")}__lte'] = fecha_dt
                else:
                    params[f'{key}__date'] = fecha_dt
            except ValueError:
                pass
        else:
            # Búsqueda textual con icontains
            if key == 'buscar':
                continue  # Manejado separadamente
            else:
                params[key] = value
    
    return params
