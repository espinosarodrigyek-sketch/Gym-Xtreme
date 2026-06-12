"""
Tests para el sistema Gym Django
"""
from django.test import TestCase
from django.contrib.auth.models import User
from usuarios.models import Perfil, Suscripcion
from productos.models import Producto, Categoria
from planes.models import Plan
from proveedores.models import Proveedor
from maquinaria.models import Maquinaria
from compras.models import Compra, DetalleCompra


class ModelTestCase(TestCase):
    """Tests básicos de modelos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@gym.com',
            password='test123'
        )
        self.plan = Plan.objects.create(
            nombre='Plan Test',
            tipo='1_mes',
            precio=100000,
            duracion_dias=30
        )
    
    def test_crear_usuario(self):
        """Verifica que se crea usuario correctamente"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('test123'))
    
    def test_perfil_creado(self):
        """Verifica que el perfil se crea automáticamente"""
        perfil = Perfil.objects.get(user=self.user)
        self.assertEqual(perfil.rol, 'cliente')
    
    def test_crear_plan(self):
        """Verifica que se crea un plan correctamente"""
        self.assertEqual(self.plan.nombre, 'Plan Test')
        self.assertEqual(self.plan.precio, 100000)
    
    def test_crear_suscripcion(self):
        """Verifica que se crea una suscripción"""
        from datetime import timedelta
        from django.utils import timezone
        
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=30)
        
        suscripcion = Suscripcion.objects.create(
            usuario=self.user,
            plan=self.plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activa=True
        )
        
        self.assertTrue(suscripcion.activa)
        self.assertEqual(suscripcion.usuario, self.user)


class ProductoTestCase(TestCase):
    """Tests para productos"""
    
    def setUp(self):
        """Setup antes de cada prueba"""
        self.categoria = Categoria.objects.create(
            nombre='Suplementos',
            descripcion='Proteinas y suplementos'
        )
    
    def test_crear_producto(self):
        """Verifica que se crea un producto"""
        producto = Producto.objects.create(
            nombre='Test Producto',
            descripcion='Descripcion test',
            categoria=self.categoria,
            precio_costo=50000,
            precio_venta=80000,
            stock_actual=10,
            estado='activo'
        )
        
        self.assertEqual(producto.margen_ganancia(), 30000)
        self.assertEqual(producto.porcentaje_margen(), 60)


class CompraTestCase(TestCase):
    """Tests para compras"""
    
    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre='Suplementos',
            descripcion='Proteinas'
        )
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            telefono='123456',
            email='test@proveedor.com',
            estado='activo'
        )
        self.producto = Producto.objects.create(
            nombre='Producto Test',
            descripcion='Test',
            categoria=self.categoria,
            precio_costo=10000,
            precio_venta=15000,
            stock_actual=5,
            estado='activo'
        )
    
    def test_crear_compra(self):
        """Verifica que se crea una compra con total"""
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=0
        )
        
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=self.producto,
            cantidad=10,
            precio_unitario=10000,
            subtotal=100000
        )
        
        # Recargar compra para obtener el total actualizado
        compra.refresh_from_db()
        
        self.assertEqual(compra.total, 100000)
