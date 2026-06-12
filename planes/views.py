from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import random
import string
from .models import Plan
from usuarios.models import (
    Suscripcion, Venta, Perfil, Rutina, TerminosYCondiciones, HistorialPeso
)
from usuarios.utils import enviar_comprobante_pago, enviar_rutina_correo


# =================== VISTAS DE PLANES ===================

@login_required
def ver_planes(request):
    """Mostrar lista de planes disponibles"""
    planes = Plan.objects.all()
    return render(request, 'planes/ver_planes.html', {'planes': planes})


@login_required
def confirmar_compra(request, plan_id):
    """Vista para confirmar la compra con simulación de pago"""
    plan = get_object_or_404(Plan, id=plan_id)

    # Verificar si ya tiene una suscripción activa
    suscripcion_activa = Suscripcion.objects.filter(
        usuario=request.user,
        fecha_fin__gte=timezone.now().date()
    ).first()

    # Obtener o crear el perfil del usuario
    perfil, created = Perfil.objects.get_or_create(
        user=request.user,
        defaults={'rol': 'cliente'}
    )

    # Calcular fecha de inicio y fin propuesta
    fecha_hoy = timezone.now().date()

    if suscripcion_activa:
        fecha_inicio_propuesta = suscripcion_activa.fecha_fin + timedelta(days=1)
    else:
        fecha_inicio_propuesta = fecha_hoy

    fecha_fin_calculada = fecha_inicio_propuesta + timedelta(days=plan.duracion_dias)

    # Obtener rutinas de la base de datos filtradas por duración del plan
    duracion_plan = plan.duracion_dias
    rutinas_db = list(Rutina.objects.filter(
        activa=True,
        duracion_dias=duracion_plan
    ).values('id', 'nombre', 'nivel', 'duracion_dias'))

    # Si no hay rutinas exactas, buscar las más cercanas (dentro de +15 días)
    if not rutinas_db:
        rutinas_db = list(Rutina.objects.filter(
            activa=True,
            duracion_dias__gte=duracion_plan,
            duracion_dias__lte=duracion_plan + 15
        ).values('id', 'nombre', 'nivel', 'duracion_dias'))

    # Opciones de rutinas para el plan actual
    opciones_rutina = [
        {'valor': 'bajar_peso', 'nombre': '🔥 Bajar de Peso', 'icono': 'fa-fire', 'es_db': False},
        {'valor': 'subir_masa', 'nombre': '💪 Subir Masa Muscular', 'icono': 'fa-dumbbell', 'es_db': False},
        {'valor': 'mantener', 'nombre': '⚖️ Mantener Peso', 'icono': 'fa-balance-scale', 'es_db': False},
        {'valor': 'definir', 'nombre': '🥷 Definir Musculatura', 'icono': 'fa-user-ninja', 'es_db': False},
        {'valor': 'cardio', 'nombre': '❤️ Cardio y Resistencia', 'icono': 'fa-heartbeat', 'es_db': False},
    ]

    # Agregar rutinas de la base de datos que coincidan con la duración del plan
    for rutina in rutinas_db:
        opciones_rutina.append({
            'valor': f'rutina_{rutina["id"]}',
            'nombre': rutina['nombre'],
            'icono': 'fa-running',
            'es_db': True,
            'duracion_dias': rutina['duracion_dias']
        })

    # Verificar si hay una rutina seleccionada previamente (de la sesión)
    rutina_seleccionada = request.session.get('rutina_seleccionada')

    # Calcular IMC si el perfil tiene los datos
    imc = None
    clasificacion_imc = None
    rutina_recomendada = None

    if perfil.peso and perfil.estatura and perfil.estatura > 0:
        imc_calc = float(perfil.peso) / (float(perfil.estatura) ** 2)
        imc = round(imc_calc, 1)

        if imc < 18.5:
            clasificacion_imc = "Bajo peso"
            rutina_recomendada = "subir_masa"
        elif imc < 25:
            clasificacion_imc = "Normal"
            rutina_recomendada = "mantener"
        elif imc < 30:
            clasificacion_imc = "Sobrepeso"
            rutina_recomendada = "bajar_peso"
        else:
            clasificacion_imc = "Obesidad"
            rutina_recomendada = "bajar_peso"

    # Obtener nombre de rutina recomendada
    rutina_recomendada_nombre = None
    for opcion in opciones_rutina:
        if opcion['valor'] == rutina_recomendada:
            rutina_recomendada_nombre = opcion['nombre']
            break

    # URL para elegir rutina (con vuelta)
    url_elegir_rutina = f"/rutinas/?next=/comprar/{plan_id}/"

    # Obtener términos y condiciones activos desde la base de datos
    terminos_obj = TerminosYCondiciones.get_terminos_activos()
    if terminos_obj:
        terminos_contenido = terminos_obj.contenido
    else:
        terminos_contenido = (
            "<h1 style='text-align:center;'><strong>TÉRMINOS Y CONDICIONES - GYMXTREME</strong></h1>"
            "<p><strong>1.</strong> El cliente declara que se encuentra en condiciones físicas aptas para realizar actividad física.</p>"
            "<p><strong>2.</strong> GymXtreme no se hace responsable por lesiones dentro de las instalaciones.</p>"
            "<p><strong>3.</strong> Se recomienda consultar con un médico antes de iniciar cualquier programa de entrenamiento.</p>"
            "<p><strong>4.</strong> No se realizan devoluciones una vez efectuado el pago del plan adquirido.</p>"
            "<p><strong>5.</strong> Al continuar con la compra, el cliente acepta estos términos y condiciones en su totalidad.</p>"
        )

    rutina_seleccionada_valor = None
    if rutina_seleccionada:
        rutina_seleccionada_valor = f"rutina_{rutina_seleccionada['id']}"

    context = {
        'plan': plan,
        'suscripcion_activa': suscripcion_activa,
        'perfil': perfil,
        'fecha_hoy': fecha_hoy,
        'fecha_inicio_propuesta': fecha_inicio_propuesta,
        'fecha_fin_calculada': fecha_fin_calculada,
        'opciones_rutina': opciones_rutina,
        'rutina_recomendada': rutina_recomendada,
        'rutina_recomendada_nombre': rutina_recomendada_nombre,
        'imc': imc,
        'clasificacion_imc': clasificacion_imc,
        'rutina_seleccionada': rutina_seleccionada,
        'rutina_seleccionada_valor': rutina_seleccionada_valor,
        'url_elegir_rutina': url_elegir_rutina,
        'terminos_contenido': terminos_contenido,
    }
    return render(request, 'planes/confirmar_compra.html', context)


