from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.db.models import Sum, Count, Q
from django.core.cache import cache

from .models import Perfil, Suscripcion, Venta, HistorialPeso, MetaUsuario, Notificacion
from .forms import LoginForm, RegistroForm
from planes.models import Plan
from compras.models import Compra
from productos.models import Producto
from .decorators import admin_required, superadmin_required
from .utils import enviar_rutina_correo, obtener_frase_motivacional, obtener_objetivo_usuario, analizar_progreso, obtener_rutina_activa, NOMBRES_RUTINA
import json


def sobre_nosotros(request):
    """Vista para la página Sobre Nosotros"""
    return render(request, 'usuarios/sobre_nosotros.html')


def terminos_condiciones(request):
    """Vista para mostrar los Términos y Condiciones legales"""
    terminos = TerminosYCondiciones.get_terminos_activos()
    if not terminos:
        # Si no hay términos en la BD, mostrar un mensaje
        return render(request, 'usuarios/terminos.html', {
            'terminos': None
        })
    return render(request, 'usuarios/terminos.html', {
        'terminos': terminos
    })


def home(request):
    from django.core.cache import cache
    
    frase_motivacional = cache.get('frase_motivacional_home')
    if not frase_motivacional:
        from api.frases import obtener_frase_motivacional
        frase_motivacional = obtener_frase_motivacional()
        cache.set('frase_motivacional_home', frase_motivacional, 60)
    
    suscripcion_activa = None
    perfil = None
    imc = None
    clasificacion_imc = None
    objetivo_usuario = None
    dias_restantes = 0
    
    if request.user.is_authenticated:
        suscripcion_activa = Suscripcion.objects.filter(
            usuario=request.user,
            fecha_fin__gte=timezone.now().date()
        ).select_related('plan').first()
        
        if suscripcion_activa:
            dias_restantes = (suscripcion_activa.fecha_fin - timezone.now().date()).days
        
        try:
            perfil = Perfil.objects.get(user=request.user)
            imc = perfil.calcular_imc()
            clasificacion_imc = perfil.get_clasificacion_imc()
            objetivo_usuario = perfil.get_objetivo()
        except Perfil.DoesNotExist:
            perfil = None
    
    planes_destacados = Plan.objects.all()[:3]
    
    context = {
        'frase_motivacional': frase_motivacional,
        'suscripcion_activa': suscripcion_activa,
        'perfil': perfil,
        'imc': imc,
        'clasificacion_imc': clasificacion_imc,
        'objetivo_usuario': objetivo_usuario,
        'dias_restantes': dias_restantes,
        'planes_destacados': planes_destacados,
    }
    return render(request, 'home.html', context)


from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO
from .decorators import admin_required
from .models import Perfil, Suscripcion, Venta, HistorialPeso, MetaUsuario, Rutina, Ejercicio, TerminosYCondiciones
from planes.models import Plan
from ventas.models import Venta as VentaProducto, DetalleVenta
from productos.models import Producto
from django.db.models import Sum, Count
from django import forms
import csv
import logging


def ver_rutinas(request):
    """Vista para mostrar las rutinas disponibles"""
    from django.db.models import Count
    
    # Obtener parámetro next para saber a dónde regresar después de seleccionar
    next_url = request.GET.get('next', '')
    
    # Verificar si hay una selección de rutina pendiente (viene de la compra)
    rutina_seleccionada_id = request.session.get('rutina_seleccionada')
    
    # Obtener rutinas de la base de datos con optimización de consultas
    rutinas_db = Rutina.objects.filter(activa=True).prefetch_related(
        'ejercicios'
    ).annotate(
        num_ejercicios=Count('ejercicios')
    ).order_by('-es_predeterminada', '-fecha_creacion')
    
    if rutinas_db.exists():
        return render(request, 'rutinas/ver_rutinas.html', {
            'frase_motivacional': obtener_frase_motivacional(),
            'rutinas': rutinas_db,
            'usar_db': True,
            'next_url': next_url,
            'rutina_seleccionada_id': rutina_seleccionada_id,
        })
    
    # Fallback a rutinas legacy
    rutinas = [
        {'objetivo': 'bajar_peso', 'nombre': 'Bajar de Peso', 'icono': 'fa-fire', 'descripcion': 'Rutina enfocada en quema de grasa'},
        {'objetivo': 'subir_masa', 'nombre': 'Subir Masa Muscular', 'icono': 'fa-dumbbell', 'descripcion': 'Para ganar músculo y fuerza'},
        {'objetivo': 'mantener', 'nombre': 'Mantener Peso', 'icono': 'fa-balance-scale', 'descripcion': 'Mantén tu condición física'},
        {'objetivo': 'definir', 'nombre': 'Definir Musculatura', 'icono': 'fa-user-ninja', 'descripcion': 'Para definir y tonificar'},
        {'objetivo': 'cardio', 'nombre': 'Cardio y Resistencia', 'icono': 'fa-heartbeat', 'descripcion': 'Mejora tu resistencia'},
    ]
    
    return render(request, 'rutinas/ver_rutinas.html', {
        'frase_motivacional': obtener_frase_motivacional(),
        'rutinas': rutinas,
        'usar_db': False,
        'next_url': next_url,
    })


def seleccionar_rutina(request, rutina_id):
    """Vista para seleccionar una rutina y volver al flujo de compra"""
    from django.http import HttpResponseRedirect
    
    # Obtener la rutina seleccionada
    rutina = get_object_or_404(Rutina, id=rutina_id, activa=True)
    
    # Guardar en sesión la rutina seleccionada con todos los datos necesarios
    request.session['rutina_seleccionada'] = {
        'id': rutina.id,
        'nombre': rutina.nombre,
        'duracion_dias': rutina.duracion_dias,
        'nivel': rutina.nivel,
    }
    
    # Obtener la URL de vuelta (next)
    next_url = request.GET.get('next', '')
    
    if next_url:
        return HttpResponseRedirect(next_url)
    
    # Por defecto volver a rutinas
    return HttpResponseRedirect(reverse('ver_rutinas'))


def ver_rutina_detalle(request, rutina_id):
    """Vista para mostrar el detalle de una rutina desde la base de datos"""
    rutina = get_object_or_404(Rutina, id=rutina_id, activa=True)
    ejercicios_por_dia = rutina.get_ejercicios_por_dia()
    
    dias_orden = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    
    return render(request, 'rutinas/detalle_rutina.html', {
        'rutina': rutina,
        'ejercios_por_dia': ejercicios_por_dia,
        'dias_orden': dias_orden,
    })


def ver_rutina_detalle_legacy(request, objetivo, duracion):
    """Legacy function - mantiene compatibilidad con rutas antiguas"""
    from django.template.loader import render_to_string


@admin_required
def lista_rutinas_admin(request):
    """Vista para listar todas las rutinas en el panel de admin"""
    rutinas = Rutina.objects.all().prefetch_related(
        'ejercicios'
    ).annotate(
        num_ejercicios=Count('ejercicios')
    )
    
    return render(request, 'rutinas/lista_rutinas_admin.html', {
        'rutinas': rutinas,
    })


@admin_required
def crear_rutina_admin(request):
    """Vista para crear una rutina desde el admin"""
    from .forms import RutinaForm, EjercicioForm
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        form = RutinaForm(request.POST, request.FILES)
        
        ejercicios_data = []
        
        # First try to read from JSON field (new format)
        ejercicios_json = request.POST.get('ejercicios_api', '')
        if ejercicios_json:
            try:
                ejercicios_array = json.loads(ejercicios_json)
                for i, ej in enumerate(ejercicios_array):
                    api_id = ej.get('api_id', '')
                    ejercicios_data.append({
                        'nombre': ej.get('nombre', ''),
                        'descripcion': ej.get('descripcion', ''),
                        'series': int(ej.get('series', 3)),
                        'repeticiones': ej.get('repeticiones', '10-12'),
                        'descanso': int(ej.get('descanso', 60)),
                        'dia': ej.get('dia', 'lunes'),
                        'orden': i + 1,
                        'ejercicio_externo_id': str(api_id) if api_id else None,
                    })
                logger.info(f"Loaded {len(ejercicios_data)} exercises from JSON field")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
        
        # Fallback: read from indexed fields (old format)
        if not ejercicios_data:
            ejercicio_count = int(request.POST.get('ejercicio_count', 0))
            logger.info(f"ejercicio_count from POST: {ejercicio_count}")
            
            for i in range(ejercicio_count):
                nombre = request.POST.get(f'ejercicio_nombre_{i}')
                logger.info(f"Exercise {i}: nombre={nombre}")
                
                if nombre:
                    api_id = request.POST.get(f'ejercicio_api_id_{i}')
                    ejercicios_data.append({
                        'nombre': nombre,
                        'descripcion': request.POST.get(f'ejercicio_desc_{i}', ''),
                        'series': int(request.POST.get(f'ejercicio_series_{i}', 3) or 3),
                        'repeticiones': request.POST.get(f'ejercicio_reps_{i}', '10-12') or '10-12',
                        'descanso': int(request.POST.get(f'ejercicio_descanso_{i}', 60) or 60),
                        'dia': request.POST.get(f'ejercicio_dia_{i}', 'lunes') or 'lunes',
                        'orden': i + 1,
                        'ejercicio_externo_id': str(api_id) if api_id else None,
                    })
        
        logger.info(f"Total ejercicios_data: {len(ejercicios_data)}")
        
        if form.is_valid():
            rutina = form.save(commit=False)
            rutina.creada_por = request.user
            rutina.save()
            
            for ej in ejercicios_data:
                Ejercicio.objects.create(rutina=rutina, **ej)
            
            messages.success(request, f'Rutina "{rutina.nombre}" creada correctamente con {len(ejercicios_data)} ejercicios')
            return redirect('lista_rutinas_admin')
        else:
            messages.error(request, 'Por favor corrija los errores del formulario')
    else:
        form = RutinaForm()
    
    ejercicio_form = EjercicioForm()
    dias = Ejercicio.DIA_CHOICES
    
    return render(request, 'rutinas/form_rutina_admin.html', {
        'form': form,
        'ejercicio_form': ejercicio_form,
        'dias': dias,
        'es_crear': True,
    })


