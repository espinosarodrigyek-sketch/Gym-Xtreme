from django.test import TestCase
from proveedores.models import Proveedor


class ProveedorModelTest(TestCase):

    def test_crear_proveedor(self):
        proveedor = Proveedor.objects.create(
            nombre="Proveedor 1",
            estado="activo"
        )

        self.assertEqual(proveedor.nombre, "Proveedor 1")