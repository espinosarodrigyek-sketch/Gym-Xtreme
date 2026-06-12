from django.test import TestCase, override_settings, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch
from django.contrib.messages.middleware import MessageMiddleware
from usuarios.models import Perfil, Suscripcion, HistorialPeso, Venta, Rutina
from usuarios.forms import LoginForm, RegistroForm
from planes.models import Plan
from datetime import timedelta
from django.utils import timezone
import uuid


# =========================================================
# LOGIN FORM TEST
# =========================================================

class LoginFormTest(TestCase):

    def setUp(self):
        cache.clear()
        self.username = f'user_{uuid.uuid4().hex[:6]}'
        self.password = 'Test12345!'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_login_valido(self):
        form = LoginForm(data={
            'username': self.username,
            'password': self.password
        })
        self.assertTrue(form.is_valid())

    def test_login_invalido_usuario(self):
        form = LoginForm(data={
            'username': 'fake',
            'password': self.password
        })
        self.assertFalse(form.is_valid())

    def test_login_invalido_password(self):
        form = LoginForm(data={
            'username': self.username,
            'password': 'wrong'
        })
        self.assertFalse(form.is_valid())


# =========================================================
# REGISTRO FORM TEST
# =========================================================

class RegistroFormTest(TestCase):

    def setUp(self):
        self.username = f'user_{uuid.uuid4().hex[:6]}'
        self.email = f'{uuid.uuid4().hex[:6]}@mail.com'
        self.password = 'StrongPass123!'

    def test_registro_valido(self):
        form = RegistroForm(data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'password_confirm': self.password
        })
        self.assertTrue(form.is_valid())

    def test_password_no_coinciden(self):
        form = RegistroForm(data={
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'password_confirm': 'Otro123!'
        })
        self.assertFalse(form.is_valid())


# =========================================================
# PERFIL TEST
# =========================================================

class PerfilModelTest(TestCase):

    def test_creacion_perfil_automatica(self):
        user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        perfil = Perfil.objects.get(user=user)
        self.assertEqual(perfil.rol, 'cliente')

    def test_imc(self):
        user = User.objects.create_user(username='u1')
        perfil = Perfil.objects.get(user=user)

        perfil.peso = Decimal('70')
        perfil.estatura = Decimal('1.70')
        perfil.save()

        self.assertTrue(perfil.calcular_imc() > 0)


# =========================================================
# SUSCRIPCION TEST
# =========================================================

class SuscripcionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u1')
        self.plan = Plan.objects.create(
            nombre='Plan 1',
            precio=50000,
            descripcion='Test',
            duracion_dias=30
        )

    def test_crear_suscripcion(self):
        suscripcion = Suscripcion.objects.create(
            usuario=self.user,
            plan=self.plan,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            objetivo_rutina='mantener'
        )
        self.assertTrue(suscripcion.activa)


# =========================================================
# HISTORIAL PESO
# =========================================================

class HistorialPesoModelTest(TestCase):

    def test_crear_registro(self):
        user = User.objects.create_user(username='u1')

        registro = HistorialPeso.objects.create(
            usuario=user,
            peso=75,
            estatura=1.70
        )

        self.assertTrue(registro.imc > 0)


class MisComprasSuscripcionesCanceladasTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='cancelleduser',
            email='cancelled@example.com',
            password='StrongPass123!'
        )
        self.plan = Plan.objects.create(
            nombre='Plan Cancelado',
            precio=50000,
            descripcion='Plan para pruebas',
            duracion_dias=30,
        )
        self.canceled_subscription = Suscripcion.objects.create(
            usuario=self.user,
            plan=self.plan,
            fecha_inicio=timezone.now().date() - timedelta(days=10),
            fecha_fin=timezone.now().date() + timedelta(days=20),
            activa=False,
            estado='cancelada',
            fecha_cancelacion=timezone.now().date() - timedelta(days=1),
            objetivo_rutina='mantener',
        )

    def test_mis_compras_excluye_suscripciones_canceladas_de_activas(self):
        from usuarios.views import mis_compras

        request = self.factory.get(reverse('mis_compras'))
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        request.user = self.user

        response = mis_compras(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Suscripci\xc3\xb3n cancelada por el usuario', response.content)
        self.assertIn(b'Fecha de cancelaci\xc3\xb3n:', response.content)
        self.assertNotIn(b'badge bg-success', response.content)


class ListaClientesEstadoTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(
            username='admin_clientes',
            password='StrongPass123!',
            is_staff=True,
        )

        self.cliente = User.objects.create_user(
            username='cliente_estado',
            email='cliente_estado@example.com',
            password='StrongPass123!',
        )
        Perfil.objects.get_or_create(user=self.cliente, defaults={'rol': 'cliente'})

        self.plan = Plan.objects.create(
            nombre='Plan Estado',
            precio=40000,
            descripcion='Plan para validar estado',
            duracion_dias=30,
        )
        Suscripcion.objects.create(
            usuario=self.cliente,
            plan=self.plan,
            fecha_inicio=timezone.now().date() - timedelta(days=2),
            fecha_fin=timezone.now().date() + timedelta(days=28),
            activa=True,
            estado='activa',
            objetivo_rutina='mantener',
        )

    def test_desactivar_cliente_actualiza_estado_y_la_vista(self):
        from clientes.views import lista_clientes, desactivar_cliente

        request = self.factory.post(
            reverse('desactivar_cliente', args=[self.cliente.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        request.user = self.admin
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        response = desactivar_cliente(request, self.cliente.id)

        self.assertEqual(response.status_code, 200)
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.is_active)

        listado_request = self.factory.get(reverse('lista_clientes'))
        listado_request.user = self.admin
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(listado_request)
        listado_request.session.save()
        listado = lista_clientes(listado_request)

        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, 'INACTIVO')
        self.assertContains(listado, 'badge-inactiva')


class ListaClientesFiltrosTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(
            username='admin_filtros',
            password='StrongPass123!',
            is_staff=True,
        )

        self.plan_a = Plan.objects.create(
            nombre='Plan A',
            precio=30000,
            descripcion='Plan A para pruebas',
            duracion_dias=30,
        )
        self.plan_b = Plan.objects.create(
            nombre='Plan B',
            precio=45000,
            descripcion='Plan B para pruebas',
            duracion_dias=60,
        )

        self.cliente_match = User.objects.create_user(
            username='juan_carlos',
            email='juan.carlos@example.com',
            password='StrongPass123!',
            first_name='Juan',
            last_name='Carlos',
        )
        self.cliente_match_plan_b = User.objects.create_user(
            username='juan_carlos_b',
            email='juan.carlos.planb@example.com',
            password='StrongPass123!',
            first_name='Juan',
            last_name='Carlos',
        )
        self.cliente_otros = User.objects.create_user(
            username='maria_test',
            email='maria@example.com',
            password='StrongPass123!',
            first_name='María',
            last_name='López',
        )
        self.cliente_vencida = User.objects.create_user(
            username='pedro_vencido',
            email='pedro@example.com',
            password='StrongPass123!',
            first_name='Pedro',
            last_name='Gómez',
        )

        Suscripcion.objects.create(
            usuario=self.cliente_match,
            plan=self.plan_a,
            fecha_inicio=timezone.now().date() - timedelta(days=5),
            fecha_fin=timezone.now().date() + timedelta(days=25),
            activa=True,
            estado='activa',
            objetivo_rutina='mantener',
        )
        Suscripcion.objects.create(
            usuario=self.cliente_match_plan_b,
            plan=self.plan_b,
            fecha_inicio=timezone.now().date() - timedelta(days=4),
            fecha_fin=timezone.now().date() + timedelta(days=26),
            activa=True,
            estado='activa',
            objetivo_rutina='mantener',
        )
        Suscripcion.objects.create(
            usuario=self.cliente_otros,
            plan=self.plan_b,
            fecha_inicio=timezone.now().date() - timedelta(days=3),
            fecha_fin=timezone.now().date() + timedelta(days=57),
            activa=True,
            estado='activa',
            objetivo_rutina='mantener',
        )
        Suscripcion.objects.create(
            usuario=self.cliente_vencida,
            plan=self.plan_b,
            fecha_inicio=timezone.now().date() - timedelta(days=40),
            fecha_fin=timezone.now().date() - timedelta(days=10),
            activa=False,
            estado='cancelada',
            fecha_cancelacion=timezone.now().date() - timedelta(days=5),
            objetivo_rutina='mantener',
        )

    def _request_lista_clientes(self, params=None):
        from clientes.views import lista_clientes

        request = self.factory.get(reverse('lista_clientes'), data=params or {})
        request.user = self.admin
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        return lista_clientes(request)

    def test_busqueda_por_nombre_completo_aplica_filtro(self):
        response = self._request_lista_clientes({'buscar': 'juan carlos'})

        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Juan Carlos', content)
        self.assertNotIn('maria@example.com', content)
        self.assertNotIn('Pedro Gómez', content)

    def test_plan_y_estado_se_aplican_juntos(self):
        response = self._request_lista_clientes({
            'buscar': 'juan carlos',
            'plan': str(self.plan_a.id),
            'estado': 'activa',
        })

        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content.count('class="cliente-card p-3"'), 1)
        self.assertIn('juan.carlos@example.com', content)
        self.assertNotIn('juan.carlos.planb@example.com', content)
        self.assertNotIn('maria@example.com', content)

    def test_estado_vencida_muestra_solo_clientes_sin_activa(self):
        response = self._request_lista_clientes({'estado': 'vencida'})

        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pedro Gómez', content)
        self.assertNotIn('Juan Carlos', content)
        self.assertNotIn('maria@example.com', content)


class ListaClientesPerfilTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(
            username='admin_perfil_cliente',
            password='StrongPass123!',
            is_staff=True,
        )
        self.cliente = User.objects.create_user(
            username='cliente_perfil_historial',
            email='cliente.perfil.historial@example.com',
            password='StrongPass123!',
            first_name='Cliente',
            last_name='Historial',
        )

        Perfil.objects.get_or_create(user=self.cliente, defaults={'rol': 'cliente'})

        self.plan = Plan.objects.create(
            nombre='Plan Perfil',
            precio=35000,
            descripcion='Plan para probar perfil',
            duracion_dias=30,
        )
        Suscripcion.objects.create(
            usuario=self.cliente,
            plan=self.plan,
            fecha_inicio=timezone.now().date() - timedelta(days=5),
            fecha_fin=timezone.now().date() + timedelta(days=25),
            activa=True,
            estado='activa',
            objetivo_rutina='mantener',
        )
        HistorialPeso.objects.create(
            usuario=self.cliente,
            peso=Decimal('68.50'),
            estatura=Decimal('1.70'),
        )

    def _request_lista_clientes(self):
        from clientes.views import lista_clientes

        request = self.factory.get(reverse('lista_clientes'))
        request.user = self.admin
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        return lista_clientes(request)

    def test_lista_clientes_usa_historial_peso_cuando_perfil_no_lo_tiene(self):
        response = self._request_lista_clientes()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '68.50 kg')


class ReportesClientesPermisosTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _crear_usuario_con_rol(self, username, rol, is_staff=True):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='StrongPass123!',
            is_staff=is_staff,
        )
        Perfil.objects.update_or_create(
            user=user,
            defaults={'rol': rol}
        )
        return user

    def _request(self, view_name, user):
        from clientes.views import lista_clientes, reporte_clientes_pdf

        view_map = {
            'lista_clientes': lista_clientes,
            'reporte_clientes_pdf': reporte_clientes_pdf,
        }

        request = self.factory.get(reverse(view_name))
        request.user = user
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()

        message_middleware = MessageMiddleware(lambda req: None)
        message_middleware.process_request(request)

        return view_map[view_name](request)

    def test_usuario_sin_rol_admin_no_ve_boton_reporte(self):
        user = self._crear_usuario_con_rol('cliente_staff', 'cliente', is_staff=True)

        response = self._request('lista_clientes', user)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Exportar PDF')
        self.assertNotContains(response, 'Exportar Excel')

    def test_usuario_sin_rol_admin_no_puede_descargar_reporte(self):
        user = self._crear_usuario_con_rol('cliente_staff_reporte', 'cliente', is_staff=True)

        response = self._request('reporte_clientes_pdf', user)

        self.assertEqual(response.status_code, 302)

    def test_usuario_admin_puede_descargar_reporte(self):
        user = self._crear_usuario_con_rol('admin_reporte', 'admin', is_staff=True)

        response = self._request('reporte_clientes_pdf', user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class PerfilUsuarioPersistenciaTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='perfil_persistencia',
            email='perfil.persistencia@example.com',
            password='StrongPass123!',
        )

    def test_perfil_usuario_guarda_peso_y_estatura(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('perfil'), data={
            'first_name': 'Perfil',
            'last_name': 'Persistencia',
            'email': 'perfil.persistencia@example.com',
            'telefono': '3009998888',
            'direccion': 'Calle 99',
            'edad': '31',
            'peso': '72.5',
            'estatura': '1.75',
        })

        self.assertEqual(response.status_code, 302)
        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.peso, Decimal('72.5'))
        self.assertEqual(perfil.estatura, Decimal('1.75'))