@admin_required
def editar_rutina_admin(request, rutina_id):
    """Vista para editar una rutina"""
    from .forms import RutinaForm, EjercicioForm
    
    rutina = get_object_or_404(Rutina, id=rutina_id)
    ejercicios = rutina.ejercicios.all().order_by('dia', 'orden')
    
    if request.method == 'POST':
        form = RutinaForm(request.POST, request.FILES, instance=rutina)
        
        ejercicios_data = []
        ejercicio_count = int(request.POST.get('ejercicio_count', 0))
        
        for i in range(ejercicio_count):
            nombre = request.POST.get(f'ejercicio_nombre_{i}')
            if nombre:
                api_id = request.POST.get(f'ejercicio_api_id_{i}')
                ejercicios_data.append({
                    'nombre': nombre,
                    'descripcion': request.POST.get(f'ejercicio_desc_{i}', ''),
                    'series': int(request.POST.get(f'ejercicio_series_{i}', 3)),
                    'repeticiones': request.POST.get(f'ejercicio_reps_{i}', '10-12'),
                    'descanso': int(request.POST.get(f'ejercicio_descanso_{i}', 60)),
                    'dia': request.POST.get(f'ejercicio_dia_{i}', 'lunes'),
                    'orden': i + 1,
                    'ejercicio_externo_id': str(api_id) if api_id else None,
                })
        
        if form.is_valid():
            rutina = form.save()
            
            rutina.ejercicios.all().delete()
            for ej in ejercicios_data:
                Ejercicio.objects.create(rutina=rutina, **ej)
            
            messages.success(request, f'Rutina "{rutina.nombre}" actualizada correctamente')
            return redirect('lista_rutinas_admin')
        else:
            messages.error(request, 'Por favor corrija los errores del formulario')
    else:
        form = RutinaForm(instance=rutina)
    
    ejercicio_form = EjercicioForm()
    dias = Ejercicio.DIA_CHOICES
    
    return render(request, 'rutinas/form_rutina_admin.html', {
        'form': form,
        'rutina': rutina,
        'ejercicios': ejercicios,
        'ejercicio_form': ejercicio_form,
        'dias': dias,
        'es_crear': False,
    })


@admin_required
def eliminar_rutina_admin(request, rutina_id):
    """Vista para eliminar una rutina"""
    rutina = get_object_or_404(Rutina, id=rutina_id)
    nombre = rutina.nombre
    rutina.delete()
    messages.success(request, f'Rutina "{nombre}" eliminada correctamente')
    return redirect('lista_rutinas_admin')


@login_required
@login_required
@login_required(login_url='login')
def mis_compras(request):
    """Vista para mostrar el historial de compras del usuario"""
    from ventas.models import Venta as VentaProducto, DetalleVenta
    
    # Ventas de PLANES
    ventas_planes = Venta.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Ventas de PRODUCTOS
    ventas_productos = VentaProducto.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Detalles de ventas de productos
    ventas_productos_con_detalles = []
    for venta in ventas_productos:
        detalles = DetalleVenta.objects.filter(venta=venta).select_related('producto')
        ventas_productos_con_detalles.append({
            'venta': venta,
            'detalles': detalles,
        })
    
    # Total gastado
    total_planes = sum(float(v.precio or 0) for v in ventas_planes)
    total_productos = sum(float(v.total or 0) for v in ventas_productos)
    total_gastado = total_planes + total_productos
    
    # Suscripciones
    ahora = timezone.now().date()
    suscripciones = Suscripcion.objects.filter(
        usuario=request.user,
        estado='activa',
        fecha_fin__gte=ahora
    ).order_by('-fecha_inicio')

    suscripciones_expiradas = Suscripcion.objects.filter(
        usuario=request.user,
        estado='activa',
        fecha_fin__lt=ahora
    ).order_by('-fecha_fin')

    suscripciones_canceladas = Suscripcion.objects.filter(
        usuario=request.user,
        estado='cancelada'
    ).order_by('-fecha_cancelacion')
    
    frase = None
    try:
        frase = obtener_frase_motivacional()
    except:
        pass

    context = {
        'ventas_planes': ventas_planes,
        'ventas_productos': ventas_productos_con_detalles,
        'total_gastado': total_gastado,
        'suscripciones': suscripciones,
        'suscripciones_expiradas': suscripciones_expiradas,
        'suscripciones_canceladas': suscripciones_canceladas,
        'frase_motivacional': frase,
    }
    
    return render(request, 'compras/mis_compras.html', context)


def ver_rutina_detalle_legacy(request, objetivo, duracion):
    """Vista legacy para mostrar una rutina como vista previa (sin usar DB)"""
    from django.template.loader import render_to_string
    
    # Mapeo simple de plantillas
    plantillas = {
        ('bajar_peso', '1_mes'): 'rutinas/rutina_1_mes_bajar_peso.html',
        ('bajar_peso', '6_meses'): 'rutinas/rutina_6_meses_bajar_peso.html',
        ('bajar_peso', '1_ano'): 'rutinas/rutina_1_ano_bajar_peso.html',
        ('subir_masa', '1_mes'): 'rutinas/rutina_1_mes_subir_masa.html',
        ('subir_masa', '6_meses'): 'rutinas/rutina_6_meses_subir_masa.html',
        ('subir_masa', '1_ano'): 'rutinas/rutina_1_ano_subir_masa.html',
        ('mantener', '1_mes'): 'rutinas/rutina_1_mes_mantener.html',
        ('mantener', '6_meses'): 'rutinas/rutina_6_meses_mantener.html',
        ('mantener', '1_ano'): 'rutinas/rutina_1_ano_mantener.html',
        ('definir', '1_mes'): 'rutinas/rutina_1_mes_definir.html',
        ('definir', '6_meses'): 'rutinas/rutina_6_meses_definir.html',
        ('definir', '1_ano'): 'rutinas/rutina_1_ano_definir.html',
        ('cardio', '1_mes'): 'rutinas/rutina_1_mes_cardio.html',
        ('cardio', '6_meses'): 'rutinas/rutina_6_meses_cardio.html',
        ('cardio', '1_ano'): 'rutinas/rutina_1_ano_cardio.html',
        ('subir_masa_perder_grasa', '1_mes'): 'rutinas/rutina_1_mes_subir_masa_perder_grasa.html',
        ('subir_masa_perder_grasa', '6_meses'): 'rutinas/rutina_6_meses_subir_masa_perder_grasa.html',
        ('subir_masa_perder_grasa', '1_ano'): 'rutinas/rutina_1_ano_subir_masa_perder_grasa.html',
    }
    
    duracion_dias = {'1_mes': 30, '6_meses': 180, '1_ano': 365}.get(duracion, 30)
    objetivo_nombres = {'bajar_peso': 'Bajar de Peso', 'subir_masa': 'Subir Masa', 'mantener': 'Mantener', 
                       'definir': 'Definir', 'cardio': 'Cardio', 'subir_masa_perder_grasa': 'Subir Masa y Perder Grasa'}
    
    plantilla = plantillas.get((objetivo, duracion), 'rutinas/rutina_1_mes_mantener.html')
    context = {
        'usuario': type('obj', (object,), {'username': 'Vista Previa'})(),
        'plan': type('obj', (object,), {'nombre': f"Plan {objetivo_nombres.get(objetivo, 'General')}", 'duracion_dias': duracion_dias})(),
        'objetivo': objetivo, 'perfil': None, 'duracion_real_meses': duracion_dias // 30,
        'duracion_real_dias': duracion_dias, 'tipo_plan': duracion,
    }
    
    return render(request, 'rutinas/rutina_wrapper.html', {
        'titulo': f"Rutina {objetivo_nombres.get(objetivo, 'General')} - {duracion.replace('_', ' ').title()}",
        'contenido_rutina': render_to_string(plantilla, context),
    })


def cerrar_sesion(request):
    logout(request)
    return redirect('login')


def iniciar_sesion(request):
    # Si ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Limpiar contadores de intentos fallidos al iniciar sesión exitosamente
            cache_key = f'login_attempts_{form.cleaned_data["username"]}'
            cache.delete(cache_key)

            # Verificar si es administrador
            if user.is_staff:
                return redirect('admin_panel')
            else:
                return redirect('home')
        else:
            # Registrar intento fallido con throttle
            username = request.POST.get('username', '')
            cache_key = f'login_attempts_{username}'
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, timeout=900)  # Expira en 15 minutos

            if attempts >= 5:
                messages.error(request, "Demasiados intentos fallidos. Tu cuenta está bloqueada temporalmente. Inténtalo en 15 minutos.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos. Intento %d de 5." % attempts)

    else:
        form = LoginForm()

    return render(request, "login.html", {'form': form})


def registro_usuario(request):
    # Si ya está autenticado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = RegistroForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, "El usuario ya existe")
                return render(request, "login.html", {'show_register': True, 'form': form})

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            messages.success(request, "¡Cuenta creada! Ahora puedes iniciar sesión")
            return render(request, "login.html", {'form': LoginForm()})
        else:
            return render(request, "login.html", {'show_register': True, 'form': form})

    return render(request, "login.html", {'show_register': True, 'form': RegistroForm()})


def perfil_usuario(request):
    perfil, created = Perfil.objects.get_or_create(
        user=request.user,
        defaults={'rol': 'cliente'}
    )

    if request.method == "POST":
        # Actualizar foto
        if 'foto' in request.FILES:
            perfil.foto = request.FILES['foto']

        # Actualizar datos del User
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()

        # Actualizar datos del Perfil
        perfil.telefono = request.POST.get('telefono', '').strip()
        perfil.direccion = request.POST.get('direccion', '').strip()

        edad_str = request.POST.get('edad', '').strip()
        if edad_str.isdigit():
            perfil.edad = int(edad_str)
        elif edad_str == '':
            perfil.edad = None

        peso_str = request.POST.get('peso', '').strip()
        if peso_str:
            try:
                perfil.peso = float(peso_str)
            except ValueError:
                perfil.peso = None
        else:
            perfil.peso = None

        estatura_str = request.POST.get('estatura', '').strip()
        if estatura_str:
            try:
                perfil.estatura = float(estatura_str)
            except ValueError:
                perfil.estatura = None
        else:
            perfil.estatura = None

        perfil.save()
        messages.success(request, "Perfil actualizado correctamente")
        return redirect('perfil')

    return render(request, 'perfil.html', {'perfil': perfil})

