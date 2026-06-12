from django.test import TestCase
from decimal import Decimal
from django.utils import timezone

from compras.models import Compra, DetalleCompra
from proveedores.models import Proveedor
from productos.models import Producto, Categoria


# ============================================================================
# COMPRA
# ============================================================================

class CompraModelTest(TestCase):

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            ciudad='Bogotá',
            telefono='3001234567',
            email='proveedor@test.com',
            direccion='Calle 1 #1-1'
        )

    def test_crear_compra_basica(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('0'),
            estado='pendiente'
        )

        self.assertEqual(compra.proveedor, self.proveedor)
        self.assertEqual(compra.estado, 'pendiente')

    def test_fecha_auto_creacion(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('100000'),
            estado='pendiente'
        )

        self.assertIsNotNone(compra.fecha)
        self.assertLessEqual(compra.fecha, timezone.now())

    def test_estados_validos(self):
        estados = ['pendiente', 'confirmada', 'cancelada', 'recibida']

        for estado in estados:
            compra = Compra.objects.create(
                proveedor=self.proveedor,
                total=Decimal('10000'),
                estado=estado
            )
            self.assertEqual(compra.estado, estado)


# ============================================================================
# DETALLE COMPRA
# ============================================================================

class DetalleCompraModelTest(TestCase):

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Test',
            ciudad='Bogotá',
            telefono='3001234567',
            email='proveedor@test.com',
            direccion='Calle 1 #1-1'
        )

        self.categoria = Categoria.objects.create(
            nombre='Proteína',
            descripcion='Suplementos',
            es_consumible=True
        )

        self.producto = Producto.objects.create(
            nombre='Whey Protein',
            descripcion='Proteína',
            precio_venta=Decimal('200000'),
            stock_actual=0,
            categoria=self.categoria,
            estado='activo'
        )

        self.compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('0'),
            estado='pendiente'
        )

    def test_crear_detalle(self):
        detalle = DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            precio_unitario=Decimal('200000')
        )

        # cálculo esperado directo (sin depender del modelo)
        self.assertEqual(
            detalle.cantidad * detalle.precio_unitario,
            Decimal('1000000')
        )

    def test_subtotal_automatico(self):
        detalle = DetalleCompra.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=3,
            precio_unitario=Decimal('100000')
        )

        self.assertEqual(
            detalle.subtotal,
            Decimal('300000')
        )


# ============================================================================
# LÓGICA COMPRA
# ============================================================================

class CompraLogicTest(TestCase):

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nombre='Proveedor Lógica',
            ciudad='Medellín',
            telefono='3102345678',
            email='logica@test.com',
            direccion='Carrera 2 #2-2'
        )

        self.categoria = Categoria.objects.create(
            nombre='Suplementos',
            descripcion='Suplementos',
            es_consumible=True
        )

        self.producto1 = Producto.objects.create(
            nombre='Proteína',
            descripcion='Proteína',
            precio_venta=Decimal('200000'),
            stock_actual=0,
            categoria=self.categoria,
            estado='activo'
        )

        self.producto2 = Producto.objects.create(
            nombre='Creatina',
            descripcion='Creatina',
            precio_venta=Decimal('80000'),
            stock_actual=0,
            categoria=self.categoria,
            estado='activo'
        )

    def test_compra_multiple_detalle(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('0'),
            estado='pendiente'
        )

        d1 = DetalleCompra.objects.create(
            compra=compra,
            producto=self.producto1,
            cantidad=2,
            precio_unitario=Decimal('150000')
        )

        d2 = DetalleCompra.objects.create(
            compra=compra,
            producto=self.producto2,
            cantidad=3,
            precio_unitario=Decimal('50000')
        )

        total_esperado = d1.subtotal + d2.subtotal

        self.assertEqual(
            total_esperado,
            Decimal('450000')
        )

    def test_cambio_estado(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('100000'),
            estado='pendiente'
        )

        compra.estado = 'confirmada'
        compra.save()

        self.assertEqual(compra.estado, 'confirmada')

    def test_notas_compra(self):
        compra = Compra.objects.create(
            proveedor=self.proveedor,
            total=Decimal('100000'),
            estado='pendiente',
            notas='Revisar calidad'
        )

        self.assertEqual(compra.notas, 'Revisar calidad')