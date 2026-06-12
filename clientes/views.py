from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from usuarios.models import Suscripcion, Perfil, HistorialPeso, MetaUsuario
from usuarios.decorators import admin_required, admin_role_required
from ventas.models import Venta as VentaProducto
from .forms import SuscripcionForm
from planes.models import Plan
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
import io
import csv


@admin_required
def lista_clientes(request):
    # Obtener parámetros de filtro
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    buscar_normalizado = buscar.lower()

    def coincide_busqueda(perfil):
        if not buscar_normalizado:
            return True

        texto_busqueda = " ".join([
            perfil.user.username or '',
            perfil.user.email or '',
            perfil.user.get_full_name() or '',
            perfil.telefono or '',
            perfil.cedula or '',
            perfil.tarjeta or '',
        ]).lower()

        return buscar_normalizado in texto_busqueda

    # QuerySet base
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')

    # Obtener todos los clientes primero para filtrar por suscripción
    lista_clientes = []
    clientes_all = list(clientes)

    for perfil in clientes_all:
        if not coincide_busqueda(perfil):
            continue

        usuario = perfil.user
        historial_peso = HistorialPeso.objects.filter(usuario=usuario).order_by('-fecha').first()

        if perfil.peso is None and historial_peso is not None:
            perfil.peso = historial_peso.peso

        if perfil.estatura is None and historial_peso is not None:
            perfil.estatura = historial_peso.estatura

        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = next((suscripcion for suscripcion in suscripciones if suscripcion.esta_activa()), None)

        # Filtrar por plan
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue

        # Filtrar por estado de suscripción
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue

        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    planes = Plan.objects.all()
    
    # Opciones de estado para el filtro
    opciones_estado = [
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
    ]
    
    # Preparar filtros custom
    filtros_custom = [
        {
            'name': 'plan',
            'label': 'Plan',
            'opciones': [{'value': p.id, 'label': p.nombre} for p in planes],
            'value': plan
        }
    ]
    
    return render(request, 'clientes/lista_clientes.html', {
        'clientes_data': lista_clientes,
        'planes': planes,
        # Contexto para filtros
        'buscar': buscar,
        'estado': estado,
        'opciones_estado': opciones_estado,
        'filtros_custom': filtros_custom,
        'mostrar_buscar': True,
        'mostrar_fecha': False,
        'mostrar_estado': True,
    })




@admin_required
def detalle_plan_ajax(request, suscripcion_id):
    """Retorna los detalles de una suscripción para mostrar en modal"""
    suscripcion = get_object_or_404(Suscripcion.objects.select_related("plan", "usuario"), id=suscripcion_id)
    plan = suscripcion.plan
    
    dias_restantes = (suscripcion.fecha_fin - timezone.now().date()).days
    
    data = {
        "nombre_plan": plan.nombre,
        "precio": float(plan.precio),
        "duracion_dias": plan.duracion_dias,
        "descripcion": plan.descripcion,
        "fecha_inicio": suscripcion.fecha_inicio.strftime("%d/%m/%Y"),
        "fecha_fin": suscripcion.fecha_fin.strftime("%d/%m/%Y"),
        "dias_restantes": dias_restantes,
        "activa": suscripcion.activa,
        "usuario": suscripcion.usuario.get_full_name() or suscripcion.usuario.username,
        "tipo": plan.get_tipo_display() if plan.tipo else "N/A",
        "beneficios": [
            "Acceso ilimitado al gimnasio",
            "Clases grupales incluidas",
            "Área de pesas y cardio",
            "Vestuarios y duchas",
        ],
    }
    
    return JsonResponse(data)

@admin_required
def ver_cliente(request, id):
    perfil = get_object_or_404(Perfil, id=id)
    usuario = perfil.user
    
    suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
    suscripcion_activa = suscripciones.filter(activa=True).first()
    
    ventas_productos = VentaProducto.objects.filter(usuario=usuario)
    total_compras = ventas_productos.aggregate(total=Sum('total'))['total'] or 0
    cantidad_compras = ventas_productos.count()
    
    historial_peso = HistorialPeso.objects.filter(usuario=usuario)[:10]
    metas = MetaUsuario.objects.filter(usuario=usuario)[:10]
    
    return render(request, 'clientes/detalle_cliente.html', {
        'perfil': perfil,
        'usuario': usuario,
        'suscripciones': suscripciones,
        'suscripcion_activa': suscripcion_activa,
        'ventas_productos': ventas_productos[:10],
        'total_compras': total_compras,
        'cantidad_compras': cantidad_compras,
        'historial_peso': historial_peso,
        'metas': metas,
    })


@admin_required
def crear_cliente(request):

    if request.method == "POST":

        form = SuscripcionForm(request.POST)

        if form.is_valid():

            suscripcion = form.save(commit=False)

            # calcular fecha fin automáticamente
            suscripcion.fecha_inicio = timezone.now().date()

            suscripcion.fecha_fin = (
                suscripcion.fecha_inicio +
                timedelta(days=suscripcion.plan.duracion_dias)
            )

            suscripcion.save()

            return redirect('lista_clientes')

    else:
        form = SuscripcionForm()

    return render(request, 'clientes/crear_cliente.html', {
        'form': form
    })