#aca esta el admin
@admin_required
def admin_panel(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Count
    from ventas.models import Venta as VentaProducto, DetalleVenta
    from usuarios.models import Venta as VentaPlan
    from compras.models import Compra
    
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_7_dias = hoy - timedelta(days=7)
    
    # ==================== MÉTRICAS PRINCIPALES ====================
    total_usuarios = User.objects.count()
    total_perfiles = Perfil.objects.count()
    total_ventas_plan = VentaPlan.objects.count()
    
    # Clientes activos (con suscripción vigente)
    clientes_activos = Suscripcion.objects.filter(activa=True, fecha_fin__gte=hoy).count()
    
    # Clientes inactivos
    clientes_inactivos = total_perfiles - clientes_activos
    
    # ==================== INGRESOS ====================
    # Ingresos del día - usar fecha__gte para evitar problemas de timezone
    ingresos_hoy_plan = VentaPlan.objects.filter(fecha__gte=hoy).aggregate(total=Sum('precio'))['total'] or 0
    ingresos_hoy_productos = DetalleVenta.objects.filter(venta__fecha__gte=hoy, venta__estado='completada').aggregate(total=Sum('subtotal'))['total'] or 0
    
    try:
        ingresos_hoy = float(ingresos_hoy_plan) + float(ingresos_hoy_productos)
    except (TypeError, ValueError):
        ingresos_hoy = 0
    
    # Ingresos de la semana
    ingresos_semana_plan = VentaPlan.objects.filter(fecha__gte=hace_7_dias).aggregate(total=Sum('precio'))['total'] or 0
    ingresos_semana_productos = DetalleVenta.objects.filter(venta__fecha__gte=hace_7_dias, venta__estado='completada').aggregate(total=Sum('subtotal'))['total'] or 0
    try:
        ingresos_semana = float(ingresos_semana_plan) + float(ingresos_semana_productos)
    except (TypeError, ValueError):
        ingresos_semana = 0
    
    # Ingresos del mes
    ingresos_mes_plan = VentaPlan.objects.filter(fecha__gte=hace_30_dias).aggregate(total=Sum('precio'))['total'] or 0
    ingresos_mes_productos = DetalleVenta.objects.filter(venta__fecha__gte=hace_30_dias, venta__estado='completada').aggregate(total=Sum('subtotal'))['total'] or 0
    try:
        ingresos_mes = float(ingresos_mes_plan) + float(ingresos_mes_productos)
    except (TypeError, ValueError):
        ingresos_mes = 0
    
    # ==================== INVERSIÓN (COMPRAS) ====================
    inversion_mes_data = Compra.objects.filter(fecha__gte=hace_30_dias).aggregate(total=Sum('total'))['total'] or 0
    try:
        inversion_mes = float(inversion_mes_data)
    except (TypeError, ValueError):
        inversion_mes = 0
    
    # ==================== GANANCIA DEL MES ====================
    cogs_mes = 0
    try:
        detalles_mes = DetalleVenta.objects.filter(
            venta__fecha__gte=hace_30_dias, 
            venta__estado='completada'
        ).select_related('producto')
        
        for dv in detalles_mes:
            try:
                if dv.producto and dv.producto.precio_costo:
                    cantidad = int(dv.cantidad) if dv.cantidad else 0
                    costo = float(dv.producto.precio_costo)
                    cogs_mes += cantidad * costo
            except (TypeError, ValueError, AttributeError):
                pass
    except Exception:
        cogs_mes = 0
    
    try:
        ganancia_mes = ingresos_mes - cogs_mes
    except (TypeError, ValueError):
        ganancia_mes = 0
    
    # Asegurar que los valores sean floats
    if not isinstance(ingresos_hoy, (int, float)):
        ingresos_hoy = 0
    if not isinstance(ingresos_semana, (int, float)):
        ingresos_semana = 0
    if not isinstance(ingresos_mes, (int, float)):
        ingresos_mes = 0
    if not isinstance(inversion_mes, (int, float)):
        inversion_mes = 0
    if not isinstance(ganancia_mes, (int, float)):
        ganancia_mes = 0
    
    # ==================== PRODUCTOS ====================
    from productos.models import Producto
    productos_bajo_stock = Producto.objects.filter(stock_actual__lte=10).order_by('stock_actual')[:5]
    total_productos = Producto.objects.count()
    total_stock = Producto.objects.aggregate(total=Sum('stock_actual'))['total'] or 0
    
    # ==================== SUSCRIPCIONES PRÓXIMAS A VENCER ====================
    proximas_vencer = Suscripcion.objects.filter(
        activa=True,
        fecha_fin__gte=hoy,
        fecha_fin__lte=hoy + timedelta(days=7)
    ).select_related('usuario', 'plan')[:5]
    
    # ==================== TOP PRODUCTOS VENDIDOS (MES) ====================
    top_productos = DetalleVenta.objects.filter(
        venta__fecha__date__gte=hace_30_dias,
        venta__estado='completada'
    ).values('producto__nombre').annotate(
        total_vendido=Sum('cantidad'),
        ingreso_total=Sum('subtotal')
    ).order_by('-total_vendido')[:5]
    
    # ==================== MAQUINARIA ====================
    from maquinaria.models import Maquinaria
    maquinaria_activa = Maquinaria.objects.filter(estado='activo').count()
    maquinaria_mantenimiento = Maquinaria.objects.filter(estado='reparacion').count()
    
    # ==================== PROVEEDORES ====================
    from proveedores.models import Proveedor
    proveedores_activos = Proveedor.objects.filter(estado='activo').count()
    
    context = {
        # Métricas principales
        'total_usuarios': total_usuarios,
        'total_perfiles': total_perfiles,
        'total_ventas': total_ventas_plan,
        'clientes_activos': clientes_activos,
        'clientes_inactivos': clientes_inactivos,
        
        # Ingresos
        'ingresos_hoy': ingresos_hoy,
        'ingresos_semana': ingresos_semana,
        'ingresos_mes': ingresos_mes,
        'inversion_mes': inversion_mes,
        'ganancia_mes': ganancia_mes,
        
        # Productos
        'productos_bajo_stock': productos_bajo_stock,
        'total_productos': total_productos,
        'total_stock': total_stock,
        
        # Suscripciones
        'proximas_vencer': proximas_vencer,
        
        # Top productos
        'top_productos': top_productos,
        
        # Maquinaria
        'maquinaria_activa': maquinaria_activa,
        'maquinaria_mantenimiento': maquinaria_mantenimiento,
        
        # Proveedores
        'proveedores_activos': proveedores_activos,
    }

    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def economia(request):
    """Panel de economía del gimnasio con cálculo de ganancia bruta e historial completo"""
    from django.utils import timezone
    from datetime import datetime
    from ventas.models import Venta as VentaProducto, DetalleVenta
    from usuarios.models import Venta as VentaPlan
    from compras.models import Compra
    
    # Obtener parámetros de filtro de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_filtro = request.GET.get('tipo', 'todos')
    
    hoy = timezone.now().date()
    
    # Por defecto, mostrar TODOS los datos (sin filtro de fecha)
    filtro_fecha = bool(fecha_inicio or fecha_fin)
    
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        fecha_inicio = None
        
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_fin = None
    
    # Helper para aplicar filtro de fecha opcional
    def aplicar_filtro_fecha(queryset, campo_fecha):
        if fecha_inicio:
            queryset = queryset.filter(**{f'{campo_fecha}__gte': fecha_inicio})
        if fecha_fin:
            queryset = queryset.filter(**{f'{campo_fecha}__lte': fecha_fin})
        return queryset
    
    # ===== INVERSIÓN TOTAL (Dinero gastado en compras a proveedores) =====
    # Solo cuenta el dinero real que salió del negocio en compras
    compras_qs = aplicar_filtro_fecha(Compra.objects.all(), 'fecha__date')
    total_inversion_data = compras_qs.aggregate(total=Sum('total'))['total'] or 0
    try:
        total_inversion = float(total_inversion_data) if total_inversion_data else 0
    except (TypeError, ValueError):
        total_inversion = 0
    
    # ===== VENTAS DE PRODUCTOS =====
    detalles_venta = DetalleVenta.objects.filter(
        venta__estado='completada'
    ).select_related('producto', 'venta')
    detalles_venta = aplicar_filtro_fecha(detalles_venta, 'venta__fecha__date')
    
    total_ventas_productos_data = detalles_venta.aggregate(
        total=Sum('subtotal')
    )['total'] or 0
    try:
        total_ventas_productos = float(total_ventas_productos_data) if total_ventas_productos_data else 0
    except (TypeError, ValueError):
        total_ventas_productos = 0
    
    # COGS = Costo de los productos vendidos (cantidad * precio_costo del producto)
    cogs_productos = 0
    try:
        detalles_list = list(detalles_venta)
        for dv in detalles_list:
            try:
                precio_costo = dv.producto.precio_costo
                if precio_costo:
                    costo = float(precio_costo)
                    cantidad = int(dv.cantidad) if dv.cantidad else 0
                    cogs_productos += costo * cantidad
            except (TypeError, ValueError, AttributeError):
                pass
    except Exception:
        cogs_productos = 0
    
    try:
        ganancia_bruta_productos = total_ventas_productos - cogs_productos
    except (TypeError, ValueError):
        ganancia_bruta_productos = 0
    
    # ===== VENTAS DE PLANES (Suscripciones) =====
    ventas_planes_qs = aplicar_filtro_fecha(VentaPlan.objects.all(), 'fecha__date')
    total_ventas_planes_data = ventas_planes_qs.aggregate(total=Sum('precio'))['total'] or 0
    
    try:
        total_ventas_planes = float(total_ventas_planes_data) if total_ventas_planes_data else 0
    except (TypeError, ValueError):
        total_ventas_planes = 0
    
    # Los planes no tienen costo de producto, toda la venta es ganancia
    try:
        ganancia_bruta_planes = float(total_ventas_planes)
    except (TypeError, ValueError):
        ganancia_bruta_planes = 0
    
    # ===== TOTALES =====
    try:
        total_ingresos = float(total_ventas_productos) + float(total_ventas_planes)
    except (TypeError, ValueError):
        total_ingresos = 0
    
    try:
        ganancia_bruta_total = float(ganancia_bruta_productos) + float(ganancia_bruta_planes)
    except (TypeError, ValueError):
        ganancia_bruta_total = 0
    
    # Margen de ganancia bruta
    margen_bruto = 0
    try:
        if total_ingresos > 0:
            margen_bruto = round((float(ganancia_bruta_total) / float(total_ingresos)) * 100, 1)
    except (TypeError, ValueError, ZeroDivisionError):
        margen_bruto = 0
    
    # ===== INVENTARIO =====
    productos = Producto.objects.all()
    inventario_venta_total = sum(
        float(p.stock_actual) * float(p.precio_venta) for p in productos
    )
    inventario_costo_total = sum(
        float(p.stock_actual) * float(p.precio_costo or 0) for p in productos
    )
    inventario_ganancia_potencial = inventario_venta_total - inventario_costo_total
    total_productos_stock = productos.aggregate(
        total_stock=Sum('stock_actual')
    )['total_stock'] or 0
    
    # Productos con margen
    productos_con_valor = []
    for p in productos:
        productos_con_valor.append({
            'id': p.id_producto,
            'nombre': p.nombre,
            'categoria': p.categoria,
            'stock_actual': p.stock_actual,
            'precio_costo': float(p.precio_costo or 0),
            'precio_venta': float(p.precio_venta),
            'margen_unidad': p.margen_ganancia(),
            'porcentaje_margen': p.porcentaje_margen(),
            'valor_venta': float(p.stock_actual) * float(p.precio_venta),
            'valor_costo': float(p.stock_actual) * float(p.precio_costo or 0),
        })
    
    # ===== TOP PRODUCTOS MÁS VENDIDOS =====
    top_productos_qs = DetalleVenta.objects.filter(
        venta__estado='completada'
    )
    top_productos_qs = aplicar_filtro_fecha(top_productos_qs, 'venta__fecha__date')
    top_productos = top_productos_qs.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad'),
        ingreso_total=Sum('subtotal')
    ).order_by('-total_vendido')[:5]
    
    # ===== HISTORIAL UNIFICADO DE TRANSACCIONES =====
    historial = []
    
    # Ventas de productos
    if tipo_filtro in ('todos', 'productos'):
        ventas_producto_qs = aplicar_filtro_fecha(
            VentaProducto.objects.filter(estado='completada'), 'fecha__date'
        ).select_related('usuario').prefetch_related('detalles__producto')
        
        for venta in ventas_producto_qs:
            detalles = venta.detalles.all()
            productos_str = ', '.join(
                [f"{d.producto.nombre} x{d.cantidad}" for d in detalles]
            )
            # Verificar si incluye maquinaria
            es_maquinaria = any(d.producto.tiene_maquina for d in detalles)
            tipo_venta = 'maquinaria' if es_maquinaria else 'producto'
            
            historial.append({
                'tipo': tipo_venta,
                'tipo_display': 'Maquinaria' if es_maquinaria else 'Producto',
                'id': venta.id_venta,
                'fecha': venta.fecha,
                'usuario': venta.usuario.username,
                'descripcion': productos_str,
                'total': float(venta.total),
                'ganancia': sum(
                    float(d.subtotal) - (int(d.cantidad) * float(d.producto.precio_costo or 0))
                    for d in detalles
                ),
                'delete_url': 'eliminar_venta',
                'delete_id': venta.id_venta,
            })
    
    # Ventas de planes
    if tipo_filtro in ('todos', 'planes'):
        ventas_planes_list = aplicar_filtro_fecha(
            Venta.objects.all(), 'fecha__date'
        ).select_related('usuario', 'plan')
        
        for venta in ventas_planes_list:
            historial.append({
                'tipo': 'plan',
                'tipo_display': 'Plan',
                'id': venta.id,
                'fecha': venta.fecha,
                'usuario': venta.usuario.username,
                'descripcion': f"Plan: {venta.plan.nombre}",
                'total': float(venta.precio),
                'ganancia': float(venta.precio),  # Planes son 100% ganancia
                'delete_url': 'eliminar_venta_plan',
                'delete_id': venta.id,
            })
    
    # Compras a proveedores
    if tipo_filtro in ('todos', 'compras'):
        compras_list = aplicar_filtro_fecha(
            Compra.objects.all(), 'fecha__date'
        ).select_related('proveedor')
        
        for compra in compras_list:
            detalles_compra = compra.detalles.all()
            productos_str = ', '.join(
                [f"{d.producto.nombre} x{d.cantidad}" for d in detalles_compra]
            ) if detalles_compra else 'Sin detalles'
            
            historial.append({
                'tipo': 'compra',
                'tipo_display': 'Compra',
                'id': compra.id_compra,
                'fecha': compra.fecha,
                'usuario': compra.proveedor.nombre,
                'descripcion': productos_str,
                'total': float(compra.total),
                'ganancia': -float(compra.total),
                'delete_url': 'ver_detalle_compra',
                'delete_id': compra.id_compra,
            })
    
    # Ordenar por fecha descendente
    historial.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Contar ventas
    total_ventas_count = VentaProducto.objects.filter(estado='completada').count()
    total_planes_count = Venta.objects.count()
    total_compras_count = Compra.objects.count()
    if filtro_fecha:
        total_ventas_count = aplicar_filtro_fecha(
            VentaProducto.objects.filter(estado='completada'), 'fecha__date'
        ).count()
        total_planes_count = aplicar_filtro_fecha(Venta.objects.all(), 'fecha__date').count()
        total_compras_count = aplicar_filtro_fecha(Compra.objects.all(), 'fecha__date').count()
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'filtro_fecha': filtro_fecha,
        'tipo_filtro': tipo_filtro,
        'hoy': hoy,
        # Inversión
        'total_inversion': total_inversion,
        # Ventas
        'total_ventas_productos': total_ventas_productos,
        'total_ventas_planes': total_ventas_planes,
        'total_ingresos': total_ingresos,
        'total_ventas_count': total_ventas_count,
        'total_planes_count': total_planes_count,
        'total_compras_count': total_compras_count,
        # Ganancias
        'cogs_productos': cogs_productos,
        'ganancia_bruta_productos': ganancia_bruta_productos,
        'ganancia_bruta_planes': ganancia_bruta_planes,
        'ganancia_bruta_total': ganancia_bruta_total,
        'margen_bruto': margen_bruto,
        # Inventario
        'inventario_venta_total': inventario_venta_total,
        'inventario_costo_total': inventario_costo_total,
        'inventario_ganancia_potencial': inventario_ganancia_potencial,
        'total_productos_stock': total_productos_stock,
        'productos': productos_con_valor,
        # Top productos
        'top_productos': top_productos,
        # Historial unificado
        'historial': historial,
        'historial_count': len(historial),
    }
    
    # === DATOS PARA GRÁFICOS ===
    # Gráfico: Ventas por mes (últimos 12 meses)
    meses_labels = []
    ventas_productos_data = []
    ventas_planes_data = []
    
    from datetime import timedelta
    import calendar
    
    for i in range(11, -1, -1):
        # Calcular el primer día del mes hace i meses
        mes_date = hoy.replace(day=1) - timedelta(days=i*30)
        # Obtener el último día del mes
        _, ultimo_dia = calendar.monthrange(mes_date.year, mes_date.month)
        fin_mes = mes_date.replace(day=ultimo_dia)
        
        mes_nombre = mes_date.strftime('%b').capitalize()
        meses_labels.append(mes_nombre)
        
        # Ventas productos del mes (sin filtro de fecha global)
        vp_mes = VentaProducto.objects.filter(
            estado='completada',
            fecha__gte=mes_date,
            fecha__lte=fin_mes
        ).aggregate(total=Sum('total'))['total'] or 0
        ventas_productos_data.append(float(vp_mes))
        
        # Ventas planes del mes
        vplan_mes = Venta.objects.filter(
            fecha__gte=mes_date,
            fecha__lte=fin_mes
        ).aggregate(total=Sum('precio'))['total'] or 0
        ventas_planes_data.append(float(vplan_mes))
    
    context['grafico_meses_labels'] = meses_labels
    context['grafico_ventas_productos'] = ventas_productos_data
    context['grafico_ventas_planes'] = ventas_planes_data
    
    # Gráfico: Distribución de ingresos (productos vs planes)
    context['grafico_distribucion_labels'] = ['Productos', 'Planes']
    context['grafico_distribucion_data'] = [float(total_ventas_productos), float(total_ventas_planes)]
    
    # Gráfico: Top 5 productos más vendidos
    context['grafico_top_productos_labels'] = [p['producto__nombre'] for p in top_productos]
    context['grafico_top_productos_data'] = [float(p['ingreso_total']) for p in top_productos]
    
    # Gráfico: Categorías más vendidas
    categorias_data = DetalleVenta.objects.filter(
        venta__estado='completada'
    ).values('producto__categoria__nombre').annotate(
        total=Sum('subtotal')
    ).order_by('-total')[:6]
    context['grafico_categorias_labels'] = [c.get('producto__categoria__nombre') or 'Sin categoría' for c in categorias_data]
    context['grafico_categorias_data'] = [float(c['total']) for c in categorias_data]
    
    # Gráfico: Resumen financiero (Ingresos, Ganancias, Inversión)
    context['grafico_financiero_labels'] = ['Ingresos', 'Ganancia Bruta', 'Inversión']
    context['grafico_financiero_data'] = [
        float(total_ingresos),
        float(ganancia_bruta_total),
        float(total_inversion)
    ]
    
    return render(request, 'admin_panel/economia.html', context)