@login_required
def procesar_pago(request, plan_id):
    """Vista para procesar el pago simulado de un plan individual"""
    if request.method != 'POST':
        return redirect('planes:ver_planes')

    # ✅ VALIDACIÓN OBLIGATORIA: Términos y condiciones
    acepto_terminos = request.POST.get('acepto_terminos') == 'on'
    if not acepto_terminos:
        messages.error(request, '❌ DEBES ACEPTAR LOS TÉRMINOS Y CONDICIONES para continuar con la compra.')
        return redirect('planes:confirmar_compra', plan_id=plan_id)

    plan = get_object_or_404(Plan, id=plan_id)
    usuario = request.user

    # ✅ GUARDAR ACEPTACIÓN EN BD
    acepto_terminos_value = True

    # Obtener el objetivo seleccionado por el usuario
    objetivo_seleccionado = request.POST.get('objetivo_rutina', '').strip()

    # Variable para guardar el ID de la rutina específica seleccionada
    rutina_id_seleccionada = None

    # Si viene de seleccionar una rutina de la DB (formato: rutina_ID)
    if objetivo_seleccionado and objetivo_seleccionado.startswith('rutina_'):
        try:
            rutina_id_seleccionada = int(objetivo_seleccionado.replace('rutina_', ''))
            rutina = Rutina.objects.get(id=rutina_id_seleccionada)
            objetivo_seleccionado = f"rutina_{rutina.id}"
        except (Rutina.DoesNotExist, ValueError):
            # ✅ Si no existe la rutina, vaciar objetivo para que se calcule la recomendada
            objetivo_seleccionado = ''
            rutina_id_seleccionada = None
    # Verificar si hay una rutina guardada en sesión
    elif 'rutina_seleccionada' in request.session:
        rutina_data = request.session.get('rutina_seleccionada', {})
        rutina_id_seleccionada = rutina_data.get('id')
        objetivo_seleccionado = f"rutina_{rutina_id_seleccionada}" if rutina_id_seleccionada else objetivo_seleccionado

    # Limpiar la sesión de rutina seleccionada después de usarla
    if 'rutina_seleccionada' in request.session:
        del request.session['rutina_seleccionada']

    # guardar datos del usuario para la rutina
    perfil, created = Perfil.objects.get_or_create(
        user=usuario,
        defaults={'rol': 'cliente'}
    )

    # Actualizar edad
    edad_str = request.POST.get('edad', '').strip()
    if edad_str:
        try:
            perfil.edad = int(edad_str)
        except ValueError:
            pass

    # Actualizar peso
    peso_str = request.POST.get('peso', '').strip()
    if peso_str:
        try:
            perfil.peso = float(peso_str)
        except ValueError:
            pass

    # Actualizar estatura
    estatura_str = request.POST.get('estatura', '').strip()
    if estatura_str:
        try:
            estatura_cm = float(estatura_str)
            perfil.estatura = estatura_cm / 100
        except ValueError:
            pass

    perfil.save()

    # ✅ CALCULAR RUTINA RECOMENDADA BASADA EN IMC
    # Esta es la lógica clave: si el usuario NO seleccionó rutina, calcular la recomendada
    rutina_recomendada = None
    if perfil.peso and perfil.estatura and perfil.estatura > 0:
        imc_calc = float(perfil.peso) / (float(perfil.estatura) ** 2)
        
        if imc_calc < 18.5:
            rutina_recomendada = "subir_masa"
        elif imc_calc < 25:
            rutina_recomendada = "mantener"
        elif imc_calc < 30:
            rutina_recomendada = "bajar_peso"
        else:
            rutina_recomendada = "bajar_peso"
    
    # Si NO hay objetivo seleccionado, usar la rutina recomendada (o 'mantener' como fallback)
    if not objetivo_seleccionado:
        objetivo_seleccionado = rutina_recomendada if rutina_recomendada else 'mantener'

    # Guardar registro en historial de peso
    if perfil.peso and perfil.estatura:
        HistorialPeso.objects.create(
            usuario=usuario,
            peso=perfil.peso,
            estatura=perfil.estatura,
            rutina=objetivo_seleccionado if objetivo_seleccionado else '',
            notas=f"Registro al comprar el plan '{plan.nombre}'",
        )

    # Obtener la fecha de inicio seleccionada por el usuario
    fecha_inicio_str = request.POST.get('fecha_inicio', '').strip()
    fecha_hoy = timezone.now().date()

    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = fecha_hoy
    else:
        fecha_inicio = fecha_hoy

    # No permitir fechas anteriores a hoy
    if fecha_inicio < fecha_hoy:
        fecha_inicio = fecha_hoy

    # verificar si ya tiene suscripcion activa
    suscripcion_activa = Suscripcion.objects.filter(
        usuario=usuario,
        estado='activa',
        activa=True,
        fecha_fin__gte=timezone.now().date()
    ).first()

    # calcular fechas
    if suscripcion_activa:
        fecha_inicio = suscripcion_activa.fecha_fin + timedelta(days=1)
        dias_a_sumar = plan.duracion_dias
        nueva_fecha_fin = fecha_inicio + timedelta(days=dias_a_sumar)

        # Actualizar la suscripcion existente
        suscripcion_activa.fecha_fin = nueva_fecha_fin
        suscripcion_activa.estado = 'activa'
        suscripcion_activa.activa = True
        # ✅ SIEMPRE guardar la rutina seleccionada o recomendada (nunca quedarse con la anterior)
        suscripcion_activa.objetivo_rutina = objetivo_seleccionado
        suscripcion_activa.save()

        suscripcion = suscripcion_activa
    else:
        fecha_fin = fecha_inicio + timedelta(days=plan.duracion_dias)

        suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            objetivo_rutina=objetivo_seleccionado,
            acepto_terminos=acepto_terminos_value,
            estado='activa',
            activa=True
        )

    # crear venta
    venta = Venta.objects.create(
        usuario=usuario,
        plan=plan,
        precio=plan.precio,
        acepto_terminos=acepto_terminos_value
    )

    # enviar comprobante de pago
    pago_ok, pago_msg = enviar_comprobante_pago(usuario, plan=venta.plan, venta=venta, total=venta.precio, tipo_pago="plan")
    if pago_ok:
        messages.success(request, f"📧 {pago_msg}")
    else:
        messages.warning(request, f"⚠️ Hubo un problema al enviar el comprobante de pago: {pago_msg}")

    # enviar correo con la rutina
    correo_ok, correo_msg = enviar_rutina_correo(usuario, plan, objetivo_seleccionado, rutina_id_seleccionada)

    if suscripcion_activa:
        messages.success(request, f"¡Renovación exitosa! Has añadido {plan.duracion_dias} días a tu membresía existente.")
    else:
        messages.success(request, f"¡Pago exitoso! Tu suscripción al plan '{plan.nombre}' ha sido activada.")

    if correo_ok:
        messages.success(request, f"📧 {correo_msg}")
    else:
        messages.warning(request, f"⚠️ Tu compra fue exitosa, pero hubo un problema al enviar la rutina: {correo_msg}")

    return redirect("home")


