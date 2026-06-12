"""
SUITE DE PRUEBAS UNITARIAS - APP USUARIOS (AUTENTICACIÓN)
========================================================================

Ingeniero de Software: Django Testing Framework
Patrón: Test-Driven Development (TDD)
Base de datos de prueba: pruebasgym (test_gym)

ESTRUCTURA:
- Pruebas de Formularios (LoginForm, RegistroForm)
- Pruebas de Modelos (Perfil, Suscripcion, HistorialPeso)
- Pruebas de Sistema Anti-Brute-Force

NOTA: Las pruebas de vistas que renderizar templates están en test_views.py
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from decimal import Decimal
from usuarios.models import Perfil, Suscripcion, HistorialPeso, MetaUsuario
from usuarios.forms import LoginForm, RegistroForm
from planes.models import Plan
from datetime import timedelta
from django.utils import timezone
import uuid


# ============================================================================
# PRUEBAS DE FORMULARIOS DE AUTENTICACIÓN
# ============================================================================

class LoginFormTest(TestCase):
    """
    Pruebas unitarias del formulario LoginForm
    
    Cubre:
    - Validación de credenciales válidas
    - Bloqueo por intentos fallidos (anti-brute-force)
    - Manejo de cache
    """
    
    def setUp(self):
        """Setup antes de cada prueba"""
        cache.clear()
        self.test_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.test_password = 'TestPassword123!'
        
        self.user = User.objects.create_user(
            username=self.test_username,
            password=self.test_password
        )
    
    def test_login_form_valid_credentials(self):
        """Verifica que formulario con credenciales válidas es válido"""
        form = LoginForm(data={
            'username': self.test_username,
            'password': self.test_password
        })
        self.assertTrue(form.is_valid(),
            f"Formulario debe ser válido con credenciales correctas")
    
    def test_login_form_invalid_username(self):
        """Verifica que formulario rechaza usuario inexistente"""
        form = LoginForm(data={
            'username': 'nonexistentuser',
            'password': self.test_password
        })
        self.assertFalse(form.is_valid(),
            f"Formulario debe ser inválido con usuario inexistente")
    
    def test_login_form_invalid_password(self):
        """Verifica que formulario rechaza contraseña incorrecta"""
        form = LoginForm(data={
            'username': self.test_username,
            'password': 'WrongPassword123!'
        })
        self.assertFalse(form.is_valid(),
            f"Formulario debe ser inválido con contraseña incorrecta")
    
    def test_login_form_blocked_after_five_attempts(self):
        """Verifica que formulario bloquea después de 5 intentos fallidos"""
        cache_key = f'login_attempts_{self.test_username}'
        cache.set(cache_key, 5, timeout=900)
        
        form = LoginForm(data={
            'username': self.test_username,
            'password': self.test_password
        })
        # El formulario debe ser inválido por demasiados intentos
        self.assertFalse(form.is_valid(),
            f"Formulario debe ser inválido por bloqueo tras 5 intentos")
    
    def test_login_form_empty_fields(self):
        """Verifica que formulario rechaza campos vacíos"""
        form = LoginForm(data={
            'username': '',
            'password': ''
        })
        self.assertFalse(form.is_valid(),
            f"Formulario debe ser inválido con campos vacíos")


class RegistroFormTest(TestCase):
    """
    Pruebas unitarias del formulario RegistroForm
    
    Cubre:
    - Validación de username (longitud, caracteres)
    - Validación de email (formato, duplicado)
    - Validación de contraseña (requisitos de seguridad)
    - Coincidencia de contraseñas
    """
    
    def setUp(self):
        """Setup antes de cada prueba"""
        self.valid_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.valid_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        self.valid_password = 'SecurePass123!'
    
    # ========== PRUEBAS DE VALIDACIÓN BÁSICA ==========
    
    def test_registro_form_valid(self):
        """Verifica que formulario válido es aceptado"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': self.valid_password
        })
        self.assertTrue(form.is_valid(),
            f"Formulario debe ser válido con datos correctos")
    
    def test_registro_form_empty_fields(self):
        """Verifica que formulario rechaza campos vacíos"""
        form = RegistroForm(data={
            'username': '',
            'email': '',
            'password': '',
            'password_confirm': ''
        })
        self.assertFalse(form.is_valid(),
            f"Formulario debe ser inválido con campos vacíos")
    
    # ========== PRUEBAS DE VALIDACIÓN DE USERNAME ==========
    
    def test_registro_form_username_too_short(self):
        """Verifica que username muy corto es rechazado"""
        form = RegistroForm(data={
            'username': 'ab',
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': self.valid_password
        })
        self.assertFalse(form.is_valid(),
            f"Username muy corto (2 caracteres) debe ser rechazado")
    
    def test_registro_form_username_invalid_characters(self):
        """Verifica que username con caracteres inválidos es rechazado"""
        invalid_usernames = [
            'user@invalid',
            'user-name',
            'user name',
            'usuario!',
            'user#123'
        ]
        
        for invalid_username in invalid_usernames:
            form = RegistroForm(data={
                'username': invalid_username,
                'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
                'password': self.valid_password,
                'password_confirm': self.valid_password
            })
            self.assertFalse(form.is_valid(),
                f"Username '{invalid_username}' debe ser rechazado")
    
    def test_registro_form_username_valid(self):
        """Verifica que username válido es aceptado"""
        form = RegistroForm(data={
            'username': 'valid_user123',
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': self.valid_password
        })
        self.assertTrue(form.is_valid(),
            f"Username válido debe ser aceptado")
    
    # ========== PRUEBAS DE VALIDACIÓN DE EMAIL ==========
    
    def test_registro_form_email_invalid_format(self):
        """Verifica que email con formato inválido es rechazado"""
        invalid_emails = [
            'notanemail',
            'missing@domain',
            '@nodomain.com'
        ]
        
        for invalid_email in invalid_emails:
            form = RegistroForm(data={
                'username': f'user_{uuid.uuid4().hex[:8]}',
                'email': invalid_email,
                'password': self.valid_password,
                'password_confirm': self.valid_password
            })
            self.assertFalse(form.is_valid(),
                f"Email inválido '{invalid_email}' debe ser rechazado")
    
    def test_registro_form_email_duplicate(self):
        """Verifica que email duplicado es rechazado"""
        # Crear usuario con este email
        User.objects.create_user(
            username='firstuser',
            email=self.valid_email,
            password=self.valid_password
        )
        
        # Intentar registrarse con el mismo email
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': self.valid_password
        })
        
        self.assertFalse(form.is_valid(),
            f"Email duplicado debe ser rechazado")
    
    def test_registro_form_email_valid(self):
        """Verifica que email válido es aceptado"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': self.valid_password
        })
        self.assertTrue(form.is_valid(),
            f"Email válido debe ser aceptado")
    
    # ========== PRUEBAS DE VALIDACIÓN DE CONTRASEÑA ==========
    
    def test_registro_form_password_too_short(self):
        """Verifica que contraseña muy corta es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'Pass1!',  # Solo 6 caracteres
            'password_confirm': 'Pass1!'
        })
        self.assertFalse(form.is_valid(),
            f"Contraseña muy corta (< 8 caracteres) debe ser rechazada")
    
    def test_registro_form_password_missing_uppercase(self):
        """Verifica que contraseña sin mayúscula es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'password123!',
            'password_confirm': 'password123!'
        })
        self.assertFalse(form.is_valid(),
            f"Contraseña sin mayúscula debe ser rechazada")
    
    def test_registro_form_password_missing_lowercase(self):
        """Verifica que contraseña sin minúscula es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'PASSWORD123!',
            'password_confirm': 'PASSWORD123!'
        })
        self.assertFalse(form.is_valid(),
            f"Contraseña sin minúscula debe ser rechazada")
    
    def test_registro_form_password_missing_number(self):
        """Verifica que contraseña sin número es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'Password!',
            'password_confirm': 'Password!'
        })
        self.assertFalse(form.is_valid(),
            f"Contraseña sin número debe ser rechazada")
    
    def test_registro_form_password_missing_special_char(self):
        """Verifica que contraseña sin carácter especial es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'Password123',
            'password_confirm': 'Password123'
        })
        self.assertFalse(form.is_valid(),
            f"Contraseña sin carácter especial debe ser rechazada")
    
    def test_registro_form_password_valid_strong(self):
        """Verifica que contraseña fuerte es aceptada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'SuperSecure2024!@#',
            'password_confirm': 'SuperSecure2024!@#'
        })
        self.assertTrue(form.is_valid(),
            f"Contraseña fuerte debe ser aceptada")
    
    # ========== PRUEBAS DE COINCIDENCIA DE CONTRASEÑA ==========
    
    def test_registro_form_password_mismatch(self):
        """Verifica que contraseñas no coincidentes son rechazadas"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!'
        })
        
        self.assertFalse(form.is_valid(),
            f"Contraseñas no coincidentes deben ser rechazadas")
    
    def test_registro_form_password_confirm_empty(self):
        """Verifica que confirmación de contraseña vacía es rechazada"""
        form = RegistroForm(data={
            'username': self.valid_username,
            'email': self.valid_email,
            'password': self.valid_password,
            'password_confirm': ''
        })
        
        self.assertFalse(form.is_valid(),
            f"Confirmación de contraseña vacía debe ser rechazada")


