from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from .models import Compra, DetalleCompra, Lote
from proveedores.models import Proveedor
from productos.models import Producto
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from datetime import datetime
from usuarios.decorators import admin_required


@admin_required
def get_next_lote(request, producto_id):
    """API endpoint to get the next lot number for a product"""
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Method not allowed"})
    
    try:
        producto = Producto.objects.get(id_producto=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({"success": False, "error": "Producto no encontrado"})
    
    ultimo_lote = Lote.objects.filter(producto=producto).order_by('-id_lote').first()
    
    if ultimo_lote:
        import re
        match = re.search(r'(\d+)$', ultimo_lote.numero_lote)
        if match:
            siguiente_numero = int(match.group(1)) + 1
            siguiente_lote = f"LOTE{siguiente_numero:03d}"
        else:
            siguiente_lote = "LOTE001"
    else:
        siguiente_lote = "LOTE001"
    
    return JsonResponse({"success": True, "next_lote": siguiente_lote})


@admin_required
@transaction.atomic
def crear_compra(request):

    proveedores = Proveedor.objects.filter(estado="activo").prefetch_related('productos')

    if request.method == "POST":
        # Use .get() to avoid MultiValueDictKeyError
        proveedor_id = request.POST.get("proveedor")
        producto_id = request.POST.get("producto")

        # Validate required fields
        if not proveedor_id or not producto_id:
            from django.contrib import messages
            messages.error(request, "Debe seleccionar un proveedor y un producto.")
            return render(request, "compras/form_compra.html", {
                "proveedores": proveedores
            })

        cantidad = int(request.POST.get("cantidad", 1))
        precio_costo = float(request.POST.get("precio", 0))
        precio_venta = float(request.POST.get("precio_venta", 0))
        fecha_fabricacion_str = request.POST.get("fecha_fabricacion", "")
        fecha_vencimiento_str = request.POST.get("fecha_vencimiento", "")

        # Parse dates early
        fecha_fabricacion = None
        fecha_vencimiento = None
        if fecha_fabricacion_str:
            try:
                fecha_fabricacion = datetime.strptime(fecha_fabricacion_str, '%Y-%m-%d').date()
            except ValueError:
                pass  # Keep None, validation will catch if required
        if fecha_vencimiento_str:
            try:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if cantidad <= 0:
            from django.contrib import messages
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return render(request, "compras/form_compra.html", {
                "proveedores": proveedores
            })

        subtotal = cantidad * precio_costo

        compra = Compra.objects.create(
            proveedor_id=proveedor_id,
            total=subtotal
        )

        # Crear detalle de compra - guardar fecha_fabricacion en detalle
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_costo,
            subtotal=subtotal,
            fecha_fabricacion=fecha_fabricacion
        )

        producto = Producto.objects.get(id_producto=producto_id)

        # Determinar si el producto es consumible (suplemento) o ropa/accesorios
        es_consumible = producto.categoria and producto.categoria.es_consumible if producto.categoria else False

        # Obtener datos del lote manual del fabricante
        numero_lote_fabricante = request.POST.get("numero_lote_fabricante", "").strip() or None

        # Validaciones según tipo de producto
        if es_consumible:
            # Para consumibles: las fechas son obligatorias
            if not fecha_fabricacion or not fecha_vencimiento:
                from django.contrib import messages
                messages.error(request, "Los productos consumibles requieren fecha de fabricación y fecha de vencimiento.")
                return render(request, "compras/form_compra.html", {
                    "proveedores": proveedores
                })

        # Crear lote para consumibles siempre; para ropa/accesorios solo si se proveen fechas
        lote = None

        if es_consumible:
            # Para consumibles: crear lote con fechas
            try:
                lote = Lote.objects.create(
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_costo,
                    fecha_compra=compra.fecha.date(),
                    fecha_fabricacion=fecha_fabricacion,
                    fecha_vencimiento=fecha_vencimiento,
                    numero_lote_fabricante=numero_lote_fabricante,
                    notas=f"Creado automaticamente desde compra #{compra.id_compra}"
                )

                from django.contrib import messages
                msj_lote = f"Lote {lote.numero_lote}"
                if numero_lote_fabricante:
                    msj_lote += f" (fabricante: {numero_lote_fabricante})"
                messages.success(request, f"{msj_lote} creado automaticamente para {producto.nombre}")

            except Exception as e:
                from django.contrib import messages
                messages.error(request, f"Error creando lote: {e}")
                return render(request, "compras/form_compra.html", {
                    "proveedores": proveedores
                })
        else:
            # Para ropa/accesorios: solo crear lote si se proporcionan ambas fechas
            if fecha_fabricacion and fecha_vencimiento:
                try:
                    lote = Lote.objects.create(
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_costo,
                        fecha_compra=compra.fecha.date(),
                        fecha_fabricacion=fecha_fabricacion,
                        fecha_vencimiento=fecha_vencimiento,
                        notas=f"Creado automaticamente desde compra #{compra.id_compra}"
                    )

                    from django.contrib import messages
                    messages.success(request, f"Lote {lote.numero_lote} creado automaticamente para {producto.nombre}")

                except Exception as e:
                    from django.contrib import messages
                    messages.error(request, f"Error creando lote: {e}")
                    return render(request, "compras/form_compra.html", {
                        "proveedores": proveedores
                    })
            else:
                # Si no se dieron fechas, igual actualizar stock
                producto.stock_actual = producto.stock_actual + cantidad
                producto.save()

        # Recargar producto tras cambios
        producto.refresh_from_db()

        # Calcular stock anterior
        stock_anterior = producto.stock_actual - cantidad

        # Registrar en historial de inventario
        from productos.models import HistorialInventario
        HistorialInventario.objects.create(
            producto=producto,
            tipo='entrada',
            origen='compra',
            cantidad=cantidad,
            stock_anterior=max(0, stock_anterior),
            stock_nuevo=producto.stock_actual,
            referencia_id=compra.id_compra,
            usuario=request.user if request.user.is_authenticated else None,
            notas=f"Compra #{compra.id_compra} - Proveedor: {compra.proveedor.nombre}"
        )

        # Notificacion de stock bajo
        from usuarios.models import Notificacion
        Notificacion.notificar_stock_bajo(producto)

        # Mensaje de confirmacion detallado
        from django.contrib import messages
        msj = f"Compra registrada: {cantidad} unidades de {producto.nombre}. "
        msj += f"Stock anterior: {max(0, stock_anterior)}, Stock actual: {producto.stock_actual}. "
        if lote:
            msj += f"Lote generado: {lote.numero_lote}"
        messages.success(request, msj)

        return redirect("lista_compras")

    return render(request, "compras/form_compra.html", {
        "proveedores": proveedores
    })