@admin_required
def eliminar_venta_plan(request, venta_id):
    """Elimina una venta de plan"""
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
    messages.success(request, f'Venta de plan eliminada correctamente.')
    return redirect(request.GET.get('next', 'economia'))


@admin_required
def eliminar_todas_ventas(request):
    """Elimina TODAS las ventas de productos y planes (para limpiar)"""
    from django.db import connection
    from ventas.models import Venta as VentaProducto, DetalleVenta
    from maquinaria.models import Maquinaria

    if request.method == 'POST':
        # Restaurar stock de todas las ventas de productos
        detalles = DetalleVenta.objects.select_related('producto').all()
        for detalle in detalles:
            producto = detalle.producto
            producto.stock_actual += detalle.cantidad
            producto.save()
            if producto.tiene_maquina and producto.maquina_id:
                try:
                    maquina = Maquinaria.objects.get(id_maquina=producto.maquina_id)
                    maquina.estado = "venta"
                    maquina.motivo_salida = ""
                    maquina.save()
                except Maquinaria.DoesNotExist:
                    pass

        count_productos = VentaProducto.objects.count()
        count_planes = Venta.objects.count()
        DetalleVenta.objects.all().delete()
        VentaProducto.objects.all().delete()
        Venta.objects.all().delete()

        messages.success(request, f'Se eliminaron {count_productos} ventas de productos y {count_planes} ventas de planes. Stock restaurado.')
    return redirect('economia')