# =========================================================
# ANTIBRUTE FORCE
# =========================================================

class AntibrutoForceTest(TestCase):

    def setUp(self):
        cache.clear()
        self.username = 'testuser'
        self.password = 'Test123!'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_bloqueo_cache(self):
        cache.set(f'login_attempts_{self.username}', 5, 900)

        form = LoginForm(data={
            'username': self.username,
            'password': self.password
        })

        self.assertFalse(form.is_valid())


class ProcesarPagoRutinaCorreoTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='routineuser',
            email='routineuser@example.com',
            password='StrongPass123!'
        )
        self.plan = Plan.objects.create(
            nombre='Plan Rutina',
            precio=50000,
            descripcion='Plan de prueba',
            duracion_dias=30,
        )
        self.rutina = Rutina.objects.create(
            nombre='Rutina HIIT',
            descripcion='Rutina de alta intensidad',
            nivel='intermedio',
            duracion_dias=30,
            activa=True,
        )
        self.client.force_login(self.user)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_procesar_pago_envia_rutina_por_correo(self):
        mail.outbox = []

        session = self.client.session
        session['rutina_seleccionada'] = {
            'id': self.rutina.id,
            'nombre': self.rutina.nombre,
            'duracion_dias': self.rutina.duracion_dias,
            'nivel': self.rutina.nivel,
        }
        session.save()

        response = self.client.post(reverse('planes:procesar_pago', args=[self.plan.id]), data={
            'acepto_terminos': 'on',
            'edad': '28',
            'peso': '72',
            'estatura': '175',
            'fecha_inicio': timezone.now().date().isoformat(),
            'objetivo_rutina': 'mantener',
        })

        self.assertEqual(response.status_code, 302)
        self.assertGreaterEqual(len(mail.outbox), 1)
        rutina_emails = [
            msg for msg in mail.outbox
            if f'📋 Tu Rutina de Entrenamiento - {self.plan.nombre}' in msg.subject
        ]
        self.assertEqual(len(rutina_emails), 1)
        self.assertEqual(rutina_emails[0].to, ['routineuser@example.com'])
        self.assertIn(self.rutina.nombre, rutina_emails[0].body)
        self.assertEqual(Venta.objects.filter(usuario=self.user).count(), 1)
        self.assertEqual(Suscripcion.objects.filter(usuario=self.user).count(), 1)


class ProcesarPagoCarritoPlanesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='cartuser', password='StrongPass123!')
        self.plan = Plan.objects.create(
            nombre='Plan Caribe',
            precio=50000,
            descripcion='Plan de prueba',
            duracion_dias=30,
        )
        self.client.force_login(self.user)

    @patch('planes.views.enviar_comprobante_pago')
    def test_procesar_pago_carrito_envia_comprobante(self, mock_enviar):
        mock_enviar.return_value = (True, 'Comprobante enviado')

        session = self.client.session
        session['carrito_planes'] = {
            'item-1': {
                'id': self.plan.id,
                'precio': str(self.plan.precio),
                'duracion_dias': self.plan.duracion_dias,
                'cantidad': 1,
            }
        }
        session.save()

        response = self.client.post(reverse('planes:procesar_pago_carrito_planes'))

        self.assertEqual(response.status_code, 302)
        mock_enviar.assert_called_once()
        self.assertEqual(mock_enviar.call_args.kwargs['tipo_pago'], 'plan')
        self.assertEqual(mock_enviar.call_args.kwargs['plan'], self.plan)
        self.assertEqual(mock_enviar.call_args.kwargs['total'], float(self.plan.precio))
        self.assertEqual(Venta.objects.filter(usuario=self.user).count(), 1)
        self.assertEqual(Suscripcion.objects.filter(usuario=self.user).count(), 1)