from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Rutina, Ejercicio
from django.conf import settings
import csv
import os


class Command(BaseCommand):
    help = 'Carga rutinas desde archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recarga sin preguntar',
        )

    def handle(self, *args, **options):
        # Usar BASE_DIR de Django
        csv_path = os.path.join(settings.BASE_DIR, 'csv_datos', 'rutinas.csv')
        
        self.stdout.write(f'📁 Buscando CSV en: {csv_path}')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'❌ No se encontró el archivo: {csv_path}'))
            return

        Rutina.objects.filter(es_predeterminada=True).delete()
        self.stdout.write(self.style.WARNING('🗑️ Rutinas anteriores eliminadas'))

        rutinas_data = {}
        dias_map = {
            'lunes': 'lunes',
            'martes': 'martes',
            'miercoles': 'miercoles',
            'jueves': 'jueves',
            'viernes': 'viernes',
            'sabado': 'sabado',
            'domingo': 'domingo'
        }
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            total_filas = 0
            for row in reader:
                total_filas += 1
                rutina_num = row.get('rutina', '').strip()
                dia = row.get('dia', '').strip().lower()
                
                if not rutina_num:
                    self.stdout.write(self.style.WARNING(f'⚠️ Fila sin rutina: {row}'))
                    continue
                
                if dia in dias_map:
                    dia = dias_map[dia]
                else:
                    dia = 'lunes'
                
                nombre_ejercicio = row.get('ejercicio', '').strip()
                if not nombre_ejercicio:
                    continue
                
                if rutina_num not in rutinas_data:
                    rutinas_data[rutina_num] = {
                        'nombre': f'Rutina {rutina_num} días',
                        'ejercicios': []
                    }
                
                try:
                    series = int(row.get('series', 4))
                except:
                    series = 4
                
                repeticiones = row.get('repeticiones', '10-12').strip()
                
                try:
                    descanso = int(row.get('descanso', 90))
                except:
                    descanso = 90
                
                ejercicios_count = len(rutinas_data[rutina_num]['ejercicios'])
                ejercicios_dict = {
                    'nombre': nombre_ejercicio,
                    'series': series,
                    'repeticiones': repeticiones,
                    'descanso': descanso,
                    'dia': dia,
                    'orden': ejercicios_count + 1
                }
                rutinas_data[rutina_num]['ejercicios'].append(ejercicios_dict)

        self.stdout.write(f'📊 Filas procesadas: {total_filas}')
        self.stdout.write(f'📊 Rutinas detectadas: {len(rutinas_data)}')

        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()

        total_rutinas = 0
        total_ejercicios = 0

        for rutina_num, data in sorted(rutinas_data.items()):
            self.stdout.write(f'➕ Creando {data["nombre"]} con {len(data["ejercicios"])} ejercicios...')
            
            rutina = Rutina.objects.create(
                nombre=data['nombre'],
                descripcion=f'Rutina predeterminada del sistema - {rutina_num} días/semana',
                nivel='intermedio',
                duracion_dias=7,
                activa=True,
                es_predeterminada=True,
                creada_por=admin_user
            )
            
            for ej in data['ejercicios']:
                Ejercicio.objects.create(
                    rutina=rutina,
                    nombre=ej['nombre'],
                    series=ej['series'],
                    repeticiones=ej['repeticiones'],
                    descanso=ej['descanso'],
                    dia=ej['dia'],
                    orden=ej['orden']
                )
                total_ejercicios += 1
            
            total_rutinas += 1
            self.stdout.write(self.style.SUCCESS(f'  ✓ {data["nombre"]}: {len(data["ejercicios"])} ejercicios'))

        self.stdout.write(self.style.SUCCESS(f'\n🎉 COMPLETADO: {total_rutinas} rutinas y {total_ejercicios} ejercicios cargados'))