@admin_required
def editar_cliente(request, id):

    cliente = get_object_or_404(Suscripcion, id=id)

    form = SuscripcionForm(request.POST or None, instance=cliente)

    if form.is_valid():
        form.save()
        return redirect('lista_clientes')

    return render(request, 'clientes/editar_cliente.html', {
        'form': form
    })

@admin_required

def eliminar_cliente(request, id):

    cliente = get_object_or_404(Suscripcion, id=id)
    nombre_usuario = cliente.usuario.username

    if request.method == "POST":
        cliente.delete()
        messages.success(request, f'✅ Suscripción de {nombre_usuario} eliminada correctamente.')
        return redirect('lista_clientes')

    return render(request, 'clientes/eliminar_cliente.html', {
        'cliente': cliente
    })


@admin_required
@require_POST
def desactivar_cliente(request, id):
    """Desactiva un usuario cliente"""
    usuario = get_object_or_404(User, id=id)
    usuario.is_active = False
    usuario.save()
    
    # Si es AJAX, retorna JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Usuario {usuario.username} desactivado correctamente',
            'is_active': usuario.is_active
        })
    
    messages.success(request, f'✅ Usuario {usuario.username} desactivado correctamente.')
    return redirect('lista_clientes')


@admin_required
@require_POST
def activar_cliente(request, id):
    """Activa un usuario cliente"""
    usuario = get_object_or_404(User, id=id)
    usuario.is_active = True
    usuario.save()
    
    # Si es AJAX, retorna JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Usuario {usuario.username} activado correctamente',
            'is_active': usuario.is_active
        })
    
    messages.success(request, f'✅ Usuario {usuario.username} activado correctamente.')
    return redirect('lista_clientes')


from django.contrib import messages


@admin_required
def limpiar_suscripciones(request):
    """Elimina todas las suscripciones de clientes"""
    if request.method == 'POST':
        count = Suscripcion.objects.count()
        Suscripcion.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} suscripciones correctamente.')
    return redirect('lista_clientes')
@admin_required


def limpiar_clientes(request):
    """Elimina todos los clientes (usuarios con rol cliente)"""
    if request.method == 'POST':
        count_perfiles = Perfil.objects.filter(rol='cliente').count()
        Perfil.objects.filter(rol='cliente').delete()
        messages.success(request, f'Se eliminaron {count_perfiles} clientes correctamente.')
    return redirect('lista_clientes')

@admin_role_required
def reporte_clientes_pdf(request):
    """Genera reporte PDF de clientes"""
    from io import BytesIO
    from django.db.models import Q
    
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')
    
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    
    # Aplicar mismos filtros que en lista_clientes
    if buscar:
        clientes = clientes.filter(
            Q(user__username__icontains=buscar) |
            Q(user__email__icontains=buscar) |
            Q(user__first_name__icontains=buscar) |
            Q(user__last_name__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(tarjeta__icontains=buscar)
        )
    
    lista_clientes = []
    for perfil in clientes:
        usuario = perfil.user
        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = suscripciones.filter(activa=True).first()
        
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue
        
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue
        
        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    template = get_template('clientes/reporte_clientes_pdf.html')
    html = template.render({
        'clientes_data': lista_clientes,
        'now': timezone.now()
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_clientes.pdf"'
    return response


@admin_role_required
def reporte_clientes_excel(request):
    """Exporta reporte de clientes a Excel (CSV)"""
    from django.db.models import Q
    
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')
    
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    
    # Aplicar mismos filtros
    if buscar:
        clientes = clientes.filter(
            Q(user__username__icontains=buscar) |
            Q(user__email__icontains=buscar) |
            Q(user__first_name__icontains=buscar) |
            Q(user__last_name__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(tarjeta__icontains=buscar)
        )
    
    lista_clientes = []
    for perfil in clientes:
        usuario = perfil.user
        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = suscripciones.filter(activa=True).first()
        
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue
        
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue
        
        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['REPORTE DE CLIENTES'])
    writer.writerow([])
    writer.writerow(['ID', 'Usuario', 'Nombre', 'Email', 'Teléfono', 'Plan', 'Estado Suscripción', 'Fecha Inicio', 'Fecha Fin'])
    
    for c in lista_clientes:
        usuario = c['usuario']
        suscripcion = c['suscripcion_activa']
        
        plan_nombre = suscripcion.plan.nombre if suscripcion else 'Sin plan'
        estado_susc = 'Activa' if suscripcion else 'Sin suscripción'
        fecha_inicio = suscripcion.fecha_inicio.strftime('%d/%m/%Y') if suscripcion and suscripcion.fecha_inicio else '-'
        fecha_fin = suscripcion.fecha_fin.strftime('%d/%m/%Y') if suscripcion and suscripcion.fecha_fin else '-'
        
        writer.writerow([
            usuario.id,
            usuario.username,
            f"{usuario.first_name} {usuario.last_name}".strip() or '-',
            usuario.email,
            c['perfil'].telefono or '-',
            plan_nombre,
            estado_susc,
            fecha_inicio,
            fecha_fin
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_clientes.csv"'
    return response