@admin_required
@transaction.atomic
def editar_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalle = DetalleCompra.objects.filter(compra=compra).first()

    if not detalle:
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=Producto.objects.first(),
            cantidad=1,
            precio_unitario=0,
            subtotal=0
        )

    proveedores = Proveedor.objects.filter(estado="activo").prefetch_related('productos')

    # Obtener el lote asociado a esta compra (si existe) para prellenar campos
    from productos.models import Lote
    lote = None
    try:
        lote = Lote.objects.filter(notas__contains=f"desde compra #{compra.id_compra}").first()
    except Exception:
        lote = None

    if request.method == "POST":

        proveedor_id = request.POST.get("proveedor")
        compra.proveedor_id = proveedor_id

        producto = Producto.objects.get(
            id_producto=request.POST.get("producto")
        )

        nueva_cantidad = int(request.POST.get("cantidad"))
        precio = float(request.POST.get("precio"))
        fecha_fabricacion_str = request.POST.get("fecha_fabricacion", "")
        fecha_vencimiento_str = request.POST.get("fecha_vencimiento", "")

        # Parse dates
        fecha_fabricacion = None
        if fecha_fabricacion_str:
            try:
                fecha_fabricacion = datetime.strptime(fecha_fabricacion_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        fecha_vencimiento = None
        if fecha_vencimiento_str:
            try:
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Validaciones según tipo de producto
        es_consumible = producto.categoria and producto.categoria.es_consumible if producto.categoria else False
        if es_consumible:
            if not fecha_fabricacion or not fecha_vencimiento:
                from django.contrib import messages
                messages.error(request, "Los productos consumibles requieren fecha de fabricación y fecha de vencimiento.")
                return render(request, "compras/form_compra.html", {
                    "compra": compra,
                    "detalle": detalle,
                    "lote": lote,
                    "proveedores": proveedores
                })

        if nueva_cantidad <= 0:
            from django.contrib import messages
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return render(request, "compras/form_compra.html", {
                "compra": compra,
                "detalle": detalle,
                "lote": lote,
                "proveedores": proveedores
            })

        cantidad_anterior = detalle.cantidad
        stock_anterior = producto.stock_actual

        producto.stock_actual = (
            producto.stock_actual
            - cantidad_anterior
            + nueva_cantidad
        )
        producto.save()

        from productos.models import HistorialInventario
        diferencia = nueva_cantidad - cantidad_anterior
        if diferencia != 0:
            HistorialInventario.objects.create(
                producto=producto,
                tipo='entrada' if diferencia > 0 else 'salida',
                origen='compra',
                cantidad=abs(diferencia),
                stock_anterior=stock_anterior,
                stock_nuevo=producto.stock_actual,
                referencia_id=compra.id_compra,
                usuario=request.user if request.user.is_authenticated else None,
                notas=f"Edición de compra #{compra.id_compra}"
            )

        detalle.producto = producto
        detalle.cantidad = nueva_cantidad
        detalle.precio_unitario = precio
        detalle.subtotal = nueva_cantidad * precio
        detalle.fecha_fabricacion = fecha_fabricacion
        detalle.save()

        compra.total = detalle.subtotal
        compra.save()

        # Actualizar lote asociado si existe
        if lote:
            lote.numero_lote_fabricante = request.POST.get("numero_lote_fabricante", lote.numero_lote_fabricante) or lote.numero_lote_fabricante
            lote.fecha_fabricacion = fecha_fabricacion if fecha_fabricacion is not None else lote.fecha_fabricacion
            lote.fecha_vencimiento = fecha_vencimiento if fecha_vencimiento is not None else lote.fecha_vencimiento
            lote.save()

        return redirect("lista_compras")

    return render(request, "compras/form_compra.html", {
        "compra": compra,
        "detalle": detalle,
        "lote": lote,
        "proveedores": proveedores
    })


@admin_required
@transaction.atomic
def eliminar_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalle = DetalleCompra.objects.filter(compra=compra).first()

    if detalle:
        producto = detalle.producto
        stock_anterior = producto.stock_actual
        producto.stock_actual -= detalle.cantidad
        producto.save()
        
        from productos.models import HistorialInventario
        HistorialInventario.objects.create(
            producto=producto,
            tipo='salida',
            origen='compra',
            cantidad=detalle.cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock_actual,
            referencia_id=compra.id_compra,
            usuario=request.user if request.user.is_authenticated else None,
            notas=f"Eliminación de compra #{compra.id_compra}"
        )

    compra.delete()

    return redirect("lista_compras")


@admin_required
def ver_detalle_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalles = DetalleCompra.objects.filter(compra=compra)

    return render(request, "compras/detalle_compra.html", {
        "compra": compra,
        "detalles": detalles
    })


@admin_required
def lista_compras(request):

    compras = Compra.objects.all().select_related("proveedor")

    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    id_compra = request.GET.get("id_compra")

    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)

    if fecha:
        compras = compras.filter(fecha__date=fecha)

    if total_min:
        compras = compras.filter(total__gte=total_min)

    if id_compra:
        compras = compras.filter(id_compra=id_compra)

    compras_con_detalles = []
    for compra in compras:
        detalle = DetalleCompra.objects.filter(compra=compra).select_related('producto').first()
        compras_con_detalles.append({
            'compra': compra,
            'detalle': detalle,
        })

    from proveedores.models import Proveedor
    proveedores = Proveedor.objects.filter(estado='activo').order_by('nombre')

    return render(request, "compras/lista_compras.html", {
        "compras_con_detalles": compras_con_detalles,
        "proveedores": proveedores
    })