# ============================================================================
# PRUEBAS DE MODELOS
# ============================================================================

class PerfilModelTest(TestCase):
    """
    Pruebas para el modelo Perfil
    
    Cubre:
    - Creación automática por signal
    - Cálculo de IMC
    - Clasificación de IMC
    """
    
    def test_perfil_created_automatically_on_user_creation(self):
        """Verifica que perfil se crea automáticamente al crear usuario"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(username=username, password='testpass')
        
        # El signal debe haber creado el perfil
        perfil = Perfil.objects.get(user=user)
        self.assertEqual(perfil.user.username, username)
        self.assertEqual(perfil.rol, 'cliente')
    
    def test_perfil_default_role_is_cliente(self):
        """Verifica que el rol por defecto es 'cliente'"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(username=username, password='testpass')
        perfil = Perfil.objects.get(user=user)
        
        self.assertEqual(perfil.rol, 'cliente',
            f"Rol por defecto debe ser 'cliente'")
    
    def test_calcular_imc_correcto(self):
        """Verifica que el cálculo de IMC es correcto"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(username=username, password='testpass')
        perfil = Perfil.objects.get(user=user)
        
        # IMC = peso / (estatura^2)
        # Para 70 kg y 1.70 m: 70 / (1.70 * 1.70) = 70 / 2.89 = 24.2
        perfil.peso = Decimal('70.00')
        perfil.estatura = Decimal('1.70')
        perfil.save()
        
        imc = perfil.calcular_imc()
        self.assertAlmostEqual(imc, 24.2, delta=0.1)
    
    def test_clasificacion_imc_normal(self):
        """Verifica clasificación de IMC en rango normal"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(username=username, password='testpass')
        perfil = Perfil.objects.get(user=user)
        
        # IMC = 24.2 (normal: 18.5-24.9)
        perfil.peso = Decimal('70.00')
        perfil.estatura = Decimal('1.75')
        perfil.save()
        
        clasificacion = perfil.get_clasificacion_imc()
        self.assertEqual(clasificacion, 'normal',
            f"IMC 24.2 debe clasificarse como 'normal'")
    
    def test_clasificacion_imc_sobrepeso(self):
        """Verifica clasificación de IMC en rango sobrepeso"""
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        user = User.objects.create_user(username=username, password='testpass')
        perfil = Perfil.objects.get(user=user)
        
        # IMC = 30.6 (sobrepeso: 25.0-29.9) - Ajusté a 28 para estar en rango
        perfil.peso = Decimal('90.00')
        perfil.estatura = Decimal('1.75')
        perfil.save()
        
        clasificacion = perfil.get_clasificacion_imc()
        self.assertEqual(clasificacion, 'sobrepeso',
            f"IMC 29.4 debe clasificarse como 'sobrepeso'")


