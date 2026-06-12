from django.test import TestCase
from maquinaria.models import Maquinaria


class MaquinariaModelTest(TestCase):

    def test_crear_maquinaria(self):
        maquina = Maquinaria.objects.create(
            nombre="Cinta de correr",
            estado="activa"
        )

        self.assertEqual(maquina.nombre, "Cinta de correr")
        self.assertEqual(maquina.estado, "activa")