@admin_required
def economia_reporte_pdf(request):
    """Genera un reporte PDF del panel de economía"""
    from django.utils import timezone
    from datetime import datetime
    from io import BytesIO
    from ventas.models import Venta as VentaProducto, DetalleVenta
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from gym.formato import formato_cop

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    hoy = timezone.now().date()
    filtro_fecha = bool(fecha_inicio or fecha_fin)

    if fecha_inicio:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        fecha_inicio_dt = None

    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_fin_dt = None

    def aplicar_filtro(queryset, campo):
        if fecha_inicio_dt:
            queryset = queryset.filter(**{f'{campo}__gte': fecha_inicio_dt})
        if fecha_fin_dt:
            queryset = queryset.filter(**{f'{campo}__lte': fecha_fin_dt})
        return queryset

    # Ventas de productos
    detalles = DetalleVenta.objects.filter(venta__estado='completada').select_related('producto', 'venta')
    detalles = aplicar_filtro(detalles, 'venta__fecha__date')
    total_ventas_productos = detalles.aggregate(total=Sum('subtotal'))['total'] or 0
    cogs = sum(int(dv.cantidad) * float(dv.producto.precio_costo or 0) for dv in detalles)
    ganancia_productos = float(total_ventas_productos) - cogs

    # Ventas de planes
    ventas_planes = aplicar_filtro(Venta.objects.all(), 'fecha__date')
    total_planes = ventas_planes.aggregate(total=Sum('precio'))['total'] or 0

    # Compras
    compras = aplicar_filtro(Compra.objects.all(), 'fecha__date')
    total_inversion = compras.aggregate(total=Sum('total'))['total'] or 0

    # Totales
    total_ingresos = float(total_ventas_productos) + float(total_planes)
    ganancia_total = ganancia_productos + float(total_planes)
    balance = total_ingresos - float(total_inversion) - cogs

    template = get_template('admin_panel/economia_reporte_pdf.html')
    html = template.render({
        'fecha_inicio': fecha_inicio_dt,
        'fecha_fin': fecha_fin_dt,
        'filtro_fecha': filtro_fecha,
        'hoy': hoy,
        'detalles_venta': detalles,
        'ventas_planes': ventas_planes,
        'compras': compras,
        'total_ventas_productos': total_ventas_productos,
        'total_planes': total_planes,
        'total_ingresos': total_ingresos,
        'cogs': cogs,
        'ganancia_productos': ganancia_productos,
        'ganancia_total': ganancia_total,
        'total_inversion': total_inversion,
        'balance': balance,
        'formato_cop': formato_cop,
    })

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_economia.pdf"'
    return response


@admin_required
def economia_reporte_excel(request):
    """Exporta el reporte de economía a Excel (CSV)"""
    import csv
    import io
    from datetime import datetime
    from django.db.models import Sum
    from ventas.models import Venta as VentaProducto, DetalleVenta
    from usuarios.models import Venta as VentaPlan
    from compras.models import Compra, DetalleCompra
    from gym.formato import formato_cop

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        fecha_inicio_dt = None

    if fecha_fin:
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_fin_dt = None

    def aplicar_filtro(queryset, campo):
        if fecha_inicio_dt:
            queryset = queryset.filter(**{f'{campo}__gte': fecha_inicio_dt})
        if fecha_fin_dt:
            queryset = queryset.filter(**{f'{campo}__lte': fecha_fin_dt})
        return queryset

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['REPORTE FINANCIERO - GYM XTREME'])
    if fecha_inicio_dt and fecha_fin_dt:
        writer.writerow([f'Periodo: {fecha_inicio_dt} - {fecha_fin_dt}'])
    else:
        writer.writerow(['Periodo: Todos los registros'])
    writer.writerow([])

    detalles = DetalleVenta.objects.filter(venta__estado='completada').select_related('producto', 'venta')
    detalles = aplicar_filtro(detalles, 'venta__fecha__date')
    total_ventas_productos = detalles.aggregate(total=Sum('subtotal'))['total'] or 0
    cogs = sum(int(dv.cantidad) * float(dv.producto.precio_costo or 0) for dv in detalles)
    ganancia_productos = float(total_ventas_productos) - cogs

    ventas_planes = aplicar_filtro(VentaPlan.objects.all(), 'fecha__date')
    total_planes = ventas_planes.aggregate(total=Sum('precio'))['total'] or 0

    compras = aplicar_filtro(Compra.objects.all(), 'fecha__date')
    total_inversion = compras.aggregate(total=Sum('total'))['total'] or 0

    total_ingresos = float(total_ventas_productos) + float(total_planes)
    ganancia_total = ganancia_productos + float(total_planes)

    writer.writerow(['RESUMEN FINANCIERO'])
    writer.writerow(['Ingresos Productos', total_ventas_productos])
    writer.writerow(['Ingresos Planes', total_planes])
    writer.writerow(['Ingresos Totales', total_ingresos])
    writer.writerow(['Ganancia Bruta', ganancia_total])
    writer.writerow(['Inversion (Compras)', total_inversion])
    writer.writerow([])

    writer.writerow(['VENTAS DE PRODUCTOS'])
    writer.writerow(['ID Venta', 'Fecha', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal'])
    for d in detalles:
        writer.writerow([
            d.venta.id_venta,
            d.venta.fecha.strftime('%d/%m/%Y') if d.venta.fecha else '',
            d.producto.nombre,
            d.cantidad,
            d.precio_unitario,
            d.subtotal
        ])
    writer.writerow(['Total', '', '', '', '', total_ventas_productos])
    writer.writerow([])

    writer.writerow(['VENTAS DE PLANES'])
    writer.writerow(['ID', 'Fecha', 'Usuario', 'Plan', 'Precio'])
    for v in ventas_planes:
        writer.writerow([
            v.id,
            v.fecha.strftime('%d/%m/%Y') if v.fecha else '',
            v.usuario.username,
            v.plan.nombre,
            v.precio
        ])
    writer.writerow(['Total', '', '', '', total_planes])
    writer.writerow([])

    writer.writerow(['COMPRAS A PROVEEDORES'])
    writer.writerow(['ID', 'Fecha', 'Proveedor', 'Total'])
    for c in compras:
        writer.writerow([
            c.id_compra,
            c.fecha.strftime('%d/%m/%Y') if c.fecha else '',
            c.proveedor.nombre,
            c.total
        ])
    writer.writerow(['Total', '', '', total_inversion])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_economia.csv"'
    return response


@admin_required
def gestionar_usuarios(request):

    usuarios = User.objects.all()

    return render(request, 'admin_panel/usuarios.html', {
        'usuarios': usuarios
    })
    
@superadmin_required
def crear_admin(request):

    if request.method == "POST":

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Validar campos requeridos
        if not username or not email or not password:
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, 'admin_panel/crear_admin.html')

        # Validar fortaleza de contraseña
        from django.core.exceptions import ValidationError
        from .forms import validar_contrasena
        try:
            validar_contrasena(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'admin_panel/crear_admin.html')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Ya existe un usuario con ese nombre")
            return render(request, 'admin_panel/crear_admin.html')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Ya existe un usuario con ese correo")
            return render(request, 'admin_panel/crear_admin.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.is_staff = True
        user.save()

        messages.success(request, "Administrador creado correctamente")

        return redirect('admin_panel')

    return render(request, 'admin_panel/crear_admin.html')


def crear_plan(request):

    if request.method == "POST":
        nombre = request.POST.get('nombre', '').strip()
        precio_str = request.POST.get('precio', '').strip()
        duracion_dias_str = request.POST.get('duracion_dias', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        imagen = request.FILES.get('imagen')
        tipo = request.POST.get('tipo', '1_mes')
        
        # Campo para plan personalizado
        duracion_meses_personalizado = request.POST.get('duracion_meses_personalizado', '').strip()
        duracion_dias_extra = request.POST.get('duracion_dias_extra', '').strip()

        # Validación de entrada
        errores = []
        
        if not nombre:
            errores.append("El nombre del plan es requerido")
        
        try:
            precio = float(precio_str)
            if precio <= 0:
                errores.append("El precio debe ser mayor a 0")
        except ValueError:
            errores.append("El precio debe ser un número válido")
        
        # Manejar duración para planes personalizados
        if tipo == 'personalizado':
            meses = 0
            dias_extra = 0
            
            if duracion_meses_personalizado:
                try:
                    meses = int(duracion_meses_personalizado)
                    if meses < 0 or meses > 36:
                        errores.append("Los meses deben estar entre 0 y 36")
                except ValueError:
                    errores.append("Los meses deben ser un número entero válido")
            
            if duracion_dias_extra:
                try:
                    dias_extra = int(duracion_dias_extra)
                    if dias_extra < 0 or dias_extra > 30:
                        errores.append("Los días extra deben estar entre 0 y 30")
                except ValueError:
                    errores.append("Los días extra deben ser un número entero válido")
            
            if meses == 0 and dias_extra == 0:
                errores.append("Debes ingresar al menos meses o días extra")
            else:
                duracion_dias = (meses * 30) + dias_extra
        else:
            # Para planes normales, usar el campo duracion_dias
            try:
                duracion_dias = int(duracion_dias_str)
                if duracion_dias <= 0:
                    errores.append("La duración debe ser mayor a 0 días")
            except ValueError:
                errores.append("La duración debe ser un número entero válido")
        
        if not descripcion:
            errores.append("La descripción es requerida")
        
        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, 'admin_panel/planes/crear_plan.html')

        Plan.objects.create(
            nombre=nombre,
            tipo=tipo,
            precio=precio,
            duracion_dias=duracion_dias,
            descripcion=descripcion,
            imagen=imagen
        )

        messages.success(request, "Plan creado correctamente")
        return redirect('lista_planes')

    return render(request, 'admin_panel/planes/crear_plan.html')

@admin_required
def lista_planes(request):
    planes = Plan.objects.all()
    return render(request, 'admin_panel/planes/lista_planes.html', {
        'planes': planes
    })

@admin_required
def eliminar_plan(request, plan_id):

    plan = Plan.objects.get(id=plan_id)

    plan.delete()

    return redirect('lista_planes')

@admin_required
def editar_plan(request, plan_id):

    plan = get_object_or_404(Plan, id=plan_id)

    if request.method == "POST":
        nombre = request.POST.get('nombre', '').strip()
        precio_str = request.POST.get('precio', '').strip()
        duracion_dias_str = request.POST.get('duracion_dias', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        # Validación de entrada
        errores = []
        
        if not nombre:
            errores.append("El nombre del plan es requerido")
        
        try:
            precio = float(precio_str)
            if precio <= 0:
                errores.append("El precio debe ser mayor a 0")
        except ValueError:
            errores.append("El precio debe ser un número válido")
        
        try:
            duracion_dias = int(duracion_dias_str)
            if duracion_dias <= 0:
                errores.append("La duración debe ser mayor a 0 días")
        except ValueError:
            errores.append("La duración debe ser un número entero válido")
        
        if not descripcion:
            errores.append("La descripción es requerida")
        
        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, 'admin_panel/planes/editar_plan.html', {'plan': plan})

        plan.nombre = nombre
        plan.tipo = request.POST.get('tipo', plan.tipo)
        plan.precio = precio
        plan.descripcion = descripcion
        plan.duracion_dias = duracion_dias

        # Actualizar imagen si se proporciona una nueva
        if request.FILES.get('imagen'):
            plan.imagen = request.FILES.get('imagen')

        plan.save()

        return redirect('lista_planes')

    return render(request, 'admin_panel/planes/editar_plan.html', {
        'plan': plan
    })


@admin_required
def limpiar_planes(request):
    """Elimina todos los planes (suscrito por el admin)"""
    if request.method == 'POST':
        count = Plan.objects.count()
        Plan.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} planes correctamente.')
    return redirect('lista_planes')


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
    """Elimina todos los clientes (usuarios con rol cliente) - NO elimina usuarios del sistema"""
    if request.method == 'POST':
        # Contar antes de eliminar
        count_perfiles = Perfil.objects.filter(rol='cliente').count()
        
        # Eliminar perfiles de clientes (sus datos)
        Perfil.objects.filter(rol='cliente').delete()
        
        messages.success(request, f'Se eliminaron {count_perfiles} clientes correctamente.')
    return redirect('lista_clientes')


@admin_required
def limpiar_productos(request):
    """Elimina todos los productos"""
    if request.method == 'POST':
        count = Producto.objects.count()
        Producto.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} productos correctamente.')
    return redirect('lista_productos')


