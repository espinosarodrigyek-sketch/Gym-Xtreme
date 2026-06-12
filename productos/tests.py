from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta

from productos.models import Producto, Categoria, Lote


# ============================================================================
# CATEGORÍAS
# ============================================================================

class CategoriaModelTest(TestCase):

    def test_crear_categoria_consumible(self):
        categoria = Categoria.objects.create(
            nombre='Proteína',
            descripcion='Suplementos',
            es_consumible=True
        )

        self.assertEqual(categoria.nombre, 'Proteína')
        self.assertTrue(categoria.es_consumible)

    def test_crear_categoria_no_consumible(self):
        categoria = Categoria.objects.create(
            nombre='Ropa',
            descripcion='Deportiva',
            es_consumible=False
        )

        self.assertFalse(categoria.es_consumible)

    def test_unique_nombre_categoria(self):
        Categoria.objects.create(
            nombre='Creatina',
            descripcion='Test',
            es_consumible=True
        )

        with self.assertRaises(Exception):
            Categoria.objects.create(
                nombre='Creatina',
                descripcion='Duplicado',
                es_consumible=True
            )


# ============================================================================
# PRODUCTOS
# ============================================================================

class ProductoModelTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre='Suplementos',
            descripcion='Gym',
            es_consumible=True
        )

    def test_crear_producto(self):
        producto = Producto.objects.create(
            nombre='Whey Protein',
            descripcion='Proteína',
            categoria=self.categoria,
            precio_costo=Decimal('100000'),
            precio_venta=Decimal('150000'),
            stock_actual=10,
            estado='activo'
        )

        self.assertEqual(producto.nombre, 'Whey Protein')
        self.assertEqual(producto.precio_venta, Decimal('150000'))

    def test_estado_producto(self):
        producto = Producto.objects.create(
            nombre='Creatina',
            descripcion='Creatina',
            categoria=self.categoria,
            precio_costo=Decimal('50000'),
            precio_venta=Decimal('80000'),
            stock_actual=5,
            estado='inactivo'
        )

        self.assertEqual(producto.estado, 'inactivo')

    def test_producto_sin_imagen(self):
        producto = Producto.objects.create(
            nombre='Sin Imagen',
            descripcion='Test',
            categoria=self.categoria,
            precio_costo=Decimal('50000'),
            precio_venta=Decimal('80000'),
            stock_actual=5,
            estado='activo',
            imagen=None
        )

        self.assertFalse(producto.imagen)

    def test_producto_sin_categoria(self):
        producto = Producto.objects.create(
            nombre='Sin categoria',
            descripcion='Test',
            categoria=None,
            precio_costo=Decimal('50000'),
            precio_venta=Decimal('80000'),
            stock_actual=5,
            estado='activo'
        )

        self.assertIsNone(producto.categoria)


# ============================================================================
# LÓGICA PRODUCTO + LOTES
# ============================================================================

class ProductoLogicTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre='Suplementos',
            descripcion='Gym',
            es_consumible=True
        )

        self.producto = Producto.objects.create(
            nombre='Proteína',
            descripcion='Test',
            categoria=self.categoria,
            precio_costo=Decimal('100000'),
            precio_venta=Decimal('150000'),
            stock_actual=0,
            estado='activo'
        )

    def test_crear_lote(self):
        lote = Lote.objects.create(
            producto=self.producto,
            cantidad=10,
            precio_unitario=Decimal('100000'),
            fecha_fabricacion=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=365),
            estado='disponible'
        )

        self.assertEqual(lote.cantidad, 10)

    def test_lotes_activos(self):
        Lote.objects.create(
            producto=self.producto,
            cantidad=5,
            precio_unitario=Decimal('100000'),
            fecha_fabricacion=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=100),
            estado='disponible'
        )

        self.assertEqual(self.producto.lotes.count(), 1)

    def test_stock_total(self):
        Lote.objects.create(
            producto=self.producto,
            cantidad=10,
            precio_unitario=Decimal('100000'),
            fecha_fabricacion=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=100),
            estado='disponible'
        )

        Lote.objects.create(
            producto=self.producto,
            cantidad=20,
            precio_unitario=Decimal('100000'),
            fecha_fabricacion=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=100),
            estado='disponible'
        )

        total = sum(l.cantidad for l in self.producto.lotes.all())
        self.assertEqual(total, 30)

    def test_margen_ganancia(self):
        margen = self.producto.precio_venta - self.producto.precio_costo
        self.assertEqual(margen, Decimal('50000'))

    def test_porcentaje_margen(self):
        margen = ((self.producto.precio_venta - self.producto.precio_costo)
                  / self.producto.precio_costo) * 100
        self.assertEqual(margen, Decimal('50'))


# ============================================================================
# CARRO SIMPLE
# ============================================================================

class CarritoTest(TestCase):

    def test_total_carrito(self):
        carrito = {
            '1': {'precio': '10000', 'cantidad': 2},
            '2': {'precio': '20000', 'cantidad': 1},
        }

        total = sum(
            int(v['cantidad']) * int(v['precio'])
            for v in carrito.values()
        )

        self.assertEqual(total, 40000)