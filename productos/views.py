"""
VISTAS DE PRODUCTOS - SISTEMA GYM DJANGO
Gestión de productos, lotes, alertas y reportes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.utils.timezone import now
from django.db.models import Count, F, Sum, Q, Max
from django.views.decorators.http import require_POST
from io import BytesIO
import csv
import json

from .models import Producto, Categoria, Lote, AlertaLote, HistorialInventario
from usuarios.decorators import admin_required

try:
    from xhtml2pdf import pisa
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


# ============================================================================
# VISTAS DE GESTIÓN DE PRODUCTOS (CRUD)
# ============================================================================

@admin_required
def lista_productos(request):
    """Lista todos los productos con estadísticas"""
    productos = Producto.objects.all().prefetch_related('lotes').annotate(
        ultima_fecha_fabricacion=Max('lotes__fecha_fabricacion')
    )
    
    # Filtros
    nombre = request.GET.get('nombre', '').strip()
    estado = request.GET.get('estado', '').strip()
    
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if estado:
        productos = productos.filter(estado=estado)
    
    # Estadísticas
    total_stock = productos.aggregate(total=Sum('stock_actual'))['total'] or 0
    total_lotes = Lote.objects.filter(estado='disponible').count()
    total_alertas = AlertaLote.objects.filter(activa=True).count()
    
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'total_productos': productos.count(),
        'total_stock': total_stock,
        'total_lotes': total_lotes,
        'total_alertas': total_alertas,
    }
    
    return render(request, 'productos/lista_productos.html', context)


@admin_required
def crear_producto(request):
    """Crear un nuevo producto"""
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            categoria_id = request.POST.get('categoria')
            precio_costo = request.POST.get('precio_costo', '0').strip()
            precio_venta = request.POST.get('precio_venta', '0').strip()
            stock_actual = request.POST.get('stock_actual', request.POST.get('stock_inicial', '0')).strip()
            estado = request.POST.get('estado', 'activo')
            imagen = request.FILES.get('imagen')
            
            if not nombre:
                messages.error(request, 'El nombre del producto es obligatorio.')
                return render(request, 'productos/crear_producto.html', {'categorias': categorias})
            
            if Producto.objects.filter(nombre=nombre).exists():
                messages.error(request, f'Ya existe un producto con el nombre "{nombre}".')
                return render(request, 'productos/crear_producto.html', {'categorias': categorias})
            
            categoria = None
            if categoria_id:
                categoria = get_object_or_404(Categoria, id=categoria_id)
            
            # Convert to appropriate types, handling empty strings
            try:
                precio_costo_float = float(precio_costo) if precio_costo else 0
            except ValueError:
                precio_costo_float = 0
                
            try:
                precio_venta_float = float(precio_venta) if precio_venta else 0
            except ValueError:
                precio_venta_float = 0
                
            try:
                stock_actual_int = int(stock_actual) if stock_actual else 0
            except ValueError:
                stock_actual_int = 0
            
            producto = Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                precio_costo=precio_costo_float,
                precio_venta=precio_venta_float,
                stock_actual=stock_actual_int,
                estado=estado,
                imagen=imagen
            )
            
            messages.success(request, f'✅ Producto "{nombre}" creado correctamente.')
            return redirect('lista_productos')
            
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
    
    return render(request, 'productos/crear_producto.html', {'categorias': categorias})


@admin_required
def editar_producto(request, id):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, id_producto=id)
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            producto.nombre = request.POST.get('nombre', producto.nombre).strip()
            producto.descripcion = request.POST.get('descripcion', producto.descripcion).strip()
            
            categoria_id = request.POST.get('categoria')
            if categoria_id:
                producto.categoria = get_object_or_404(Categoria, id=categoria_id)
            
            if request.POST.get('precio_costo'):
                producto.precio_costo = float(request.POST.get('precio_costo'))
            if request.POST.get('precio_venta'):
                producto.precio_venta = float(request.POST.get('precio_venta'))
            if request.POST.get('stock_actual'):
                producto.stock_actual = int(request.POST.get('stock_actual'))
            
            producto.estado = request.POST.get('estado', producto.estado)
            
            if request.FILES.get('imagen'):
                producto.imagen = request.FILES.get('imagen')
            
            producto.save()
            
            messages.success(request, f'✅ Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('lista_productos')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    context = {
        'producto': producto,
        'categorias': categorias,
    }
    
    return render(request, 'productos/form_producto.html', context)


@admin_required
def toggle_producto(request, id):
    """Activar/desactivar un producto"""
    producto = get_object_or_404(Producto, id_producto=id)
    producto.estado = 'inactivo' if producto.estado == 'activo' else 'activo'
    producto.save()
    
    estado_txt = 'activado' if producto.estado == 'activo' else 'desactivado'
    messages.success(request, f'✅ Producto "{producto.nombre}" {estado_txt}.')
    
    return redirect('lista_productos')


@admin_required
def toggle_producto_ajax(request, id):
    """Activar/desactivar un producto (AJAX)"""
    if request.method == 'POST':
        try:
            producto = get_object_or_404(Producto, id_producto=id)
            producto.estado = 'inactivo' if producto.estado == 'activo' else 'activo'
            producto.save()
            
            return JsonResponse({
                'success': True,
                'nuevo_estado': producto.estado,
                'mensaje': f'Producto {producto.estado}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@admin_required
def eliminar_producto(request, id):
    """Eliminar un producto"""
    producto = get_object_or_404(Producto, id_producto=id)
    nombre = producto.nombre
    producto.delete()
    
    messages.success(request, f'✅ Producto "{nombre}" eliminado.')
    return redirect('lista_productos')


@admin_required
def crear_categoria(request):
    """Crear una nueva categoría"""
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8') or '{}')
                nombre = payload.get('nombre', '').strip()
                descripcion = payload.get('descripcion', '').strip()
            else:
                nombre = request.POST.get('nombre', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
            
            if not nombre:
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'}, status=400)
                messages.error(request, 'El nombre es obligatorio.')
                return render(request, 'productos/crear_categoria.html')
            
            if Categoria.objects.filter(nombre=nombre).exists():
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': f'Ya existe: "{nombre}".'}, status=400)
                messages.error(request, f'Ya existe: "{nombre}".')
                return render(request, 'productos/crear_categoria.html')
            
            categoria = Categoria.objects.create(nombre=nombre, descripcion=descripcion)
            
            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'categoria': {'id': categoria.id, 'nombre': categoria.nombre}})
            
            messages.success(request, f'✅ Categoría "{nombre}" creada.')
            return redirect('lista_productos')
            
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'productos/crear_categoria.html')
    
    return render(request, 'productos/crear_categoria.html')


@admin_required
@require_POST
def limpiar_productos(request):
    """Limpiar productos (con confirmación)"""
    try:
        if request.POST.get('confirmacion') != 'si':
            messages.error(request, 'Confirmación requerida.')
            return redirect('lista_productos')
        
        count = Producto.objects.count()
        Producto.objects.all().delete()
        
        messages.success(request, f'✓ Se eliminaron {count} productos.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('lista_productos')


# ============================================================================
# VISTAS DE DETALLE Y CATÁLOGO
# ============================================================================

@admin_required
def detalle_producto(request, id):
    """Vista detallada de un producto con sus lotes"""
    producto = get_object_or_404(Producto, id_producto=id)
    lotes = Lote.objects.filter(producto=producto).order_by('fecha_vencimiento')
    from django.utils.timezone import now
    current_date = now().date()
    
    # Filtrar lotes por estado real basado en fechas
    es_consumible = producto.categoria.es_consumible if producto.categoria else False

    if es_consumible:
        lotes_disponibles = lotes.filter(estado='disponible', fecha_vencimiento__gte=current_date)
        lotes_vencidos = lotes.filter(fecha_vencimiento__lt=current_date) | lotes.filter(estado='vencido')
    else:
        lotes_disponibles = lotes.filter(estado='disponible')
        lotes_vencidos = lotes.filter(estado='vencido')
    lotes_vencidos = lotes_vencidos.distinct()
    ultimo_lote = lotes.filter(fecha_compra__isnull=False).order_by('-fecha_compra').first() or lotes.last()
    total_stock_lotes = sum(l.cantidad for l in lotes_disponibles)
    
    # Determinar el estado actual del producto basado en los lotes
    # Verificar si el producto tiene lotes vencidos
    tiene_lotes_vencidos = lotes_vencidos.exists()
    
    # Verificar si el producto tiene lotes disponibles (no vencidos)
    tiene_lotes_disponibles = lotes_disponibles.exists()
    
    # Determinar si el producto está vencido (todos los lotes vencidos o no hay lotes)
    producto_esta_vencido = producto.esta_vencido()
    
    # Determinar si el producto está disponible para la venta
    producto_disponible = producto.tiene_lotes_vigentes() and producto.stock_actual > 0
    
    context = {
        'producto': producto,
        'lotes': lotes,
        'lotes_disponibles': lotes_disponibles,
        'lotes_vencidos': lotes_vencidos,
        'total_stock_lotes': total_stock_lotes,
        'cantidad_lotes': lotes.count(),
        'ultimo_lote': ultimo_lote,
        'producto_esta_vencido': producto_esta_vencido,
        'producto_disponible': producto_disponible,
        'tiene_lotes_vencidos': tiene_lotes_vencidos,
        'tiene_lotes_disponibles': tiene_lotes_disponibles,
    }
    
    return render(request, 'productos/detalle_producto.html', context)


def catalogo(request):
    """Catálogo público de productos"""
    # Filtro por categoría
    categoria_nombre = request.GET.get('categoria', '').strip() or None

    # Productos activos
    productos = Producto.objects.filter(estado='activo')

    if categoria_nombre:
        productos = productos.filter(categoria__nombre__iexact=categoria_nombre)

    # Preparar datos
    productos_con_estado = []
    for producto in productos:
        # Calcular si tiene lotes vigentes
        tiene_vigentes = producto.tiene_lotes_vigentes()
        esta_vencido = producto.esta_vencido()

        # Stock disponible
        if producto.tiene_lotes():
            stock = producto.stock_total_lotes()
        else:
            stock = producto.stock_actual

        # Solo mostrar si hay stock
        if stock > 0 or tiene_vigentes:
            productos_con_estado.append({
                'producto': producto,
                'esta_vencido': esta_vencido,
                'stock_disponible': stock,
            })

    # Categorias con conteo de productos activos
    from django.db.models import Count
    categorias = Categoria.objects.annotate(
        total=Count('productos', filter=Q(productos__estado='activo'))
    )

    context = {
        'productos': productos_con_estado,
        'categorias': categorias,
        'categoria_seleccionada': categoria_nombre,
    }

    return render(request, 'productos/tienda/catalogo.html', context)


# ============================================================================
# VISTAS DE CARRITO (SESIÓN)
# ============================================================================

@login_required
def ver_carrito(request):
    """Ver carrito de compras"""
    carrito = request.session.get('carrito', {})
    total = 0
    
    for key, item in carrito.items():
        subtotal = float(item.get('precio', 0)) * int(item.get('cantidad', 1))
        item['subtotal'] = subtotal
        total += subtotal
    
    context = {
        'carrito': carrito,
        'total': total,
    }
    
    return render(request, 'productos/tienda/carrito.html', context)


@login_required
def agregar_carrito(request, id):
    """Agregar producto al carrito"""
    producto = get_object_or_404(Producto, id_producto=id)
    cantidad = int(request.POST.get('cantidad', 1))
    
    if cantidad <= 0:
        messages.error(request, 'Cantidad debe ser > 0.')
        return redirect('catalogo')
    
    # Validar no vencido
    if producto.esta_vencido():
        messages.error(request, f'"{producto.nombre}" está vencido.')
        return redirect('catalogo')
    
    # Stock disponible
    if producto.tiene_lotes():
        stock = producto.stock_total_lotes()
    else:
        stock = producto.stock_actual
    
    if stock <= 0:
        messages.error(request, 'Sin stock disponible.')
        return redirect('catalogo')
    
    carrito = request.session.get('carrito', {})
    
    # Verificar cantidad
    cant_actual = 0
    if str(id) in carrito:
        cant_actual = carrito[str(id)]['cantidad']
    
    if cant_actual + cantidad > stock:
        messages.error(request, f'Stock insuficiente: {stock} disponible.')
        return redirect('catalogo')
    
    # Agregar
    if str(id) in carrito:
        carrito[str(id)]['cantidad'] += cantidad
    else:
        carrito[str(id)] = {
            'id': id,
            'nombre': producto.nombre,
            'precio': float(producto.precio_venta),
            'cantidad': cantidad,
            'imagen': producto.imagen.url if producto.imagen else '',
        }
    
    request.session['carrito'] = carrito
    messages.success(request, f'"{producto.nombre}" agregado al carrito.')
    
    return redirect('catalogo')


@login_required
def eliminar_carrito(request, id):
    """Eliminar del carrito"""
    carrito = request.session.get('carrito', {})
    if str(id) in carrito:
        del carrito[str(id)]
    request.session['carrito'] = carrito
    messages.success(request, 'Eliminado del carrito.')
    return redirect('ver_carrito')


@login_required
def sumar_producto(request, id):
    """Aumentar cantidad en carrito"""
    carrito = request.session.get('carrito', {})
    
    if str(id) in carrito:
        producto = get_object_or_404(Producto, id_producto=id)
        
        # Validar no vencido
        if producto.esta_vencido():
            del carrito[str(id)]
            request.session['carrito'] = carrito
            messages.error(request, f'"{producto.nombre}" está vencido.')
            return redirect('ver_carrito')
        
        # Stock
        if producto.tiene_lotes():
            stock = producto.stock_total_lotes()
        else:
            stock = producto.stock_actual
        
        if carrito[str(id)]['cantidad'] < stock:
            carrito[str(id)]['cantidad'] += 1
        else:
            messages.warning(request, 'Stock insuficiente.')
    
    request.session['carrito'] = carrito
    return redirect('ver_carrito')


@login_required
def restar_producto(request, id):
    """Disminuir cantidad en carrito"""
    carrito = request.session.get('carrito', {})
    
    if str(id) in carrito:
        carrito[str(id)]['cantidad'] -= 1
        
        if carrito[str(id)]['cantidad'] <= 0:
            del carrito[str(id)]
            messages.success(request, 'Eliminado del carrito.')
    
    request.session['carrito'] = carrito
    return redirect('ver_carrito')


@login_required
def pago_carrito(request):
    """Procesar pago"""
    carrito = request.session.get('carrito', {})
    
    if not carrito:
        messages.error(request, 'Carrito vacío.')
        return redirect('catalogo')
    
    if request.method == 'POST':
        try:
            total = 0
            for key, item in carrito.items():
                subtotal = float(item['precio']) * int(item['cantidad'])
                total += subtotal
            
            # Aquí iría lógica de consumo de stock
            # Por ahora solo limpiamos
            request.session['carrito'] = {}
            
            messages.success(request, f'✅ ¡Pago exitoso!')
            return redirect('catalogo')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('ver_carrito')
    
    total = 0
    for key, item in carrito.items():
        total += float(item['precio']) * int(item['cantidad'])
    
    context = {
        'carrito': carrito,
        'total': total,
    }
    
    return render(request, 'productos/tienda/pago_carrito.html', context)


# ============================================================================
# VISTAS DE ALERTAS
# ============================================================================

@admin_required
def marcar_alerta_leida(request, alerta_id):
    """Marcar una alerta como leída"""
    if request.method == 'POST':
        try:
            alerta = get_object_or_404(AlertaLote, id_alerta=alerta_id)
            alerta.leida = True
            alerta.save()
            messages.success(request, 'Alerta marcada como leída.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('alertas_lotes')


@admin_required
def desactivar_alerta(request, alerta_id):
    """Desactivar una alerta"""
    if request.method == 'POST':
        try:
            alerta = get_object_or_404(AlertaLote, id_alerta=alerta_id)
            alerta.activa = False
            alerta.save()
            messages.success(request, 'Alerta desactivada.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('alertas_lotes')


@admin_required
def alertas_lotes_prox_vencer(request):
    """Alertas de lotes próximos a vencer"""
    lotes = Lote.objects.filter(estado='disponible').order_by('fecha_vencimiento')
    
    # Clasificar
    alertas_criticas = []  # ≤ 7 días
    alertas_altas = []     # 8-14 días
    alertas_medias = []    # 15-30 días
    alertas_bajas = []     # > 30 días
    
    for lote in lotes:
        dias = lote.dias_para_vencer()
        
        lote_info = {
            'lote': lote,
            'producto': lote.producto,
            'dias_restantes': dias,
            'numero_lote': lote.numero_lote,
            'cantidad': lote.cantidad,
            'fecha_fabricacion': lote.fecha_fabricacion,
            'fecha_vencimiento': lote.fecha_vencimiento,
            'fecha_compra': lote.fecha_compra,
            'precio_unitario_fmt': lote.precio_unitario_fmt if hasattr(lote, 'precio_unitario_fmt') else "${:,.2f}".format(float(lote.precio_unitario)),
        }
        
        if dias <= 0:
            # Lotes vencidos van a críticas (rojo) para atención inmediata
            alertas_criticas.append(lote_info)
        elif dias <= 7:
            alertas_criticas.append(lote_info)
        elif dias <= 14:
            alertas_altas.append(lote_info)
        elif dias <= 30:
            alertas_medias.append(lote_info)
        else:
            alertas_bajas.append(lote_info)
    
    total = len(alertas_criticas) + len(alertas_altas) + len(alertas_medias) + len(alertas_bajas)
    
    context = {
        'alertas_criticas': alertas_criticas,
        'alertas_altas': alertas_altas,
        'alertas_medias': alertas_medias,
        'alertas_bajas': alertas_bajas,
        'total_alertas': total,
        'total_criticas': len(alertas_criticas),
        'total_altas': len(alertas_altas),
        'total_medias': len(alertas_medias),
        'total_bajas': len(alertas_bajas),
    }
    
    return render(request, 'productos/alertas_lotes.html', context)


@admin_required
@require_POST
def limpiar_alertas_lotes(request):
    """Limpiar todas las alertas"""
    try:
        if request.POST.get('confirmacion') != 'si':
            messages.error(request, 'Confirmación requerida.')
            return redirect('alertas_lotes')
        
        count = AlertaLote.objects.count()
        AlertaLote.objects.all().delete()
        
        messages.success(request, f'✓ Se eliminaron {count} alertas.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('alertas_lotes')


@admin_required
def alertas_stock(request):
    """Alertas de stock bajo"""
    productos = Producto.objects.filter(stock_actual__lte=10).order_by('stock_actual')
    
    context = {
        'productos_bajo_stock': productos,
        'total': productos.count(),
    }
    
    return render(request, 'productos/alertas_stock.html', context)


@admin_required
def historial_inventario(request):
    """Historial de movimientos de inventario"""
    historial = HistorialInventario.objects.all().order_by('-fecha')[:100]
    
    context = {
        'historial': historial,
        'total': historial.count(),
    }
    
    return render(request, 'productos/historial_inventario.html', context)


# ============================================================================
# VISTAS DE REPORTES
# ============================================================================

@admin_required
def reporte_productos_pdf(request):
    """Reporte PDF de productos"""
    if not HAS_PDF:
        messages.error(request, 'xhtml2pdf no instalado.')
        return redirect('lista_productos')
    
    # Obtener productos con sus lotes asociados para el template
    productos = Producto.objects.all().prefetch_related('lotes').order_by('nombre')
    
    template = get_template('productos/reporte_pdf.html')
    html = template.render({'productos': productos, 'now': now()})
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error: {pisa_status.err}', status=500)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_productos.pdf"'
    return response


@admin_required
def reporte_productos_excel(request):
    """Reporte Excel de productos"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_productos.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Nombre', 'Categoría', 'Precio Costo', 'Precio Venta', 'Stock', 'Estado'])
    
    for p in Producto.objects.all():
        writer.writerow([
            p.id_producto,
            p.nombre,
            p.categoria.nombre if p.categoria else '',
            p.precio_costo,
            p.precio_venta,
            p.stock_actual,
            p.estado,
        ])
    
    return response