@admin_required
def reporte_compras_pdf(request):
    compras = Compra.objects.all()

    id_compra = request.GET.get("id_compra")
    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")

    if id_compra:
        compras = compras.filter(id_compra=id_compra)

    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)

    if fecha:
        compras = compras.filter(fecha__date=fecha)

    if total_min:
        compras = compras.filter(total__gte=total_min)

    template = get_template('compras/reporte_pdf.html')
    html = template.render({
        'compras': compras,
        'now': now()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_compras.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response


@admin_required
def reporte_compras_excel(request):
    """Exporta todas las compras a Excel"""
    import csv
    import io
    
    compras = Compra.objects.all().select_related("proveedor")
    
    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    id_compra = request.GET.get("id_compra")
    
    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)
    if fecha:
        compras = compras.filter(fecha__date=fecha)
    if total_min:
        compras = compras.filter(total__gte=total_min)
    if id_compra:
        compras = compras.filter(id_compra=id_compra)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Proveedor', 'Producto', 'Cantidad', 'Precio Unitario', 'Fecha', 'Total'])
    
    for compra in compras:
        detalle = DetalleCompra.objects.filter(compra=compra).first()
        producto = detalle.producto.nombre if detalle and detalle.producto else '-'
        cantidad = detalle.cantidad if detalle else '-'
        precio = detalle.precio_unitario if detalle else '-'
        
        writer.writerow([
            compra.id_compra,
            compra.proveedor.nombre,
            producto,
            cantidad,
            precio,
            compra.fecha.strftime('%d/%m/%Y') if compra.fecha else '-',
            float(compra.total)
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_compras.csv"'
    
    return response