# =================== PASARELA DE PAGO DE PLANES ===================

@login_required
def pasarela_pago_planes(request):
    """Pasarela de pago visual para planes en carrito"""
    carrito = request.session.get('carrito_planes', {})

    if not carrito:
        messages.error(request, 'El carrito está vacío.')
        return redirect('planes:ver_planes')

    usuario = request.user

    # Obtener o crear perfil
    perfil, _ = Perfil.objects.get_or_create(user=usuario, defaults={'rol': 'cliente'})

    # Verificar suscripción activa
    suscripcion_activa = Suscripcion.objects.filter(
        usuario=usuario,
        fecha_fin__gte=timezone.now().date()
    ).first()

    # Calcular totales
    total = 0
    total_dias = 0
    items = []
    for key, item in carrito.items():
        precio = float(item.get('precio', 0))
        cantidad = int(item.get('cantidad', 1))
        dias = int(item.get('duracion_dias', 0))
        subtotal = precio * cantidad
        total += subtotal
        total_dias += dias * cantidad
        items.append({
            'id': item['id'],
            'nombre': item['nombre'],
            'precio': precio,
            'cantidad': cantidad,
            'duracion_dias': dias,
            'subtotal': subtotal,
        })

    # Datos del usuario para el formulario de pago simulado
    nombre_completo = f'{usuario.first_name} {usuario.last_name}'.strip() or usuario.username
    email = usuario.email or ''

    # Generar número de referencia aleatorio
    referencia = f'GXM-{datetime.now().strftime("%Y%m%d")}-{"".join(random.choices(string.digits, k=6))}'

    context = {
        'items': items,
        'total': total,
        'total_dias': total_dias,
        'cantidad_planes': len(items),
        'total_items_carrito': sum(i['cantidad'] for i in items),
        'perfil': perfil,
        'suscripcion_activa': suscripcion_activa,
        'nombre_completo': nombre_completo,
        'email': email,
        'referencia': referencia,
        'ahora': timezone.now(),
    }
    return render(request, 'planes/pasarela_pago_planes.html', context)


