from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Compra, DetalleCompra, Lote
from proveedores.models import Proveedor
from productos.models import Producto
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from usuarios.decorators import admin_required


@admin_required
def get_next_lote(request, producto_id):
    """API endpoint to get the next lot number for a product"""
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Method not allowed"})
    
    try:
        producto = Producto.objects.get(id_producto=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({"success": False, "error": "Product not found"})
    
    # Get the highest existing lot number for this product
    ultimo_lote = Lote.objects.filter(producto=producto).order_by('-id_lote').first()
    
    if ultimo_lote:
        # Extract number from the last lot (ej: LOTE001 -> 1)
        import re
        match = re.search(r'(\d+)$', ultimo_lote.numero_lote)
        if match:
            siguiente_numero = int(match.group(1)) + 1
            siguiente_lote = f"LOTE{siguiente_numero:03d}"
        else:
            siguiente_lote = "LOTE001"
    else:
        siguiente_lote = "LOTE001"
    
    return JsonResponse({
        "success": True,
        "next_lote": siguiente_lote
    })


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

        # Crear detalle de compra
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_costo,
            subtotal=subtotal
        )

        producto = Producto.objects.get(id_producto=producto_id)
        
        # Crear lote automáticamente desde la compra
        lote = None
        if fecha_fabricacion_str and fecha_vencimiento_str:
            try:
                from datetime import datetime
                fecha_fabricacion = datetime.strptime(fecha_fabricacion_str, '%Y-%m-%d').date()
                fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date()
                
                # El modelo Lote generará automáticamente numero_lote en save()
                lote = Lote.objects.create(
                    producto=producto,
                    cantidad=cantidad,
                    fecha_fabricacion=fecha_fabricacion,
                    fecha_vencimiento=fecha_vencimiento,
                    notas=f"Creado automaticamente desde compra #{compra.id_compra}"
                )
                
                from django.contrib import messages
                messages.success(request, f"Lote {lote.numero_lote} creado automaticamente para {producto.nombre}")
                
            except ValueError as e:
                from django.contrib import messages
                messages.error(request, f"Formato de fecha invalido: {e}")
                return render(request, "compras/form_compra.html", {
                    "proveedores": proveedores
                })
            except Exception as e:
                from django.contrib import messages
                messages.error(request, f"Error creando lote: {e}")
                return render(request, "compras/form_compra.html", {
                    "proveedores": proveedores
                })
        
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

        return redirect("lista_compras")

    return render(request, "compras/form_compra.html", {
        "proveedores": proveedores
    })
