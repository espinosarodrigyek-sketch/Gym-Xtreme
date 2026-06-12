import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from usuarios.models import Perfil
from productos.models import Producto
from planes.models import Plan
from proveedores.models import Proveedor
from maquinaria.models import Maquinaria


class Command(BaseCommand):
    help = 'Elimina datos masivamente según el tipo especificado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            required=True,
            choices=['usuarios', 'productos', 'planes', 'proveedores', 'maquinaria', 'todo'],
            help='Tipo de datos a eliminar'
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Limite de registros a eliminar (los más antiguos)'
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar eliminación (sin esto solo muestra cuántos se eliminarían)'
        )

    def handle(self, *args, **options):
        tipo = options.get('tipo')
        limite = options.get('limite')
        confirmar = options.get('confirmar')
        
        if not confirmar:
            self.stdout.write(self.style.WARNING('Usa --confirmar para eliminar. Solo simulación:'))
        
        eliminados = 0
        
        if tipo in ['usuarios', 'todo']:
            # No eliminar superusers ni staff
            users = User.objects.filter(is_superuser=False, is_staff=False)
            if limite:
                users = users[:limite]
            count = users.count()
            if count > 0:
                if confirmar:
                    users.delete()
                eliminados += count
                self.stdout.write(self.style.SUCCESS(f'[X] {count} usuarios eliminados (simulación)'))
            else:
                self.stdout.write(self.style.WARNING('[-] No hay usuarios para eliminar'))
        
        if tipo in ['productos', 'todo']:
            productos = Producto.objects.all()
            if limite:
                productos = productos[:limite]
            count = productos.count()
            if count > 0:
                if confirmar:
                    productos.delete()
                eliminados += count
                self.stdout.write(self.style.SUCCESS(f'[X] {count} productos eliminados (simulación)'))
            else:
                self.stdout.write(self.style.WARNING('[-] No hay productos para eliminar'))
        
        if tipo in ['planes', 'todo']:
            planes = Plan.objects.all()
            if limite:
                planes = planes[:limite]
            count = planes.count()
            if count > 0:
                if confirmar:
                    planes.delete()
                eliminados += count
                self.stdout.write(self.style.SUCCESS(f'[X] {count} planes eliminados (simulación)'))
            else:
                self.stdout.write(self.style.WARNING('[-] No hay planes para eliminar'))
        
        if tipo in ['proveedores', 'todo']:
            proveedores = Proveedor.objects.all()
            if limite:
                proveedores = proveedores[:limite]
            count = proveedores.count()
            if count > 0:
                if confirmar:
                    proveedores.delete()
                eliminados += count
                self.stdout.write(self.style.SUCCESS(f'[X] {count} proveedores eliminados (simulación)'))
            else:
                self.stdout.write(self.style.WARNING('[-] No hay proveedores para eliminar'))
        
        if tipo in ['maquinaria', 'todo']:
            maquinaria = Maquinaria.objects.all()
            if limite:
                maquinaria = maquinaria[:limite]
            count = maquinaria.count()
            if count > 0:
                if confirmar:
                    maquinaria.delete()
                eliminados += count
                self.stdout.write(self.style.SUCCESS(f'[X] {count} maquinaria eliminada (simulación)'))
            else:
                self.stdout.write(self.style.WARNING('[-] No hay maquinaria para eliminar'))
        
        if confirmar:
            self.stdout.write(self.style.SUCCESS(f'OK Eliminacion completada: {eliminados} registros'))
        else:
            self.stdout.write(self.style.WARNING(f'Total a eliminar: {eliminados}. Ejecuta con --confirmar para eliminar de verdad'))