# =================== VISTAS DEL CARRITO DE PLANES ===================

@login_required
def agregar_plan_carrito(request, plan_id):
    """Agregar un plan al carrito de la sesión"""
    plan = get_object_or_404(Plan, id=plan_id)

    # Aceptar cantidad tanto por POST (formulario) como por GET (botón directo)
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
    else:
        cantidad = int(request.GET.get('cantidad', 1))

    if cantidad <= 0:
        messages.error(request, 'La cantidad debe ser mayor a 0.')
        return redirect('planes:ver_planes')

    carrito = request.session.get('carrito_planes', {})

    if str(plan_id) in carrito:
        carrito[str(plan_id)]['cantidad'] += cantidad
    else:
        carrito[str(plan_id)] = {
            'id': plan.id,
            'nombre': plan.nombre,
            'precio': float(plan.precio),
            'cantidad': cantidad,
            'duracion_dias': plan.duracion_dias,
            'descripcion': plan.descripcion,
        }

    request.session['carrito_planes'] = carrito
    messages.success(
        request,
        f'"{plan.nombre}" agregado al carrito correctamente. '
        f'Puedes agregar más planes. Recuerda: si compras otro plan, los días se sumarán '
        f'automáticamente al vencimiento de tu suscripción actual.'
    )
    return redirect('planes:ver_carrito_planes')


@login_required
def ver_carrito_planes(request):
    """Ver carrito de planes"""
    carrito = request.session.get('carrito_planes', {})
    total = 0
    total_dias = 0

    for key, item in carrito.items():
        subtotal = float(item.get('precio', 0)) * int(item.get('cantidad', 1))
        dias = int(item.get('duracion_dias', 0)) * int(item.get('cantidad', 1))
        item['subtotal'] = subtotal
        total += subtotal
        total_dias += dias

    context = {
        'carrito': carrito,
        'total': total,
        'total_dias': total_dias,
    }
    return render(request, 'planes/carrito.html', context)