@admin_required
def reporte_alertas_lotes_pdf(request):
    """Reporte PDF de alertas de lotes - Mejorado y robusto"""
    try:
        if not HAS_PDF:
            messages.error(request, '❌ Error: xhtml2pdf no instalado. Instala con: pip install xhtml2pdf')
            return redirect('alertas_lotes')
        
        # Obtener todos los lotes disponibles
        lotes = Lote.objects.filter(estado='disponible').order_by('fecha_vencimiento')
        
        if not lotes.exists():
            messages.warning(request, 'ℹ️ No hay lotes disponibles para generar el reporte.')
            return redirect('alertas_lotes')
        
        # Clasificar alertas
        alertas_criticas = []  # ≤ 7 días (incluyendo vencidos)
        alertas_altas = []     # 8-14 días
        alertas_medias = []    # 15-30 días
        alertas_bajas = []     # > 30 días
        
        for lote in lotes:
            dias = lote.dias_para_vencer()
            
            # Formatear precio con formato moneda
            try:
                precio_fmt = f"${float(lote.precio_unitario):,.2f}"
            except (ValueError, TypeError):
                precio_fmt = "$0.00"
            
            # Datos seguros para el template
            lote_info = {
                'lote': lote,
                'producto': lote.producto,
                'numero_lote': lote.numero_lote,
                'cantidad': lote.cantidad,
                'fecha_vencimiento': lote.fecha_vencimiento,
                'dias_restantes': dias,
                'precio_unitario': float(lote.precio_unitario) if lote.precio_unitario else 0,
                'precio_unitario_fmt': precio_fmt,
            }
            
            # Clasificar según días restantes
            if dias <= 0:
                alertas_criticas.append(lote_info)
            elif dias <= 7:
                alertas_criticas.append(lote_info)
            elif dias <= 14:
                alertas_altas.append(lote_info)
            elif dias <= 30:
                alertas_medias.append(lote_info)
            else:
                alertas_bajas.append(lote_info)
        
        # Preparar contexto para el template
        template_context = {
            'alertas_criticas': alertas_criticas,
            'alertas_altas': alertas_altas,
            'alertas_medias': alertas_medias,
            'alertas_bajas': alertas_bajas,
            'total_alertas': len(alertas_criticas) + len(alertas_altas) + len(alertas_medias) + len(alertas_bajas),
            'now': now(),
        }
        
        # Renderizar template HTML
        template = get_template('productos/reporte_alertas_pdf.html')
        html_content = template.render(template_context)
        
        # Generar PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            html_string=html_content,
            dest=pdf_buffer,
            encoding='UTF-8'
        )
        
        # Verificar si hubo errores
        if pisa_status.err:
            messages.error(request, f'❌ Error generando PDF: {pisa_status.err}')
            return redirect('alertas_lotes')
        
        # Obtener PDF generado
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        # Si el PDF está vacío, hay error
        if not pdf_content:
            messages.error(request, '❌ Error: PDF vacío generado.')
            return redirect('alertas_lotes')
        
        # Retornar PDF como descarga
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_alertas_lotes.pdf"'
        
        return response
        
    except Exception as e:
        import traceback
        error_msg = f'❌ Error inesperado: {str(e)}'
        print(f"[ERROR PDF] {error_msg}")
        print(traceback.format_exc())
        messages.error(request, error_msg)
        return redirect('alertas_lotes')


