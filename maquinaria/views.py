from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Maquinaria
from productos.models import Producto
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from usuarios.decorators import admin_required
import io
import csv


@admin_required
def reporte_maquinaria_pdf(request):
    from io import BytesIO
    maquinas = Maquinaria.objects.all()

    id_maquina = request.GET.get("id_maquina")
    nombre = request.GET.get("nombre")
    tipo = request.GET.get("tipo")
    ubicacion = request.GET.get("ubicacion")
    estado = request.GET.get("estado")

    if id_maquina:
        maquinas = maquinas.filter(id_maquina=id_maquina)
    if nombre:
        maquinas = maquinas.filter(nombre__icontains=nombre)
    if tipo:
        maquinas = maquinas.filter(tipo=tipo)
    if ubicacion:
        maquinas = maquinas.filter(ubicacion__icontains=ubicacion)
    if estado:
        maquinas = maquinas.filter(estado=estado)

    template = get_template('maquinaria/reporte_pdf.html')
    html = template.render({'maquinas': maquinas, 'now': now()})

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_maquinaria.pdf"'
    return response


@admin_required
def reporte_maquinaria_excel(request):
    maquinas = Maquinaria.objects.all()

    id_maquina = request.GET.get("id_maquina")
    nombre = request.GET.get("nombre")
    tipo = request.GET.get("tipo")
    ubicacion = request.GET.get("ubicacion")
    estado = request.GET.get("estado")

    if id_maquina:
        maquinas = maquinas.filter(id_maquina=id_maquina)
    if nombre:
        maquinas = maquinas.filter(nombre__icontains=nombre)
    if tipo:
        maquinas = maquinas.filter(tipo=tipo)
    if ubicacion:
        maquinas = maquinas.filter(ubicacion__icontains=ubicacion)
    if estado:
        maquinas = maquinas.filter(estado=estado)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['REPORTE DE MAQUINARIA'])
    writer.writerow([])
    writer.writerow(['ID', 'Nombre', 'Tipo', 'Ubicación', 'Estado', 'Fecha Adquisición'])

    for m in maquinas:
        writer.writerow([
            m.id_maquina,
            m.nombre,
            m.tipo,
            m.ubicacion,
            m.estado,
            m.fecha_adquisicion.strftime('%d/%m/%Y') if m.fecha_adquisicion else ''
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_maquinaria.csv"'
    return response


@admin_required
def lista_maquinaria(request):
    maquinas = Maquinaria.objects.all()

    id_maquina = request.GET.get("id_maquina")
    nombre = request.GET.get("nombre")
    tipo = request.GET.get("tipo")
    ubicacion = request.GET.get("ubicacion")
    estado = request.GET.get("estado")

    if id_maquina:
        maquinas = maquinas.filter(id_maquina=id_maquina)
    if nombre:
        maquinas = maquinas.filter(nombre__icontains=nombre)
    if tipo:
        maquinas = maquinas.filter(tipo=tipo)
    if ubicacion:
        maquinas = maquinas.filter(ubicacion__icontains=ubicacion)
    if estado:
        maquinas = maquinas.filter(estado=estado)

    # Obtener ubicaciones únicas para el filtro desplegable
    ubicaciones_unicas = Maquinaria.objects.exclude(ubicacion__isnull=True).exclude(ubicacion='').values_list('ubicacion', flat=True).distinct().order_by('ubicacion')

    return render(request, "maquinaria/lista.html", {
        "maquinas": maquinas,
        "ubicaciones": ubicaciones_unicas
    })


@admin_required
def crear_maquinaria(request):
    from proveedores.models import Proveedor
    proveedores = Proveedor.objects.filter(estado='activo')
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        if not nombre:
            messages.error(request, "El nombre es requerido.")
            return render(request, "maquinaria/form.html", {'proveedores': proveedores})
        
        try:
            precio_compra = float(request.POST.get("precio_compra")) if request.POST.get("precio_compra") else None
        except ValueError:
            messages.error(request, "El precio de compra debe ser un número válido.")
            return render(request, "maquinaria/form.html", {'proveedores': proveedores})
        
        proveedor_id = request.POST.get("proveedor")
        proveedor = None
        if proveedor_id:
            proveedor = Proveedor.objects.filter(id_proveedor=proveedor_id).first()
        
        maquina = Maquinaria.objects.create(
            nombre=nombre,
            descripcion=request.POST.get("descripcion"),
            tipo=request.POST.get("tipo", 'otro'),
            ubicacion=request.POST.get("ubicacion"),
            estado=request.POST.get("estado", 'activo'),
            precio_compra=precio_compra,
            fecha_compra=request.POST.get("fecha_compra") or None,
            imagen=request.FILES.get("imagen"),
            proveedor=proveedor,
        )
        messages.success(request, f'Maquina "{maquina.nombre}" creada correctamente.')
        return redirect("lista_maquinaria")

    return render(request, "maquinaria/form.html", {'proveedores': proveedores})


@admin_required
def editar_maquinaria(request, id):
    maquina = get_object_or_404(Maquinaria, id_maquina=id)

    if request.method == "POST":
        maquina.nombre = request.POST.get("nombre")
        maquina.descripcion = request.POST.get("descripcion")
        maquina.tipo = request.POST.get("tipo", maquina.tipo)
        maquina.ubicacion = request.POST.get("ubicacion")
        maquina.estado = request.POST.get("estado", maquina.estado)
        maquina.precio_compra = request.POST.get("precio_compra") or None
        maquina.precio_venta = request.POST.get("precio_venta") or None
        maquina.fecha_compra = request.POST.get("fecha_compra") or None
        
        proveedor_id = request.POST.get("proveedor")
        if proveedor_id:
            maquina.proveedor_id = proveedor_id
        else:
            maquina.proveedor = None

        if request.FILES.get("imagen"):
            maquina.imagen = request.FILES["imagen"]

        maquina.save()
        messages.success(request, f'Maquina "{maquina.nombre}" actualizada.')
        return redirect("lista_maquinaria")

    from proveedores.models import Proveedor
    proveedores = Proveedor.objects.filter(estado='activo')
    return render(request, "maquinaria/form.html", {"maquina": maquina, "proveedores": proveedores})


@admin_required
@transaction.atomic
def eliminar_maquinaria(request, id):
    maquina = get_object_or_404(Maquinaria, id_maquina=id)
    nombre = maquina.nombre

    if maquina.producto_vinculado:
        maquina.producto_vinculado.delete()

    maquina.delete()
    messages.success(request, f'Maquina "{nombre}" eliminada.')
    return redirect("lista_maquinaria")


@admin_required
@transaction.atomic
def poner_en_venta(request, id):
    maquina = get_object_or_404(Maquinaria, id_maquina=id)

    if request.method == "POST":
        precio = request.POST.get("precio_venta")

        if not precio:
            messages.error(request, "Debes ingresar un precio de venta.")
            return render(request, "maquinaria/poner_en_venta.html", {"maquina": maquina})

        try:
            precio = float(precio)
            if precio <= 0:
                messages.error(request, "El precio debe ser mayor a 0.")
                return render(request, "maquinaria/poner_en_venta.html", {"maquina": maquina})
        except ValueError:
            messages.error(request, "El precio debe ser un número válido.")
            return render(request, "maquinaria/poner_en_venta.html", {"maquina": maquina})

        if maquina.estado == 'venta':
            messages.warning(request, f'"{maquina.nombre}" ya esta en venta.')
            return redirect("lista_maquinaria")

        if maquina.estado == 'vendido':
            messages.error(request, f'"{maquina.nombre}" ya fue vendida.')
            return redirect("lista_maquinaria")

        producto = Producto.objects.create(
            nombre=maquina.nombre,
            descripcion=maquina.descripcion or f"Maquina de {maquina.get_tipo_display()}",
            categoria="Maquinaria",
            precio_venta=precio,
            stock_actual=1,
            tiene_maquina=True,
            maquina_id=maquina.id_maquina,
            estado="activo",
            imagen=maquina.imagen,
        )

        maquina.estado = "venta"
        maquina.precio_venta = precio
        maquina.producto_vinculado = producto
        maquina.save()

        messages.success(request, f'"{maquina.nombre}" puesta en venta. Ahora aparece en los productos.')
        return redirect("lista_maquinaria")

    return render(request, "maquinaria/poner_en_venta.html", {"maquina": maquina})


@admin_required
@transaction.atomic
def quitar_de_venta(request, id):
    maquina = get_object_or_404(Maquinaria, id_maquina=id)

    if maquina.producto_vinculado:
        maquina.producto_vinculado.delete()
        maquina.producto_vinculado = None

    maquina.estado = "activo"
    maquina.precio_venta = None
    maquina.save()

    messages.success(request, f'"{maquina.nombre}" quitada de la tienda.')
    return redirect("lista_maquinaria")


@admin_required
def limpiar_maquinaria(request):
    """Elimina toda la maquinaria"""
    if request.method == 'POST':
        count = Maquinaria.objects.count()
        Maquinaria.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} equipos de maquinaria correctamente.')
    return redirect("lista_maquinaria")