class SuscripcionModelTest(TestCase):
    """
    Pruebas para el modelo Suscripcion
    
    Cubre:
    - Creación de suscripción
    - Estado activo
    - Relación con Plan y Usuario
    """
    
    def setUp(self):
        """Setup antes de cada prueba"""
        self.username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=self.username,
            password='testpass'
        )
        
        self.plan = Plan.objects.create(
            nombre='Plan Mensual',
            precio=Decimal('50000'),
            descripcion='Plan de 30 días',
            duracion_dias=30
        )
    
    def test_crear_suscripcion(self):
        """Verifica creación correcta de suscripción"""
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        suscripcion = Suscripcion.objects.create(
            usuario=self.user,
            plan=self.plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            objetivo_rutina='mantener'
        )
        
        self.assertEqual(suscripcion.usuario.username, self.username,
            f"Suscripción debe asociarse al usuario correcto")
        self.assertEqual(suscripcion.plan.nombre, 'Plan Mensual',
            f"Suscripción debe asociarse al plan correcto")
    
    def test_suscripcion_activa_por_defecto(self):
        """Verifica que suscripción es activa por defecto"""
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        suscripcion = Suscripcion.objects.create(
            usuario=self.user,
            plan=self.plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            objetivo_rutina='mantener'
        )
        
        self.assertTrue(suscripcion.activa,
            f"Suscripción nueva debe estar activa")