@admin_required
def limpiar_proveedores(request):
    """Elimina todos los proveedores"""
    from proveedores.models import Proveedor
    if request.method == 'POST':
        count = Proveedor.objects.count()
        Proveedor.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} proveedores correctamente.')
    return redirect('lista_proveedores')


@admin_required
def limpiar_maquinaria(request):
    """Elimina toda la maquinaria"""
    from maquinaria.models import Maquinaria
    if request.method == 'POST':
        count = Maquinaria.objects.count()
        Maquinaria.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} equipos de maquinaria correctamente.')
    return redirect('lista_maquinaria')


@admin_required
def limpiar_todo(request):
    """LIMPIA TODOS LOS DATOS DEL SISTEMA EXCEPTO ADMINISTRADORES"""
    if request.method == 'POST':
        from proveedores.models import Proveedor
        from maquinaria.models import Maquinaria
        from ventas.models import Venta as VentaProducto, DetalleVenta
        
        # Contar elementos a eliminar
        datos = {
            'productos': Producto.objects.count(),
            'planes': Plan.objects.count(),
            'suscripciones': Suscripcion.objects.count(),
            'perfiles_clientes': Perfil.objects.filter(rol='cliente').count(),
            'ventas_productos': VentaProducto.objects.count(),
            'ventas_planes': Venta.objects.count(),
            'proveedores': Proveedor.objects.count(),
            'maquinaria': Maquinaria.objects.count(),
            'historial_peso': HistorialPeso.objects.count(),
            'metas': MetaUsuario.objects.count(),
        }
        
        # Eliminar en orden correcto (respetando foreign keys)
        DetalleVenta.objects.all().delete()
        VentaProducto.objects.all().delete()
        Venta.objects.all().delete()
        Suscripcion.objects.all().delete()
        HistorialPeso.objects.all().delete()
        MetaUsuario.objects.all().delete()
        Proveedor.objects.all().delete()
        Maquinaria.objects.all().delete()
        Producto.objects.all().delete()
        Plan.objects.all().delete()
        Perfil.objects.filter(rol='cliente').delete()
        
        total = sum(datos.values())
        messages.success(request, f'Se eliminaron {total} registros en total. Los administradores no fueron afectados.')
    
    return redirect('admin_panel')
    
def ver_planes(request):
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
        imc = float(perfil.peso) / (float(perfil.estatura) ** 2)
        imc = round(imc, 1)
        
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
        # Fallback: contenido por defecto si no hay términos en la BD
        terminos_contenido = """
<h1 style="text-align: center;"><strong>TÉRMINOS Y CONDICIONES - GYMXTREME</strong></h1>
<p><strong>1. RESPONSABILIDAD DEL CLIENTE:</strong><br>El cliente declara que se encuentra en condiciones físicas aptas para realizar actividad física y es responsable de elegir el plan adecuado según su estado de salud.</p>
<p><strong>2. EXONERACIÓN DE RESPONSABILIDAD:</strong><br>GymXtreme no se hace responsable por lesiones, accidentes o cualquier problema de salud que pueda surgir dentro de las instalaciones o durante la ejecución de rutinas.</p>
<p><strong>3. VALORACIÓN MÉDICA:</strong><br>Se recomienda al cliente consultar con un médico antes de iniciar cualquier programa de entrenamiento.</p>
<p><strong>4. USO DE INSTALACIONES:</strong><br>El uso de máquinas, equipos y áreas del gimnasio es bajo responsabilidad del cliente.</p>
<p><strong>5. PAGOS Y DEVOLUCIONES:</strong><br>No se realizan devoluciones una vez efectuado el pago del plan adquirido.</p>
<p><strong>6. NORMAS INTERNAS:</strong><br>El cliente se compromete a cumplir con todas las normas internas del gimnasio.</p>
<p><strong>7. ACEPTACIÓN:</strong><br>Al continuar con la compra, el cliente acepta estos términos y condiciones en su totalidad.</p>
"""
    
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
    """Vista para procesar el pago simulado"""
    if request.method != 'POST':
        return redirect('planes:ver_planes')
    
    # ✅ VALIDACIÓN OBLIGATORIA: Términos y condiciones
    acepto_terminos = request.POST.get('acepto_terminos') == 'on'
    if not acepto_terminos:
        messages.error(request, '❌ DEBES ACEPTAR LOS TÉRMINOS Y CONDICIONES para continuar con la compra.')
        return redirect('confirmar_compra', plan_id=plan_id)
    
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
            objetivo_seleccionado = 'mantener'
            rutina_id_seleccionada = None
    # Verificar si hay una rutina guardada en sesión
    elif 'rutina_seleccionada' in request.session:
        rutina_data = request.session.get('rutina_seleccionada', {})
        rutina_id_seleccionada = rutina_data.get('id')
        objetivo_seleccionado = f"rutina_{rutina_id_seleccionada}" if rutina_id_seleccionada else objetivo_seleccionado
    
    # Limpiar la sesión de rutina seleccionada después de usarla
    if 'rutina_seleccionada' in request.session:
        del request.session['rutina_seleccionada']
    
    # Simular procesamiento de pago
    
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
    
    # Actualizar peso (ya viene en kg)
    peso_str = request.POST.get('peso', '').strip()
    if peso_str:
        try:
            perfil.peso = float(peso_str)
        except ValueError:
            pass
    
    # Actualizar estatura (convertir de cm a metros)
    estatura_str = request.POST.get('estatura', '').strip()
    if estatura_str:
        try:
            estatura_cm = float(estatura_str)
            perfil.estatura = estatura_cm / 100  # Convertir cm a metros
        except ValueError:
            pass
    
    perfil.save()

    # Guardar registro en historial de peso
    if perfil.peso and perfil.estatura:
        HistorialPeso.objects.create(
            usuario=usuario,
            peso=perfil.peso,
            estatura=perfil.estatura,
            rutina=objetivo_seleccionado if objetivo_seleccionado else '',
            notas=f"Registro al comprar el plan '{plan.nombre}'",
        )
    
    # Depuración: mostrar los valores que llegan del formulario
    print(f"=== DEBUG FORMULARIO ===")
    print(f"Edad recibida: '{request.POST.get('edad', '')}'")
    print(f"Peso recibido: '{request.POST.get('peso', '')}'")
    print(f"Estatura recibida: '{request.POST.get('estatura', '')}'")
    print(f"Objetivo seleccionado: '{objetivo_seleccionado}'")
    print(f"Fecha inicio recibida: '{request.POST.get('fecha_inicio', '')}'")
    
    # Depuración: mostrar los valores guardados en perfil
    perfil.refresh_from_db()
    print(f"=== PERFIL GUARDADO ===")
    print(f"Edad en BD: {perfil.edad}")
    print(f"Peso en BD: {perfil.peso}")
    print(f"Estatura en BD: {perfil.estatura}")
    
    # Obtener la fecha de inicio seleccionada por el usuario
    fecha_inicio_str = request.POST.get('fecha_inicio', '').strip()
    fecha_hoy = timezone.now().date()
    
    # Si el usuario no selecciona fecha o es anterior a hoy, usar hoy
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
        fecha_fin__gte=timezone.now().date()
    ).first()
    
    # calcular fechas
    if suscripcion_activa:
        # Si ya tiene plan activo, la nueva fecha de inicio debe ser al día siguiente
        # de la suscripción actual
        fecha_inicio = suscripcion_activa.fecha_fin + timedelta(days=1)
        dias_a_sumar = plan.duracion_dias
        nueva_fecha_fin = fecha_inicio + timedelta(days=dias_a_sumar)
        
        # Actualizar la suscripcion existente
        suscripcion_activa.fecha_fin = nueva_fecha_fin
        if objetivo_seleccionado:
            suscripcion_activa.objetivo_rutina = objetivo_seleccionado
        suscripcion_activa.save()
        
        # Usar la suscripcion actualizada
        suscripcion = suscripcion_activa
    else:
        # Si no tiene plan activo, usar la fecha que eligió el usuario
        fecha_fin = fecha_inicio + timedelta(days=plan.duracion_dias)
        
        # crear suscripcion con el objetivo seleccionado
        suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            objetivo_rutina=objetivo_seleccionado if objetivo_seleccionado else 'mantener',
            acepto_terminos=acepto_terminos_value
        )


    # crear venta (siempre se registra la compra)
    Venta.objects.create(
        usuario=usuario,
        plan=plan,
        precio=plan.precio,
        acepto_terminos=acepto_terminos_value
    )


    # enviar correo con la rutina incluyendo el objetivo seleccionado y rutina específica
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


# ==================== HISTORIAL DE PESO ====================

