import os
from django.core.management.base import BaseCommand
from gym.csv_import import (
    importar_usuarios_desde_csv,
    importar_productos_desde_csv,
    importar_planes_desde_csv
)


class Command(BaseCommand):
    help = 'Carga datos masivamente desde archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuarios',
            type=str,
            help='Ruta al archivo CSV de usuarios'
        )
        parser.add_argument(
            '--productos',
            type=str,
            help='Ruta al archivo CSV de productos'
        )
        parser.add_argument(
            '--planes',
            type=str,
            help='Ruta al archivo CSV de planes'
        )
        parser.add_argument(
            '--todo',
            type=str,
            help='Ruta al directorio que contiene los archivos CSV'
        )

    def handle(self, *args, **options):
        base_path = options.get('todo', '')
        
        if base_path:
            usuarios_path = os.path.join(base_path, 'usuarios.csv')
            productos_path = os.path.join(base_path, 'productos.csv')
            planes_path = os.path.join(base_path, 'planes.csv')
            
            if os.path.exists(usuarios_path):
                cantidad = importar_usuarios_desde_csv(usuarios_path)
                self.stdout.write(f'Se importaron {cantidad} usuarios')
                
            if os.path.exists(productos_path):
                cantidad = importar_productos_desde_csv(productos_path)
                self.stdout.write(f'Se importaron {cantidad} productos')
                
            if os.path.exists(planes_path):
                cantidad = importar_planes_desde_csv(planes_path)
                self.stdout.write(f'Se importaron {cantidad} planes')
        else:
            if options.get('usuarios'):
                cantidad = importar_usuarios_desde_csv(options['usuarios'])
                self.stdout.write(f'Se importaron {cantidad} usuarios')
                
            if options.get('productos'):
                cantidad = importar_productos_desde_csv(options['productos'])
                self.stdout.write(f'Se importaron {cantidad} productos')
                
            if options.get('planes'):
                cantidad = importar_planes_desde_csv(options['planes'])
                self.stdout.write(f'Se importaron {cantidad} planes')
                
        self.stdout.write(self.style.SUCCESS('Carga masiva completada'))