@login_required
def eliminar_plan_carrito(request, plan_id):
    """Eliminar plan del carrito"""
    carrito = request.session.get('carrito_planes', {})
    if str(plan_id) in carrito:
        plan_nombre = carrito[str(plan_id)].get('nombre', 'Plan')
        del carrito[str(plan_id)]
        request.session['carrito_planes'] = carrito
        messages.success(request, f'"{plan_nombre}" eliminado del carrito.')
    return redirect('planes:ver_carrito_planes')


@login_required
def sumar_plan_carrito(request, plan_id):
    """Aumentar cantidad de plan en carrito"""
    carrito = request.session.get('carrito_planes', {})
    if str(plan_id) in carrito:
        carrito[str(plan_id)]['cantidad'] += 1
        request.session['carrito_planes'] = carrito
    return redirect('planes:ver_carrito_planes')


@login_required
def restar_plan_carrito(request, plan_id):
    """Disminuir cantidad de plan en carrito"""
    carrito = request.session.get('carrito_planes', {})
    if str(plan_id) in carrito:
        carrito[str(plan_id)]['cantidad'] -= 1
        if carrito[str(plan_id)]['cantidad'] <= 0:
            del carrito[str(plan_id)]
            messages.success(request, 'Plan eliminado del carrito.')
        request.session['carrito_planes'] = carrito
    return redirect('planes:ver_carrito_planes')


@login_required
def procesar_pago_carrito_planes(request):
    """Procesar el pago del carrito de planes"""
    carrito = request.session.get('carrito_planes', {})

    if not carrito:
        messages.error(request, 'El carrito está vacío.')
        return redirect('planes:ver_planes')

    usuario = request.user

    # Obtener o crear perfil
    perfil, _ = Perfil.objects.get_or_create(user=usuario, defaults={'rol': 'cliente'})

    # Calcular total de días
    total_dias = sum(
        int(item.get('duracion_dias', 0)) * int(item.get('cantidad', 1))
        for item in carrito.values()
    )

    # Verificar si ya tiene suscripción activa
    suscripcion_activa = Suscripcion.objects.filter(
        usuario=usuario,
        estado='activa',
        activa=True,
        fecha_fin__gte=timezone.now().date()
    ).first()

    fecha_hoy = timezone.now().date()
    total_precio = sum(
        float(item.get('precio', 0)) * int(item.get('cantidad', 1))
        for item in carrito.values()
    )
    primer_item = list(carrito.values())[0]
    primer_plan = get_object_or_404(Plan, id=primer_item['id'])

    # Si tiene suscripción activa, sumar días; si no, crear nueva
    if suscripcion_activa:
        # Sumar días a la suscripción existente
        nueva_fecha_fin = suscripcion_activa.fecha_fin + timedelta(days=total_dias)
        suscripcion_activa.fecha_fin = nueva_fecha_fin
        suscripcion_activa.estado = 'activa'
        suscripcion_activa.activa = True
        suscripcion_activa.save()
        suscripcion = suscripcion_activa
    else:
        # Crear nueva suscripción
        suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=primer_plan,
            fecha_inicio=fecha_hoy,
            fecha_fin=fecha_hoy + timedelta(days=total_dias),
            objetivo_rutina='mantener',
            acepto_terminos=True,
            estado='activa',
            activa=True
        )

    # Crear ventas para cada plan en el carrito
    for item in carrito.values():
        plan = get_object_or_404(Plan, id=item['id'])
        for _ in range(int(item.get('cantidad', 1))):
            Venta.objects.create(
                usuario=usuario,
                plan=plan,
                precio=plan.precio,
                acepto_terminos=True
            )

    # Enviar comprobante de pago del carrito
    pago_ok, pago_msg = enviar_comprobante_pago(
        usuario,
        plan=primer_plan,
        total=total_precio,
        tipo_pago='plan'
    )
    if pago_ok:
        messages.success(request, f"📧 {pago_msg}")
    else:
        messages.warning(
            request,
            f"⚠️ Hubo un problema al enviar el comprobante de pago: {pago_msg}"
        )

    # Limpiar carrito
    request.session['carrito_planes'] = {}

    messages.success(
        request,
        f'¡Pago confirmado! Se han agregado {total_dias} días a tu suscripción. '
        f'Tu plan se ha extendido hasta la nueva fecha de vencimiento.'
    )
    return redirect('mis_compras')