@login_required
def historial_peso(request):
    """Vista principal del historial de peso con gráfica y análisis inteligente"""
    registros = HistorialPeso.objects.filter(usuario=request.user)
    metas = MetaUsuario.objects.filter(usuario=request.user, estado='activa')

    # Obtener datos para la gráfica
    registros_grafica = registros.order_by('fecha')[:30]  # Últimos 30 registros
    fechas = [r.fecha.strftime('%d/%m/%Y') for r in reversed(registros_grafica)]
    pesos = [float(r.peso) for r in reversed(registros_grafica)]
    imcs = [float(r.imc) if r.imc else 0 for r in reversed(registros_grafica)]

    # Estadísticas
    stats = {}
    if registros.exists():
        ultimo = registros.first()
        primero = registros.last()
        stats = {
            'ultimo_peso': float(ultimo.peso),
            'ultimo_imc': float(ultimo.imc) if ultimo.imc else None,
            'ultimo_color': ultimo.get_color_imc(),
            'ultimo_clasificacion': ultimo.get_clasificacion_imc(),
            'peso_inicial': float(primero.peso),
            'diferencia': round(float(ultimo.peso) - float(primero.peso), 1),
            'total_registros': registros.count(),
        }

    # Análisis inteligente del progreso
    analisis = analizar_progreso(request.user)

    # Rutina activa del usuario (de su suscripción)
    rutina_activa = analisis.get('rutina_actual')
    rutina_activa_nombre = analisis.get('rutina_actual_nombre')

    context = {
        'registros': registros[:20],
        'metas': metas,
        'fechas_json': json.dumps(fechas),
        'pesos_json': json.dumps(pesos),
        'imcs_json': json.dumps(imcs),
        'stats': stats,
        'rutinas': HistorialPeso.OBJETIVOS,
        'frase_motivacional': obtener_frase_motivacional(),
        'analisis': analisis,
        'rutina_activa': rutina_activa,
        'rutina_activa_nombre': rutina_activa_nombre,
    }
    return render(request, 'progreso/historial_peso.html', context)


@login_required
def agregar_registro_peso(request):
    """Agregar un nuevo registro de peso - la rutina se toma automáticamente de la suscripción activa"""
    if request.method == 'POST':
        peso_str = request.POST.get('peso', '').strip()
        estatura_str = request.POST.get('estatura', '').strip()
        notas = request.POST.get('notas', '').strip()

        errores = []

        try:
            peso = float(peso_str)
            if peso < 20 or peso > 300:
                errores.append("El peso debe estar entre 20 y 300 kg")
        except ValueError:
            errores.append("El peso debe ser un número válido")

        try:
            estatura_cm = float(estatura_str)
            if estatura_cm < 100 or estatura_cm > 250:
                errores.append("La estatura debe estar entre 100 y 250 cm")
            estatura = estatura_cm / 100
        except ValueError:
            errores.append("La estatura debe ser un número válido")

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect('historial_peso')

        # Obtener la rutina de la suscripción activa automáticamente
        rutina_automatica = obtener_rutina_activa(request.user)

        # Crear registro con la rutina automática
        HistorialPeso.objects.create(
            usuario=request.user,
            peso=peso,
            estatura=estatura,
            rutina=rutina_automatica if rutina_automatica else '',
            notas=notas,
        )

        # Actualizar perfil con los datos más recientes
        perfil, _ = Perfil.objects.get_or_create(user=request.user, defaults={'rol': 'cliente'})
        perfil.peso = peso
        perfil.estatura = estatura
        perfil.save()

        messages.success(request, "Registro de peso guardado correctamente")

        # Ejecutar análisis inteligente y mostrar alertas
        analisis = analizar_progreso(request.user)
        for alerta in analisis.get('alertas', []):
            if alerta['tipo'] == 'exito':
                messages.success(request, alerta['mensaje'])
            elif alerta['tipo'] == 'advertencia':
                messages.warning(request, alerta['mensaje'])
            elif alerta['tipo'] == 'sugerencia':
                messages.info(request, alerta['mensaje'])
            elif alerta['tipo'] == 'motivacion':
                messages.success(request, alerta['mensaje'])

    return redirect('historial_peso')


@login_required
@login_required
def eliminar_registro_peso(request, registro_id):
    """Eliminar un registro de peso"""
    registro = get_object_or_404(HistorialPeso, id=registro_id, usuario=request.user)

    if request.method == 'POST':
        registro.delete()
        messages.success(request, "Registro eliminado correctamente")

    return redirect('historial_peso')


# ==================== METAS ====================

@login_required
def mis_metas(request):
    """Vista de las metas del usuario"""
    metas_activas = MetaUsuario.objects.filter(usuario=request.user, estado='activa')
    metas_completadas = MetaUsuario.objects.filter(usuario=request.user, estado='completada')

    # Obtener peso actual
    ultimo_registro = HistorialPeso.objects.filter(usuario=request.user).first()
    peso_actual = float(ultimo_registro.peso) if ultimo_registro else None

    context = {
        'metas_activas': metas_activas,
        'metas_completadas': metas_completadas,
        'peso_actual': peso_actual,
        'frase_motivacional': obtener_frase_motivacional(),
    }
    return render(request, 'progreso/mis_metas.html', context)


@login_required
def crear_meta(request):
    """Crear una nueva meta"""
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()
        tipo = request.POST.get('tipo', 'peso')
        peso_objetivo_str = request.POST.get('peso_objetivo', '').strip()
        fecha_objetivo_str = request.POST.get('fecha_objetivo', '').strip()

        errores = []
        if not descripcion:
            errores.append("La descripción es requerida")

        peso_objetivo = None
        if peso_objetivo_str:
            try:
                peso_objetivo = float(peso_objetivo_str)
            except ValueError:
                errores.append("El peso objetivo debe ser un número válido")

        fecha_objetivo = None
        if fecha_objetivo_str:
            try:
                fecha_objetivo = datetime.strptime(fecha_objetivo_str, '%Y-%m-%d').date()
            except ValueError:
                errores.append("La fecha no es válida")

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect('mis_metas')

        MetaUsuario.objects.create(
            usuario=request.user,
            tipo=tipo,
            descripcion=descripcion,
            peso_objetivo=peso_objetivo,
            fecha_objetivo=fecha_objetivo,
        )

        messages.success(request, "Meta creada correctamente")

    return redirect('mis_metas')


@login_required
def completar_meta(request, meta_id):
    """Marcar una meta como completada"""
    meta = get_object_or_404(MetaUsuario, id=meta_id, usuario=request.user)

    if request.method == 'POST':
        meta.estado = 'completada'
        meta.fecha_completada = timezone.now()
        meta.save()
        messages.success(request, f"¡Felicidades! Meta completada: {meta.descripcion}")

    return redirect('mis_metas')


@login_required
def eliminar_meta(request, meta_id):
    """Eliminar una meta"""
    meta = get_object_or_404(MetaUsuario, id=meta_id, usuario=request.user)

    if request.method == 'POST':
        meta.delete()
        messages.success(request, "Meta eliminada correctamente")

    return redirect('mis_metas')


# ==================== NOTIFICACIONES ====================

@login_required
def mis_notificaciones(request):
    """Vista para ver las notificaciones del usuario"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    )
    
    # También mostrar notificaciones globales para admins
    if request.user.is_staff:
        notificaciones = Notificacion.objects.filter(
            models.Q(usuario=request.user) | models.Q(usuario__isnull=True)
        )
    
    # Separar leídas y no leídas
    notificaciones_no_leidas = notificaciones.filter(leida=False)
    notificaciones_leidas = notificaciones.filter(leida=True)[:20]
    
    context = {
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'notificaciones_leidas': notificaciones_leidas,
        'total_no_leidas': notificaciones_no_leidas.count(),
        'frase_motivacional': obtener_frase_motivacional(),
    }
    return render(request, 'notificaciones/lista.html', context)


@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Marcar una notificación como leída"""
    notificacion = get_object_or_404(Notificacion, id=notificacion_id)
    
    # Verificar que la notificación pertenece al usuario o es global
    if notificacion.usuario == request.user or (not notificacion.usuario and request.user.is_staff):
        notificacion.leida = True
        notificacion.save()
        messages.success(request, "Notificación marcada como leída")
    
    return redirect('mis_notificaciones')