@admin_required
def reporte_alertas_lotes_excel(request):
    """Reporte Excel de alertas"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_alertas.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Producto', 'Lote', 'Cantidad', 'Vencimiento', 'Días', 'Nivel'])
    
    for lote in Lote.objects.filter(estado='disponible').order_by('fecha_vencimiento'):
        dias = lote.dias_para_vencer()
        
        if dias <= 0:
            nivel = 'Vencido'
        elif dias <= 7:
            nivel = 'Crítica'
        elif dias <= 14:
            nivel = 'Alta'
        elif dias <= 30:
            nivel = 'Media'
        else:
            nivel = 'Baja'
        
        writer.writerow([
            lote.producto.nombre,
            lote.numero_lote,
            lote.cantidad,
            lote.fecha_vencimiento,
            dias,
            nivel,
        ])
    
    return response


# ============================================================================
# VISTAS DE APIS
# ============================================================================

@admin_required
def api_lotes_producto(request, producto_id):
    """API: Lotes de un producto"""
    try:
        lotes = Lote.objects.filter(
            producto_id=producto_id,
            estado='disponible'
        ).order_by('fecha_vencimiento')
        
        data = []
        for lote in lotes:
            data.append({
                'id': lote.id_lote,
'numero_lote': lote.numero_lote,
                'numero_lote_fabricante': lote.numero_lote_fabricante,
                'fecha_vencimiento': lote.fecha_vencimiento.isoformat() if lote.fecha_vencimiento else None,
                'cantidad': lote.cantidad,
                'precio_unitario': float(lote.precio_unitario),
                'dias_restantes': lote.dias_para_vencer(),
            })
        
        return JsonResponse({'success': True, 'lotes': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@admin_required
def api_alertas_lotes(request):
    """API: Alertas de lotes"""
    try:
        lotes = Lote.objects.filter(estado='disponible').order_by('fecha_vencimiento')
        
        data = []
        for lote in lotes:
            dias = lote.dias_para_vencer()
            
            if dias > 0:
                data.append({
                    'id': lote.id_lote,
                    'numero_lote': lote.numero_lote,
                    'producto': lote.producto.nombre,
                    'dias_restantes': dias,
                    'nivel': 'critica' if dias <= 7 else 'alta' if dias <= 14 else 'media' if dias <= 30 else 'baja',
                })
        
        return JsonResponse({'success': True, 'alertas': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
