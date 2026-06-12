from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from .models import Proveedor, Devolucion
from .forms import DevolucionForm, ProveedorProductoForm
from productos.models import Producto
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from usuarios.decorators import admin_required
import io
import csv


@admin_required
def reporte_devoluciones_pdf(request):
    """Reporte PDF de devoluciones"""
    from io import BytesIO
    devoluciones = Devolucion.objects.select_related('proveedor').all()
    
    estado = request.GET.get('estado')
    proveedor_id = request.GET.get('proveedor')
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    if proveedor_id:
        devoluciones = devoluciones.filter(proveedor_id=proveedor_id)
    
    template = get_template('proveedores/reporte_devoluciones_pdf.html')
    html = template.render({
        'devoluciones': devoluciones,
        'now': now()
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_devoluciones.pdf"'
    return response


@admin_required
def reporte_devoluciones_excel(request):
    """Reporte Excel de devoluciones"""
    devoluciones = Devolucion.objects.select_related('proveedor').all()
    
    estado = request.GET.get('estado')
    proveedor_id = request.GET.get('proveedor')
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    if proveedor_id:
        devoluciones = devoluciones.filter(proveedor_id=proveedor_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['REPORTE DE DEVOLUCIONES'])
    writer.writerow([])
    writer.writerow(['ID', 'Proveedor', 'Producto', 'Cantidad', 'Motivo', 'Estado', 'Fecha'])
    
    for d in devoluciones:
        writer.writerow([
            d.id,
            d.proveedor.nombre if d.proveedor else 'Sin proveedor',
            d.producto.nombre if d.producto else 'Sin producto',
            d.cantidad,
            d.get_motivo_display(),
            d.estado,
            d.fecha_devolucion.strftime('%d/%m/%Y') if d.fecha_devolucion else ''
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_devoluciones.csv"'
    return response


@admin_required
def reporte_proveedores_pdf(request):
    from io import BytesIO
    proveedores = Proveedor.objects.all()

    nombre = request.GET.get("nombre")
    telefono = request.GET.get("telefono")
    correo = request.GET.get("correo")
    estado = request.GET.get("estado")

    if nombre:
        proveedores = proveedores.filter(nombre__icontains=nombre)

    if telefono:
        proveedores = proveedores.filter(telefono__icontains=telefono)

    if correo:
        proveedores = proveedores.filter(email__icontains=correo)

    if estado:
        proveedores = proveedores.filter(estado=estado)

    template = get_template('proveedores/reporte_pdf.html')
    html = template.render({
        'proveedores': proveedores,
        'now': now()
    })

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_proveedores.pdf"'
    return response


@admin_required
def reporte_proveedores_excel(request):
    proveedores = Proveedor.objects.all()

    nombre = request.GET.get("nombre")
    telefono = request.GET.get("telefono")
    correo = request.GET.get("correo")
    estado = request.GET.get("estado")

    if nombre:
        proveedores = proveedores.filter(nombre__icontains=nombre)
    if telefono:
        proveedores = proveedores.filter(telefono__icontains=telefono)
    if correo:
        proveedores = proveedores.filter(email__icontains=correo)
    if estado:
        proveedores = proveedores.filter(estado=estado)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['REPORTE DE PROVEEDORES'])
    writer.writerow([])
    writer.writerow(['ID', 'Nombre', 'Teléfono', 'Email', 'Dirección', 'Ciudad', 'Estado'])

    for p in proveedores:
        writer.writerow([
            p.id_proveedor,
            p.nombre,
            p.telefono,
            p.email,
            p.direccion,
            p.ciudad or '',
            p.estado
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_proveedores.csv"'
    return response


@admin_required
def lista_proveedores(request):

    proveedores = Proveedor.objects.all()

    nombre = request.GET.get('nombre')
    telefono = request.GET.get('telefono')
    email= request.GET.get('email')
    estado = request.GET.get('estado')

    if nombre:
        proveedores = proveedores.filter(nombre__icontains=nombre)

    if telefono:
        proveedores = proveedores.filter(telefono__icontains=telefono)

    if email:
        proveedores = proveedores.filter(correo__icontains=email)

    if estado:
        proveedores = proveedores.filter(estado=estado)

    return render(request, 'proveedores/lista_proveedores.html', {
        'proveedores': proveedores
    })


@admin_required
def crear_proveedor(request):

    if request.method == "POST":

        nombre = request.POST['nombre']
        telefono = request.POST['telefono']
        email = request.POST['email']
        direccion = request.POST['direccion']
        estado = 'activo' if request.POST.get('estado') else 'inactivo'

        proveedor = Proveedor.objects.create(
            nombre=nombre,
            telefono=telefono,
            email=email,
            direccion=direccion,
            estado=estado
        )

        productos_seleccionados = request.POST.getlist('productos')
        if productos_seleccionados:
            productos = Producto.objects.filter(id_producto__in=productos_seleccionados)
            proveedor.productos.set(productos)

        return redirect('lista_proveedores')

    productos = Producto.objects.all()
    return render(request, 'proveedores/form_proveedor.html', {
        'productos': productos
    })


@admin_required
def editar_proveedor(request, id):

    proveedor = get_object_or_404(Proveedor, id_proveedor=id)

    if request.method == "POST":

        proveedor.nombre = request.POST['nombre']
        proveedor.telefono = request.POST['telefono']
        proveedor.email = request.POST['email']
        proveedor.direccion = request.POST['direccion']
        proveedor.estado = 'activo' if request.POST.get('estado') else 'inactivo'

        proveedor.save()

        productos_seleccionados = request.POST.getlist('productos')
        if productos_seleccionados:
            productos = Producto.objects.filter(id_producto__in=productos_seleccionados)
            proveedor.productos.set(productos)
        else:
            proveedor.productos.clear()

        return redirect('lista_proveedores')

    productos = Producto.objects.all()
    return render(request, 'proveedores/form_proveedor.html', {
        'proveedor': proveedor,
        'productos': productos
    })


@admin_required
def toggle_proveedor(request, id):

    proveedor = Proveedor.objects.get(id_proveedor=id)

    if proveedor.estado == "activo":
        proveedor.estado = "inactivo"
    else:
        proveedor.estado = "activo"

    proveedor.save()

    return redirect('lista_proveedores')


@admin_required
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id_proveedor=id)
    proveedor.delete()
    messages.success(request, 'Proveedor eliminado correctamente')
    return redirect('lista_proveedores')


@admin_required
def lista_devoluciones(request):
    """Lista todas las devoluciones"""
    devoluciones = Devolucion.objects.select_related('proveedor', 'producto').all()
    
    estado = request.GET.get('estado')
    proveedor_id = request.GET.get('proveedor')
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
    if proveedor_id:
        devoluciones = devoluciones.filter(proveedor_id=proveedor_id)
    
    proveedores = Proveedor.objects.filter(estado='activo').prefetch_related('productos')
    
    return render(request, 'proveedores/lista_devoluciones.html', {
        'devoluciones': devoluciones,
        'proveedores': proveedores
    })


@admin_required
@transaction.atomic
def crear_devolucion(request):
    """Crea una nueva devolución y envía correo al proveedor"""
    if request.method == 'POST':
        form = DevolucionForm(request.POST, request.FILES)
        
        proveedor_id = request.POST.get('proveedor')
        producto_id = request.POST.get('producto')
        
        proveedor = None
        producto = None
        
        if proveedor_id:
            try:
                proveedor = Proveedor.objects.get(id_proveedor=proveedor_id)
            except Proveedor.DoesNotExist:
                messages.error(request, "El proveedor seleccionado no existe.")
                return render(request, 'proveedores/crear_devolucion.html', {
                    'form': form,
                    'proveedores': Proveedor.objects.filter(estado='activo').prefetch_related('productos')
                })
        
        if producto_id:
            try:
                producto = Producto.objects.get(id_producto=producto_id)
            except Producto.DoesNotExist:
                messages.error(request, "El producto seleccionado no existe.")
                return render(request, 'proveedores/crear_devolucion.html', {
                    'form': form,
                    'proveedores': Proveedor.objects.filter(estado='activo').prefetch_related('productos')
                })
        
        if form.is_valid():
            cantidad = form.cleaned_data.get('cantidad', 0)
            
            if cantidad <= 0:
                messages.error(request, "La cantidad debe ser mayor a 0.")
                return render(request, 'proveedores/crear_devolucion.html', {
                    'form': form,
                    'proveedores': Proveedor.objects.filter(estado='activo').prefetch_related('productos')
                })
            
            devolucion = form.save()
            
            if producto and producto.stock_actual >= cantidad:
                producto.stock_actual -= cantidad
                producto.save()
            
            try:
                motivo_display = dict(Devolucion.MOTIVO_CHOICES).get(devolucion.motivo, devolucion.motivo)
                estado_display = dict(Devolucion.ESTADO_CHOICES).get(devolucion.estado, devolucion.estado)
                
                host = request.get_host()
                if not host or 'localhost' in host or '127.0.0.1' in host:
                    base_url = 'http://localhost:8000'
                else:
                    base_url = f'{request.scheme}://{host}'
                
                base_url = base_url.rstrip('/')
                link_aprobar = f"{base_url}/proveedores/devolucion/{devolucion.token}/aprobar/"
                link_rechazar = f"{base_url}/proveedores/devolucion/{devolucion.token}/rechazar/"
                link_ver = f"{base_url}/proveedores/devolucion/{devolucion.token}/ver/"
                
                producto_nombre = devolucion.producto.nombre if devolucion.producto else "Sin producto"
                producto_info = f"<p style=\"margin: 5px 0;\"><strong>Producto:</strong> {producto_nombre}</p>" if devolucion.producto else "<p style=\"margin: 5px 0;\"><strong>Producto:</strong> No especificado</p>"
                
                html_mensaje = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; background-color: #111111; color: #ffffff; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #1a1a1a; border-radius: 15px; padding: 25px;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #DC3545, #A71D2A); border-radius: 15px; padding: 25px; text-align: center; margin-bottom: 25px;">
            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">🔄 Solicitud de Devolución</h1>
            <p style="margin: 10px 0 0; color: #cccccc;">Gym Xtreme</p>
        </div>

        <!-- Detalles -->
        <div style="margin-bottom: 20px;">
            <h3 style="color: #DC3545; border-bottom: 1px solid #333; padding-bottom: 10px;">📦 Detalles del Producto</h3>
            {producto_info}
            <p style="margin: 5px 0;"><strong>Cantidad:</strong> {devolucion.cantidad} unidad(es)</p>
            <p style="margin: 5px 0;"><strong>Motivo:</strong> {motivo_display}</p>
            <p style="margin: 5px 0;"><strong>Descripción:</strong> {devolucion.descripcion}</p>
            <p style="margin: 5px 0;"><strong>Fecha:</strong> {devolucion.fecha_devolucion.strftime('%d/%m/%Y %H:%M')}</p>
            {'<p style="margin: 5px 0;"><strong>Imagen:</strong> Disponible en el sistema</p>' if devolucion.imagen else ''}
            <p style="margin: 5px 0; color: #888;">{f"Notas: {devolucion.notas_admin}" if devolucion.notas_admin else ""}</p>
        </div>

        <!-- Botones de Acción -->
        <div style="background-color: #222222; border-radius: 10px; padding: 20px; text-align: center; margin: 25px 0;">
            <h3 style="color: #ffffff; margin-top: 0;">✋ Responda esta Solicitud</h3>
            <p style="color: #cccccc; margin-bottom: 20px;">¿Acepta o rechaza esta devolución?</p>
            
            <a href="{link_aprobar}" style="display: inline-block; background-color: #198754; color: #ffffff; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; margin: 5px;">✅ Aprobar</a>
            
            <a href="{link_rechazar}" style="display: inline-block; background-color: #DC3545; color: #ffffff; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; margin: 5px;">❌ Rechazar</a>
            
            <p style="color: #666666; font-size: 12px; margin-top: 15px;">
                Al hacer clic en un botón, podrá escribir el motivo de su respuesta
            </p>
        </div>

        <!-- Ver Detalles -->
        <div style="text-align: center; margin-top: 20px;">
            <a href="{link_ver}" style="color: #DC3545; text-decoration: underline;">Ver todos los detalles</a>
        </div>

        <!-- Footer -->
        <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #333; color: #666666; font-size: 12px;">
            <p>Este es un correo automático de Gym Xtreme</p>
        </div>

    </div>
</body>
</html>
"""
                
                from django.core.mail import EmailMessage
                email = EmailMessage(
                    subject=f'[Gym Xtreme] Solicitud de Devolución - {producto_nombre}',
                    body=html_mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else settings.EMAIL_HOST_USER,
                    to=[devolucion.proveedor.email],
                )
                email.content_subtype = 'html'
                email.send(fail_silently=False)
                
                messages.success(request, f'✅ Devolución creada y notificación enviada a {devolucion.proveedor.email}')
            except Exception as e:
                import logging
                logging.error(f"Error al enviar correo de devolución: {str(e)}")
                messages.warning(request, f'⚠️ Devolución creada pero falló el envío de correo: {str(e)}')
            
            return redirect('lista_devoluciones')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = DevolucionForm()
    
    proveedores = Proveedor.objects.filter(estado='activo').prefetch_related('productos')
    
    return render(request, 'proveedores/crear_devolucion.html', {
        'form': form,
        'proveedores': proveedores
    })


def responder_devolucion(request, token, accion):
    """Vista pública para que el proveedor responda la devolución"""
    devolucion = get_object_or_404(Devolucion, token=token)
    
    if accion == 'ver':
        return render(request, 'proveedores/devolucion_publica.html', {
            'devolucion': devolucion
        })
    
    if accion not in ['aprobar', 'rechazar']:
        return render(request, 'proveedores/devolucion_error.html', {
            'error': 'Acción inválida'
        })
    
    if request.method == 'POST':
        motivo_respuesta = request.POST.get('motivo', '').strip()
        
        if accion == 'aprobar':
            devolucion.estado = 'aprobada'
            mensaje_respuesta = 'La devolución ha sido APROBADA'
        else:
            devolucion.estado = 'rechazada'
            mensaje_respuesta = 'La devolución ha sido RECHAZADA'
        
        devolucion.respuesta_proveedor = motivo_respuesta
        devolucion.fecha_respuesta = now()
        devolucion.save()
        
        return render(request, 'proveedores/devolucion_respuesta.html', {
            'devolucion': devolucion,
            'mensaje': mensaje_respuesta,
            'accion': accion
        })
    
    return render(request, 'proveedores/devolucion_responder.html', {
        'devolucion': devolucion,
        'accion': accion
    })


@admin_required
def detalle_devolucion(request, id):
    """Ver detalle de una devolución"""
    devolucion = get_object_or_404(Devolucion, id=id)
    return render(request, 'proveedores/detalle_devolucion.html', {
        'devolucion': devolucion
    })


@admin_required
def actualizar_estado_devolucion(request, id):
    """Actualiza el estado de una devolución"""
    devolucion = get_object_or_404(Devolucion, id=id)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in ['pendiente', 'aprobada', 'rechazada', 'completada']:
            devolucion.estado = nuevo_estado
            devolucion.save()
            messages.success(request, f'✅ Estado actualizado a {nuevo_estado}')
    
    return redirect('detalle_devolucion', id=id)


@admin_required
def eliminar_devolucion(request, id):
    """Elimina una devolución (solo si no está pendiente)"""
    devolucion = get_object_or_404(Devolucion, id=id)
    
    if devolucion.estado == 'pendiente':
        messages.error(request, '⚠️ No puedes eliminar una devolución pendiente')
        return redirect('detalle_devolucion', id=id)
    
    devolucion.delete()
    messages.success(request, '✅ Devolución eliminada correctamente')
    return redirect('lista_devoluciones')


@admin_required
def limpiar_proveedores(request):
    """Elimina todos los proveedores"""
    if request.method == 'POST':
        count = Proveedor.objects.count()
        Proveedor.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} proveedores correctamente.')
    return redirect('lista_proveedores')