@login_required
def marcar_todas_leidas(request):
    """Marcar todas las notificaciones como leídas"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    )
    
    # También marcar globales para admins
    if request.user.is_staff:
        notificaciones = Notificacion.objects.filter(
            models.Q(usuario=request.user) | models.Q(usuario__isnull=True),
            leida=False
        )
    
    count = notificaciones.count()
    notificaciones.update(leida=True)
    
    messages.success(request, f"{count} notificaciones marcadas como leídas")
    return redirect('mis_notificaciones')


# ==================== CARGA MASIVA ====================

@admin_required
def carga_masiva(request):
    """Vista para cargar datos masivamente desde CSV"""
    from productos.models import Producto, Categoria
    from usuarios.models import Perfil
    from planes.models import Plan
    from proveedores.models import Proveedor
    from maquinaria.models import Maquinaria
    from django.contrib.auth.models import User
    import csv
    from io import TextIOWrapper
    
    resultado = None
    errores = []
    
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        tipo_dato = request.POST.get('tipo_dato', 'productos')
        
        nombre_archivo = archivo.name.lower()
        
        try:
            # Leer archivo CSV
            if nombre_archivo.endswith('.csv'):
                wrapper = TextIOWrapper(archivo, encoding='utf-8')
                reader = csv.DictReader(wrapper)
                filas = list(reader)
            elif nombre_archivo.endswith(('.xlsx', '.xls')):
                errores.append("Excel no disponible. Use formato CSV.")
                return render(request, 'admin_panel/carga_masiva.html', {'resultado': resultado, 'errores': errores})
            else:
                errores.append("Formato no soportado. Use CSV.")
                return render(request, 'admin_panel/carga_masiva.html', {'resultado': resultado, 'errores': errores})
            
            creados = 0
            duplicados = 0
            
            if tipo_dato == 'categorias':
                for row in filas:
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre:
                        continue
                    
                    if Categoria.objects.filter(nombre__iexact=nombre).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        Categoria.objects.create(
                            nombre=nombre,
                            descripcion=str(row.get('descripcion', '')).strip()
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {nombre}: {str(e)}")
            
            elif tipo_dato == 'productos':
                for row in filas:
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre:
                        continue
                    
                    if Producto.objects.filter(nombre__iexact=nombre).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        categoria_id = row.get('categoria_id', '').strip()
                        categoria = None
                        if categoria_id:
                            try:
                                categoria = Categoria.objects.get(id=int(categoria_id))
                            except (Categoria.DoesNotExist, ValueError):
                                pass
                        
                        Producto.objects.create(
                            nombre=nombre,
                            descripcion=str(row.get('descripcion', '')).strip(),
                            categoria=categoria,
                            precio_costo=float(row.get('precio_costo', 0) or 0),
                            precio_venta=float(row.get('precio_venta', 0) or 0),
                            stock_actual=int(row.get('stock_actual', 0) or 0),
                            estado=str(row.get('estado', 'activo')).strip()
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {nombre}: {str(e)}")
            
            elif tipo_dato == 'clientes':
                for row in filas:
                    username = str(row.get('username', '')).strip()
                    email = str(row.get('email', '')).strip()
                    
                    if not username or not email:
                        continue
                    
                    if User.objects.filter(username=username).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=row.get('password', 'gym123456'),
                            first_name=str(row.get('first_name', '')).strip(),
                            last_name=str(row.get('last_name', '')).strip()
                        )
                        
                        Perfil.objects.create(
                            user=user,
                            telefono=str(row.get('telefono', '')).strip(),
                            edad=int(row.get('edad', 25)) if row.get('edad') else 25,
                            peso=float(row.get('peso', 0)) if row.get('peso') else None,
                            estatura=float(row.get('estatura', 1.70)) if row.get('estatura') else None
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {username}: {str(e)}")
            
            elif tipo_dato == 'planes':
                for row in filas:
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre:
                        continue
                    
                    if Plan.objects.filter(nombre__iexact=nombre).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        Plan.objects.create(
                            nombre=nombre,
                            descripcion=str(row.get('descripcion', '')).strip(),
                            precio=float(row.get('precio', 0) or 0),
                            duracion_dias=int(row.get('duracion_dias', 30) or 30)
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {nombre}: {str(e)}")
            
            elif tipo_dato == 'proveedores':
                for row in filas:
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre:
                        continue
                    
                    if Proveedor.objects.filter(nombre__iexact=nombre).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        Proveedor.objects.create(
                            nombre=nombre,
                            telefono=str(row.get('telefono', '')).strip(),
                            email=str(row.get('email', '')).strip(),
                            direccion=str(row.get('direccion', '')).strip(),
                            ciudad=str(row.get('ciudad', '')).strip(),
                            estado=str(row.get('estado', 'activo')).strip()
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {nombre}: {str(e)}")
            
            elif tipo_dato == 'usuarios':
                for row in filas:
                    username = str(row.get('username', '')).strip()
                    email = str(row.get('email', '')).strip()
                    
                    if not username or not email:
                        continue
                    
                    if User.objects.filter(username=username).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=row.get('password', 'gym123456'),
                            first_name=str(row.get('first_name', '')).strip(),
                            last_name=str(row.get('last_name', '')).strip()
                        )
                        
                        Perfil.objects.create(
                            user=user,
                            cedula=str(row.get('cedula', '')).strip(),
                            tarjeta=str(row.get('tarjeta', '')).strip(),
                            telefono=str(row.get('telefono', '')).strip(),
                            direccion=str(row.get('direccion', '')).strip(),
                            edad=int(row.get('edad', 25)) if row.get('edad') else 25,
                            rol=str(row.get('rol', 'cliente')).strip()
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {username}: {str(e)}")
            
            elif tipo_dato == 'maquinaria':
                for row in filas:
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre:
                        continue
                    
                    if Maquinaria.objects.filter(nombre__iexact=nombre).exists():
                        duplicados += 1
                        continue
                    
                    try:
                        Maquinaria.objects.create(
                            nombre=nombre,
                            descripcion=str(row.get('descripcion', '')).strip(),
                            tipo=str(row.get('tipo', 'otro')).strip(),
                            ubicacion=str(row.get('ubicacion', '')).strip(),
                            estado=str(row.get('estado', 'activo')).strip(),
                            precio_compra=float(row.get('precio_compra', 0)) if row.get('precio_compra') else None,
                            precio_venta=float(row.get('precio_venta', 0)) if row.get('precio_venta') else None
                        )
                        creados += 1
                    except Exception as e:
                        errores.append(f"Error en {nombre}: {str(e)}")
            
            resultado = {
                'creados': creados,
                'duplicados': duplicados,
                'total': creados + duplicados,
                'tipo': tipo_dato
            }
            
        except Exception as e:
            errores.append(f"Error al procesar archivo: {str(e)}")
    
    return render(request, 'admin_panel/carga_masiva.html', {
        'resultado': resultado,
        'errores': errores
    })


@admin_required
def eliminar_carga_masiva(request):
    """Vista para eliminar datos cargados masivamente"""
    from productos.models import Producto
    from usuarios.models import Perfil
    from django.contrib.auth.models import User
    from planes.models import Plan
    
    resultado = None
    errores = []
    
    if request.method == 'POST':
        tipo_dato = request.POST.get('tipo_dato', 'productos')
        modo = request.POST.get('modo', 'fecha')
        fecha_inicio = request.POST.get('fecha_inicio')
        
        try:
            if tipo_dato == 'productos':
                if modo == 'todos':
                    eliminados = Producto.objects.count()
                    Producto.objects.all().delete()
                else:
                    eliminados = Producto.objects.count()
                    Producto.objects.all().delete()
                resultado = f"{eliminados} productos eliminados"
            
            elif tipo_dato == 'clientes':
                if modo == 'todos':
                    # Eliminar todos los perfiles y usuarios relacionados
                    perfiles = Perfil.objects.all()
                    eliminados = perfiles.count()
                    for perfil in perfiles:
                        if perfil.user:
                            perfil.user.delete()
                    resultado = f"{eliminados} clientes eliminados"
                else:
                    resultado = "Eliminación por fecha no implementada"
            
            elif tipo_dato == 'planes':
                if modo == 'todos':
                    eliminados = Plan.objects.count()
                    Plan.objects.all().delete()
                else:
                    eliminados = 0
                resultado = f"{eliminados} planes eliminados"
                
        except Exception as e:
            errores.append(f"Error al eliminar: {str(e)}")
    
    return render(request, 'admin_panel/eliminar_carga_masiva.html', {
        'resultado': resultado,
        'errores': errores,
        'productos_count': Producto.objects.count(),
        'clientes_count': Perfil.objects.count(),
        'planes_count': Plan.objects.count()
    })


# ==================== ACTUALIZAR PLAN Y CANCELAR SUSCRIPCIÓN ====================

@login_required
def actualizar_plan_nuevo(request, suscripcion_id):
    """
    Vista mejorada para actualizar un plan de suscripción
    Desactiva el plan anterior y activa el nuevo de forma segura
    """
    from django.db import transaction
    
    # Obtener la suscripción actual
    suscripcion_actual = get_object_or_404(
        Suscripcion, 
        id=suscripcion_id, 
        usuario=request.user
    )
    
    # Verificar que la suscripción esté activa
    if suscripcion_actual.estado == 'cancelada':
        messages.error(request, 'No puedes actualizar una suscripción cancelada.')
        return redirect('mis_compras')
    
    # Obtener planes disponibles
    planes = Plan.objects.exclude(id=suscripcion_actual.plan.id)
    
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        nuevo_plan = get_object_or_404(Plan, id=plan_id)
        
        try:
            with transaction.atomic():
                # 1. Desactivar el plan anterior
                suscripcion_actual.estado = 'cancelada'
                suscripcion_actual.fecha_cancelacion = timezone.now().date()
                suscripcion_actual.activa = False
                suscripcion_actual.save()
                
                # 2. Crear nueva suscripción
                fecha_inicio = timezone.now().date()
                fecha_fin = fecha_inicio + timedelta(days=nuevo_plan.duracion_dias)
                
                nueva_suscripcion = Suscripcion.objects.create(
                    usuario=request.user,
                    plan=nuevo_plan,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    activa=True,
                    estado='activa',
                    objetivo_rutina=suscripcion_actual.objetivo_rutina,
                    acepto_terminos=True
                )
                
                # 3. Registrar la venta
                Venta.objects.create(
                    usuario=request.user,
                    plan=nuevo_plan,
                    precio=nuevo_plan.precio,
                    acepto_terminos=True
                )
                
                messages.success(
                    request,
                    f'¡Plan actualizado correctamente! Ahora tienes el plan {nuevo_plan.nombre} '
                    f'activo hasta {fecha_fin.strftime("%d/%m/%Y")}'
                )
                return redirect('mis_compras')
                
        except Exception as e:
            messages.error(
                request,
                f'Ocurrió un error al actualizar tu plan. Por favor, intenta de nuevo.'
            )
            return redirect('mis_compras')
    
    return render(request, 'compras/actualizar_plan.html', {
        'suscripcion_actual': suscripcion_actual,
        'planes_disponibles': planes,
    })


@login_required
def cancelar_suscripcion_nueva(request, suscripcion_id):
    """
    Vista mejorada para cancelar una suscripción
    Mantiene el historial pero marca la suscripción como cancelada
    Requiere confirmación del usuario
    """
    from django.db import transaction
    
    # Obtener la suscripción
    suscripcion = get_object_or_404(
        Suscripcion,
        id=suscripcion_id,
        usuario=request.user
    )
    
    # Verificar que no esté ya cancelada
    if suscripcion.estado == 'cancelada':
        messages.info(request, 'Esta suscripción ya ha sido cancelada.')
        return redirect('mis_compras')
    
    if request.method == 'POST':
        # El usuario confirma la cancelación
        confirmar = request.POST.get('confirmar_cancelacion')
        
        if confirmar == 'si':
            try:
                with transaction.atomic():
                    # Marcar como cancelada
                    suscripcion.estado = 'cancelada'
                    suscripcion.activa = False
                    suscripcion.fecha_cancelacion = timezone.now().date()
                    suscripcion.save()
                    
                    messages.success(
                        request,
                        f'Tu suscripción al plan {suscripcion.plan.nombre} ha sido cancelada. '
                        'Puedes reactivarla o contratar un nuevo plan en cualquier momento. '
                        'Tu historial de compras se mantiene disponible.'
                    )
                    return redirect('mis_compras')
                    
            except Exception as e:
                messages.error(
                    request,
                    'Ocurrió un error al cancelar tu suscripción. Por favor, intenta de nuevo.'
                )
                return redirect('mis_compras')
        else:
            # El usuario canceló la operación
            messages.info(request, 'Cancelación abortada.')
            return redirect('mis_compras')
    
    # GET request - mostrar página de confirmación
    return render(request, 'compras/confirmar_cancelacion.html', {
        'suscripcion': suscripcion,
    })