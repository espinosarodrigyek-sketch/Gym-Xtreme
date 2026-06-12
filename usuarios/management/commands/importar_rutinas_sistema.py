from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Rutina, Ejercicio
import os


class Command(BaseCommand):
    help = 'Importa las rutinas del sistema desde los templates HTML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobreescribir rutinas existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write('='*50)
        self.stdout.write('IMPORTANDO RUTINAS DEL SISTEMA')
        self.stdout.write('='*50)
        
        from django.conf import settings
        base_path = os.path.join(settings.BASE_DIR, 'usuarios', 'templates', 'rutinas')
        
        rutinas_data = [
            {
                'nombre': 'Bajar de Peso - 1 Mes',
                'descripcion': 'Rutina enfocada en quema de grasa y definicion corporal. Incluye HIIT, cardio y ejercicios compuestos.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_bajar_peso.html',
            },
            {
                'nombre': 'Bajar de Peso - 6 Meses',
                'descripcion': 'Programa completo de 6 meses para perder grasa de manera sostenible.',
                'nivel': 'intermedio',
                'duracion_dias': 180,
                'template': 'rutina_6_meses_bajar_peso.html',
            },
            {
                'nombre': 'Bajar de Peso - 1 Ano',
                'descripcion': 'Transformacion completa de 1 ano para perder grasa y mantener resultados.',
                'nivel': 'avanzado',
                'duracion_dias': 365,
                'template': 'rutina_1_ano_bajar_peso.html',
            },
            {
                'nombre': 'Subir Masa - 1 Mes',
                'descripcion': 'Rutina para ganar masa muscular con ejercicios de fuerza.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_subir_masa.html',
            },
            {
                'nombre': 'Subir Masa - 6 Meses',
                'descripcion': 'Programa de 6 meses para aumentar masa muscular.',
                'nivel': 'intermedio',
                'duracion_dias': 180,
                'template': 'rutina_6_meses_subir_masa.html',
            },
            {
                'nombre': 'Subir Masa - 1 Ano',
                'descripcion': 'Programa completo de 1 ano para transformacion muscular.',
                'nivel': 'avanzado',
                'duracion_dias': 365,
                'template': 'rutina_1_ano_subir_masa.html',
            },
            {
                'nombre': 'Mantener Peso - 1 Mes',
                'descripcion': 'Rutina para mantener condicion fisica y salud.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_mantener.html',
            },
            {
                'nombre': 'Mantener Peso - 6 Meses',
                'descripcion': 'Programa de 6 meses para mantener peso y salud.',
                'nivel': 'intermedio',
                'duracion_dias': 180,
                'template': 'rutina_6_meses_mantener.html',
            },
            {
                'nombre': 'Mantener Peso - 1 Ano',
                'descripcion': 'Programa anual para mantener peso y bienestar.',
                'nivel': 'avanzado',
                'duracion_dias': 365,
                'template': 'rutina_1_ano_mantener.html',
            },
            {
                'nombre': 'Definir Musculatura - 1 Mes',
                'descripcion': 'Rutina para definir y tonificar musculatura.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_definir.html',
            },
            {
                'nombre': 'Cardio y Resistencia - 1 Mes',
                'descripcion': 'Rutina para mejorar resistencia cardiovascular.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_cardio.html',
            },
            {
                'nombre': 'Subir Masa y Perder Grasa - 1 Mes',
                'descripcion': 'Rutina combinada para ganar musculo y perder grasa.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'template': 'rutina_1_mes_subir_masa_perder_grasa.html',
            },
        ]
        
        admin_user = User.objects.filter(is_superuser=True).first()
        
        stats = {'creadas': 0, 'actualizadas': 0, 'ejercicios': 0, 'errores': 0}
        
        for data in rutinas_data:
            template_path = os.path.join(base_path, data['template'])
            
            if not os.path.exists(template_path):
                self.stdout.write('[WARN] No encontrado: ' + data['template'])
                continue
            
            try:
                rutina, created = Rutina.objects.get_or_create(
                    nombre=data['nombre'],
                    defaults={
                        'descripcion': data['descripcion'],
                        'nivel': data['nivel'],
                        'duracion_dias': data['duracion_dias'],
                        'creada_por': admin_user,
                        'activa': True,
                        'es_predeterminada': True,
                    }
                )
                
                if created:
                    stats['creadas'] += 1
                    self.stdout.write('[OK] Creada: ' + rutina.nombre)
                elif options['force']:
                    stats['actualizadas'] += 1
                    self.stdout.write('[UPD] Actualizada: ' + rutina.nombre)
                else:
                    self.stdout.write('[SKIP] Ya existe: ' + rutina.nombre)
                    continue
                
                self._importar_ejercicios(rutina, template_path, stats)
                
            except Exception as e:
                stats['errores'] += 1
                self.stdout.write('[ERROR] ' + data['nombre'] + ': ' + str(e))
        
        self.stdout.write('='*50)
        self.stdout.write('ESTADISTICAS')
        self.stdout.write('='*50)
        self.stdout.write('Rutinas creadas: ' + str(stats['creadas']))
        self.stdout.write('Rutinas actualizadas: ' + str(stats['actualizadas']))
        self.stdout.write('Ejercicios importados: ' + str(stats['ejercicios']))
        self.stdout.write('Errores: ' + str(stats['errores']))
    
    def _importar_ejercicios(self, rutina, template_path, stats):
        """Importa ejercicios desde el template HTML"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return
        
        with open(template_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        tablas = soup.find_all('table')
        
        dia_mapping = {
            'lunes': 'lunes', 'martes': 'martes', 'miercoles': 'miercoles',
            'jueves': 'jueves', 'viernes': 'viernes', 'sabado': 'sabado', 'domingo': 'domingo'
        }
        
        ejercicio_id = 1
        
        for tabla in tablas:
            filas = tabla.find_all('tr')
            if len(filas) < 2:
                continue
            
            headers = [th.get_text(strip=True).lower() for th in filas[0].find_all('th')]
            
            dia_idx = None
            for idx, header in enumerate(headers):
                if 'dia' in header:
                    dia_idx = idx
                    break
            
            for fila in filas[1:]:
                celdas = fila.find_all('td')
                if not celdas:
                    continue
                
                try:
                    if dia_idx is not None and dia_idx < len(celdas):
                        dia_texto = celdas[dia_idx].get_text(strip=True).lower()
                        dia_encontrado = None
                        for key in dia_mapping:
                            if key in dia_texto:
                                dia_encontrado = dia_mapping[key]
                                break
                        if dia_encontrado is None:
                            continue
                    else:
                        continue
                    
                    ejercicio_nombre = celdas[1].get_text(strip=True) if len(celdas) > 1 else 'Ejercicio'
                    duracion = celdas[2].get_text(strip=True) if len(celdas) > 2 else '30 min'
                    
                    series = 3
                    repeticiones = '10-12'
                    
                    if 'cardio' in ejercicio_nombre.lower() or 'descanso' in ejercicio_nombre.lower():
                        series = 1
                        repeticiones = duracion
                    
                    ejercicio, created = Ejercicio.objects.get_or_create(
                        rutina=rutina,
                        nombre=ejercicio_nombre,
                        dia=dia_encontrado,
                        defaults={
                            'descripcion': 'Duracion: ' + duracion,
                            'series': series,
                            'repeticiones': repeticiones,
                            'descanso': 60,
                            'orden': ejercicio_id,
                        }
                    )
                    
                    if created:
                        stats['ejercicios'] += 1
                    
                    ejercicio_id += 1
                    
                except Exception:
                    pass