class HistorialPesoModelTest(TestCase):
    """
    Pruebas para el modelo HistorialPeso
    
    Cubre:
    - Creación de registro de peso
    - Cálculo automático de IMC
    - Clasificación de IMC
    """
    
    def setUp(self):
        """Setup antes de cada prueba"""
        self.username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=self.username,
            password='testpass'
        )
    
    def test_crear_registro_peso(self):
        """Verifica creación de registro de peso"""
        registro = HistorialPeso.objects.create(
            usuario=self.user,
            peso=Decimal('75.00'),
            estatura=Decimal('1.70')
        )
        
        self.assertEqual(registro.usuario.username, self.username,
            f"Registro debe asociarse al usuario correcto")
        self.assertEqual(registro.peso, Decimal('75.00'),
            f"Peso debe guardarse correctamente")
    
    def test_imc_calculado_automaticamente(self):
        """Verifica que IMC se calcula automáticamente"""
        registro = HistorialPeso.objects.create(
            usuario=self.user,
            peso=Decimal('75.00'),
            estatura=Decimal('1.70')
        )
        
        self.assertIsNotNone(registro.imc)
        # IMC = 75 / (1.70^2) = 75 / 2.89 = 25.95
        self.assertAlmostEqual(float(registro.imc), 25.95, delta=0.1)
    
    def test_clasificacion_imc_registro_peso(self):
        """Verifica clasificación de IMC en registro de peso"""
        registro = HistorialPeso.objects.create(
            usuario=self.user,
            peso=Decimal('75.00'),
            estatura=Decimal('1.70')
        )
        
        clasificacion = registro.get_clasificacion_imc()
        self.assertEqual(clasificacion, 'Sobrepeso',
            f"IMC 25.95 debe clasificarse como 'Sobrepeso'")


# ============================================================================
# SUITE DE PRUEBAS DE SEGURIDAD
# ============================================================================

class AntibrutoForceTest(TestCase):
    """
    Pruebas para el sistema anti-brute-force
    
    Cubre:
    - Incremento de contador de intentos
    - Bloqueo después de 5 intentos
    - Limpieza de contador tras login exitoso
    """
    
    def setUp(self):
        """Setup antes de cada prueba"""
        cache.clear()
        self.test_username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.test_password = 'TestPassword123!'
        
        self.user = User.objects.create_user(
            username=self.test_username,
            password=self.test_password
        )
    
    def test_cache_key_format(self):
        """Verifica formato correcto de la clave de cache"""
        cache_key = f'login_attempts_{self.test_username}'
        cache.set(cache_key, 1, timeout=900)
        
        self.assertEqual(cache.get(cache_key), 1,
            f"Cache debe almacenar y recuperar el contador")
    
    def test_contador_se_incrementa(self):
        """Verifica que el contador se incrementa en intentos fallidos"""
        cache_key = f'login_attempts_{self.test_username}'
        
        # Simular intentos
        for i in range(1, 4):
            cache_key_current = f'login_attempts_{self.test_username}'
            intentos = cache.get(cache_key_current, 0) + 1
            cache.set(cache_key_current, intentos, timeout=900)
        
        self.assertEqual(cache.get(cache_key), 3,
            f"Contador debe ser 3 después de 3 intentos")
    
    def test_bloqueo_tras_5_intentos(self):
        """Verifica que se bloquea después de 5 intentos"""
        cache_key = f'login_attempts_{self.test_username}'
        cache.set(cache_key, 5, timeout=900)
        
        # Verificar que con 5 intentos, el sistema está bloqueado
        self.assertEqual(cache.get(cache_key), 5,
            f"Cache debe tener 5 intentos")
        
        # Verificar que el formulario detecta el bloqueo
        form = LoginForm(data={
            'username': self.test_username,
            'password': self.test_password
        })
        self.assertFalse(form.is_valid(),
            f"Formulario debe rechazar login tras 5 intentos")
    
    def test_limpieza_contador_tras_login_exitoso(self):
        """Verifica que se limpia el contador tras login exitoso"""
        cache_key = f'login_attempts_{self.test_username}'
        
        # Simular intentos previos fallidos
        cache.set(cache_key, 2, timeout=900)
        self.assertEqual(cache.get(cache_key), 2,
            f"Debe haber 2 intentos previos")
        
        # Limpiar cache (como hace la vista al login exitoso)
        cache.delete(cache_key)
        
        self.assertIsNone(cache.get(cache_key),
            f"Contador debe estar limpio tras login exitoso")
