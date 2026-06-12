from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Rutina, Ejercicio


class Command(BaseCommand):
    help = 'Mejora las rutinas del sistema con ejercicios más completos y profesionales'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('MEJORANDO RUTINAS DEL SISTEMA')
        self.stdout.write('='*60)
        
        admin_user = User.objects.filter(is_superuser=True).first()
        
        rutinas_mejoradas = {
            'Bajar de Peso - 1 Mes': {
                'descripcion': 'Rutina intensiva para quema de grasa. Combina HIIT, cardio y ejercicios compuestos para maximizar la pérdida de peso.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Press de banca', '4 series', '10 repeticiones', '60s'),
                    ('lunes', 'Sentadillas con peso', '4 series', '12 repeticiones', '90s'),
                    ('lunes', 'Peso muerto rumano', '3 series', '10 repeticiones', '90s'),
                    ('lunes', 'Flexiones', '3 series', '12-15 repeticiones', '60s'),
                    ('lunes', 'Plancha', '3 series', '30 segundos', '45s'),
                    ('martes', 'Burpees', '4 series', '15 repeticiones', '60s'),
                    ('martes', 'Saltos al cajón', '4 series', '12 repeticiones', '60s'),
                    ('martes', 'Mountain climbers', '3 series', '30 segundos', '45s'),
                    ('martes', 'Cardio bicicleta', '1 serie', '20 minutos', '0s'),
                    ('martes', 'Abdominales crunch', '4 series', '20 repeticiones', '45s'),
                    ('miercoles', 'Descanso activo', 'Estiramientos', '15 minutos', '0s'),
                    ('jueves', 'Press militar', '4 series', '10 repeticiones', '60s'),
                    ('jueves', 'Elevaciones laterales', '3 series', '15 repeticiones', '45s'),
                    ('jueves', 'Remo con mancuerna', '4 series', '12 repeticiones', '60s'),
                    ('jueves', 'Curl de bíceps', '3 series', '12 repeticiones', '45s'),
                    ('jueves', 'Tríceps en polea', '3 series', '12 repeticiones', '45s'),
                    ('viernes', 'Sentadillas跳跃', '4 series', '15 repeticiones', '60s'),
                    ('viernes', 'Zancadas', '3 series', '12 cada pierna', '60s'),
                    ('viernes', 'Peso muerto', '4 series', '8 repeticiones', '90s'),
                    ('viernes', 'Elevaciones de talones', '3 series', '15 repeticiones', '45s'),
                    ('viernes', 'Cardio cinta', '1 serie', '25 minutos', '0s'),
                    ('sabado', 'HIIT completo', 'Circuitos', '30 minutos', '0s'),
                    ('sabado', 'Saltos de tijera', '4 series', '30 segundos', '30s'),
                    ('sabado', 'Burpees explosives', '4 series', '15 repeticiones', '45s'),
                    ('sabado', 'Battle ropes', '3 series', '30 segundos', '45s'),
                    ('domingo', 'Descanso', 'Stretching completo', '20 minutos', '0s'),
                ]
            },
            'Subir Masa - 1 Mes': {
                'descripcion': 'Rutina de fuerza e hypertrophy para ganar masa muscular. Ejercicios compounds e isolados para máximo crecimiento.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Press de banca', '4 series', '8-10 repeticiones', '90s'),
                    ('lunes', 'Press inclinado', '4 series', '8-10 repeticiones', '90s'),
                    ('lunes', 'Elevaciones laterales', '4 series', '12-15 repeticiones', '60s'),
                    ('lunes', 'Aperturas con mancuernas', '3 series', '12 repeticiones', '60s'),
                    ('lunes', 'Tríceps en barra', '3 series', '10 repeticiones', '60s'),
                    ('martes', 'Dominadas', '4 series', '8-12 repeticiones', '90s'),
                    ('martes', 'Remo curvado', '4 series', '10 repeticiones', '75s'),
                    ('martes', 'Remo en máquina', '3 series', '12 repeticiones', '60s'),
                    ('martes', 'Curl de bíceps barra', '4 series', '10 repeticiones', '60s'),
                    ('martes', 'Curl martillo', '3 series', '12 repeticiones', '45s'),
                    ('miercoles', 'Sentadillas', '4 series', '8-10 repeticiones', '120s'),
                    ('miercoles', 'Prensa de piernas', '4 series', '10-12 repeticiones', '90s'),
                    ('miercoles', 'Hack squat', '3 series', '12 repeticiones', '90s'),
                    ('miercoles', 'Extensiones de cuádriceps', '3 series', '15 repeticiones', '60s'),
                    ('miercoles', 'Curl de isquiotibiales', '3 series', '12 repeticiones', '60s'),
                    ('jueves', 'Press militar', '4 series', '8-10 repeticiones', '90s'),
                    ('jueves', 'Elevaciones frontales', '3 series', '12-15 repeticiones', '60s'),
                    ('jueves', 'Face pulls', '4 series', '15 repeticiones', '60s'),
                    ('jueves', 'Abductores', '3 series', '15 repeticiones', '60s'),
                    ('jueves', 'Crunch en máquina', '4 series', '15 repeticiones', '45s'),
                    ('viernes', 'Peso muerto convencional', '4 series', '6-8 repeticiones', '120s'),
                    ('viernes', 'Stiff', '3 series', '10 repeticiones', '90s'),
                    ('viernes', 'Jalas al pecho', '4 series', '10 repeticiones', '75s'),
                    ('viernes', 'Curl de antebrazo', '3 series', '15 repeticiones', '45s'),
                    ('viernes', 'Plancha lateral', '3 series', '30 segundos', '30s'),
                    ('sabado', 'Full body ligero', '3 series', '10-12 repeticiones', '60s'),
                    ('domingo', 'Descanso', 'Stretching y recuperación', '30 minutos', '0s'),
                ]
            },
            'Mantener Peso - 1 Mes': {
                'descripcion': 'Rutina equilibrada para mantener condición física. Combina fuerza, cardio y flexibilidad.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Press de banca', '3 series', '10-12 repeticiones', '75s'),
                    ('lunes', 'Filas horizontales', '3 series', '12 repeticiones', '60s'),
                    ('lunes', 'Press overhead', '3 series', '12 repeticiones', '60s'),
                    ('lunes', 'Curl bíceps', '3 series', '12 repeticiones', '45s'),
                    ('martes', 'Sentadillas', '3 series', '12 repeticiones', '90s'),
                    ('martes', 'Peso muerto', '3 series', '10 repeticiones', '90s'),
                    ('martes', 'Zancadas', '3 series', '10 cada pierna', '60s'),
                    ('martes', 'Elevaciones de talones', '3 series', '15 repeticiones', '45s'),
                    ('miercoles', 'Cardio intervalos', 'Caminata rápida', '25 minutos', '0s'),
                    ('miercoles', 'Abdominales', '4 series', '15 repeticiones', '45s'),
                    ('miercoles', 'Escaladora', '3 series', '20 segundos', '30s'),
                    ('jueves', 'Pull ups', '3 series', '8-10 repeticiones', '90s'),
                    ('jueves', 'Press máquinas', '3 series', '12 repeticiones', '60s'),
                    ('jueves', 'Aperturas', '3 series', '12 repeticiones', '60s'),
                    ('jueves', 'Tríceps', '3 series', '12 repeticiones', '45s'),
                    ('viernes', 'Piernas-press', '3 series', '12 repeticiones', '90s'),
                    ('viernes', 'Piernas-extensiones', '3 series', '15 repeticiones', '60s'),
                    ('viernes', 'Curl piernas', '3 series', '15 repeticiones', '60s'),
                    ('viernes', 'Plancha', '3 series', '45 segundos', '30s'),
                    ('viernes', 'Cardio elíptico', '1 serie', '20 minutos', '0s'),
                    ('sabado', 'HIIT suave', 'Circuitos', '20 minutos', '0s'),
                    ('sabado', 'Stretching', 'Yoga', '30 minutos', '0s'),
                    ('domingo', 'Actividad ligera', 'Caminata o bicicleta', '45 minutos', '0s'),
                ]
            },
            'Definir Musculatura - 1 Mes': {
                'descripcion': 'Rutina de definición muscular con volumen moderado y cardio para revelar los músculos.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Press de banca', '4 series', '10-12 repeticiones', '60s'),
                    ('lunes', 'Press inclinado', '3 series', '12 repeticiones', '60s'),
                    ('lunes', 'Remo握住', '4 series', '12 repeticiones', '60s'),
                    ('lunes', 'Face pulls', '3 series', '15 repeticiones', '45s'),
                    ('lunes', 'Dip tríceps', '3 series', '12 repeticiones', '45s'),
                    ('martes', 'Sentadillas', '4 series', '12 repeticiones', '75s'),
                    ('martes', 'Prensa', '3 series', '15 repeticiones', '60s'),
                    ('martes', 'Peso muerto rumano', '3 series', '12 repeticiones', '75s'),
                    ('martes', 'Curl femoral', '3 series', '15 repeticiones', '45s'),
                    ('martes', 'Abdominales crunch', '4 series', '20 repeticiones', '45s'),
                    ('miercoles', 'HIIT', 'Circuitos', '25 minutos', '0s'),
                    ('miercoles', 'Mountain climbers', '4 series', '30 segundos', '30s'),
                    ('miercoles', 'Burpees', '4 series', '15 repeticiones', '45s'),
                    ('miercoles', 'Saltos al cajón', '3 series', '12 repeticiones', '60s'),
                    ('jueves', 'Press militar', '4 series', '10 repeticiones', '60s'),
                    ('jueves', 'Elevaciones laterales', '4 series', '15 repeticiones', '45s'),
                    ('jueves', 'Remo mancuerna', '4 series', '12 repeticiones', '60s'),
                    ('jueves', 'Curl bíceps', '3 series', '12 repeticiones', '45s'),
                    ('jueves', 'Tríceps patada', '3 series', '12 repeticiones', '45s'),
                    ('viernes', 'Peso muerto', '3 series', '10 repeticiones', '90s'),
                    ('viernes', 'Stiff', '3 series', '12 repeticiones', '60s'),
                    ('viernes', 'Jalas al pecho', '3 series', '12 repeticiones', '60s'),
                    ('viernes', 'Plancha', '3 series', '45 segundos', '30s'),
                    ('viernes', 'Abdominales bicicleta', '4 series', '20 repeticiones', '45s'),
                    ('sabado', 'Cardio', 'Trote continuo', '30 minutos', '0s'),
                    ('sabado', 'Abdominales inferiores', '3 series', '15 repeticiones', '45s'),
                    ('domingo', 'Descanso activo', 'Estiramientos', '20 minutos', '0s'),
                ]
            },
            'Cardio y Resistencia - 1 Mes': {
                'descripcion': 'Rutina enfocada en mejorar la capacidad cardiovascular y resistencia aeróbica.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Trote cinta', '1 serie', '25 minutos', '0s'),
                    ('lunes', 'Burpees', '5 series', '20 repeticiones', '45s'),
                    ('lunes', 'Saltos de comba', '5 series', '30 segundos', '30s'),
                    ('martes', 'Bicicleta estática', '1 serie', '30 minutos', '0s'),
                    ('martes', 'Mountain climbers', '4 series', '30 segundos', '30s'),
                    ('martes', 'Jumping jacks', '4 series', '40 repeticiones', '30s'),
                    ('miercoles', 'Natación/Hidrogimnasia', '1 serie', '30 minutos', '0s'),
                    ('miercoles', 'Abdominales bicicleta', '4 series', '25 repeticiones', '45s'),
                    ('miercoles', 'Escaladora', '4 series', '30 segundos', '30s'),
                    ('jueves', 'Trote intervalos', '1 serie', '25 minutos', '0s'),
                    ('jueves', 'Burpees', '4 series', '15 repeticiones', '45s'),
                    ('jueves', 'Saltos al cajón', '4 series', '15 repeticiones', '60s'),
                    ('viernes', 'Elíptico', '1 serie', '30 minutos', '0s'),
                    ('viernes', 'Battle ropes', '4 series', '30 segundos', '45s'),
                    ('viernes', 'Kettlebell swings', '4 series', '20 repeticiones', '45s'),
                    ('sabado', 'Carrera larga', '1 serie', '45 minutos', '0s'),
                    ('sabado', 'Estiramientos dinámicos', '1 serie', '15 minutos', '0s'),
                    ('domingo', 'Caminata activa', '1 serie', '40 minutos', '0s'),
                    ('domingo', 'Yoga cardiovascular', '1 serie', '30 minutos', '0s'),
                ]
            },
            'Subir Masa y Perder Grasa - 1 Mes': {
                'descripcion': 'Rutina híbrida que combina fuerza y cardio para ganar músculo mientras se quema grasa.',
                'nivel': 'principiante',
                'duracion_dias': 30,
                'ejercicios': [
                    ('lunes', 'Press banca + Cardio', '4 series + 10 min', '8-10 reps + HIIT', '90s'),
                    ('lunes', 'Sentadillas', '4 series', '10-12 repeticiones', '90s'),
                    ('lunes', 'Remo', '3 series', '12 repeticiones', '60s'),
                    ('lunes', 'Curl bíceps', '3 series', '12 repeticiones', '45s'),
                    ('martes', 'HIIT', 'Circuitos', '20 minutos', '0s'),
                    ('martes', 'Mountain climbers', '4 series', '30 segundos', '30s'),
                    ('martes', 'Burpees', '4 series', '15 repeticiones', '45s'),
                    ('martes', 'Saltos de comba', '4 series', '30 segundos', '30s'),
                    ('miercoles', 'Press militar', '4 series', '8-10 repeticiones', '75s'),
                    ('miercoles', 'Peso muerto', '4 series', '8 repeticiones', '90s'),
                    ('miercoles', 'Dominadas', '3 series', '10 repeticiones', '75s'),
                    ('miercoles', 'Tríceps', '3 series', '12 repeticiones', '45s'),
                    ('jueves', 'Cardio intervalos', '1 serie', '25 minutos', '0s'),
                    ('jueves', 'Zancadas', '3 series', '12 cada pierna', '60s'),
                    ('jueves', 'Step ups', '3 series', '15 cada pierna', '45s'),
                    ('viernes', 'Press banca', '4 series', '8 repeticiones', '75s'),
                    ('viernes', 'Remo', '4 series', '10 repeticiones', '60s'),
                    ('viernes', 'Curl martillo', '3 series', '12 repeticiones', '45s'),
                    ('viernes', 'Plancha', '3 series', '45 segundos', '30s'),
                    ('sabado', 'HIIT intenso', 'Circuitos', '30 minutos', '0s'),
                    ('sabado', 'Battle ropes', '4 series', '30 segundos', '45s'),
                    ('sabado', 'Abdominales', '4 series', '20 repeticiones', '45s'),
                    ('domingo', 'Descanso activo', 'Estiramientos', '30 minutos', '0s'),
                ]
            },
        }
        
        stats = {'actualizadas': 0, 'ejercicios': 0}
        
        for nombre_rutina, data in rutinas_mejoradas.items():
            try:
                rutina = Rutina.objects.get(nombre=nombre_rutina)
                
                rutina.descripcion = data['descripcion']
                rutina.nivel = data['nivel']
                rutina.duracion_dias = data['duracion_dias']
                rutina.save()
                
                rutina.ejercicios.all().delete()
                
                orden = 1
                for dia, nombre, series, reps, descanso in data['ejercicios']:
                    Ejercicio.objects.create(
                        rutina=rutina,
                        nombre=nombre,
                        descripcion=f'{series}, {reps}',
                        series=int(series.split()[0]) if series[0].isdigit() else 3,
                        repeticiones=reps,
                        descanso=int(descanso.replace('s', '').replace(' min', '').replace('Sec', '').replace('Seg', '')) if descanso != '0s' and 'min' not in descanso else 0,
                        dia=dia,
                        orden=orden,
                    )
                    orden += 1
                
                stats['actualizadas'] += 1
                stats['ejercicios'] += len(data['ejercicios'])
                self.stdout.write(f'[OK] {nombre_rutina}: {len(data["ejercicios"])} ejercicios')
                
            except Rutina.DoesNotExist:
                self.stdout.write(f'[WARN] No encontrada: {nombre_rutina}')
        
        self.stdout.write('='*60)
        self.stdout.write('RESUMEN')
        self.stdout.write('='*60)
        self.stdout.write(f'Rutinas actualizadas: {stats["actualizadas"]}')
        self.stdout.write(f'Ejerciciostotales: {stats["ejercicios"]}')
        self.stdout.write('Completado!')
