from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Rutina, Ejercicio


class Command(BaseCommand):
    help = 'Agrega ejercicios a las rutinas del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Agregando ejercicios...')
        
        ejercicios_data = {
            'Bajar de Peso - 1 Mes': [
                ('lunes', 'Cardio + Core', '45 min', 1, '10-15 min'),
                ('martes', 'Full Body (Ligero)', '40 min', 3, '12'),
                ('miercoles', 'Cardio Intervalado', '30 min', 1, '20 seg'),
                ('jueves', 'Descanso Activo', '20 min', 1, '-'),
                ('viernes', 'Circuit Training', '45 min', 3, '45 seg'),
                ('sabado', 'Cardio Largo', '50 min', 1, '25 min'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
            'Subir Masa - 1 Mes': [
                ('lunes', 'Pecho + Triceps', '45 min', 4, '8-12'),
                ('martes', 'Espalda + Biceps', '45 min', 4, '8-12'),
                ('miercoles', 'Piernas', '50 min', 4, '8-12'),
                ('jueves', 'Descanso', '-', 1, '-'),
                ('viernes', 'Hombros + Abdominales', '40 min', 3, '10-15'),
                ('sabado', 'Full Body', '45 min', 3, '12'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
            'Mantener Peso - 1 Mes': [
                ('lunes', 'Entrenamiento Mixto', '40 min', 3, '12'),
                ('martes', 'Cardio Ligero', '30 min', 1, '20 min'),
                ('miercoles', 'Fuerza General', '40 min', 3, '12'),
                ('jueves', 'Descanso Activo', '25 min', 1, '15 min'),
                ('viernes', 'Entrenamiento Mixto', '40 min', 3, '12'),
                ('sabado', 'Cardio', '35 min', 1, '25 min'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
            'Definir Musculatura - 1 Mes': [
                ('lunes', 'Hipertrofia Alta', '45 min', 4, '10-12'),
                ('martes', 'Cardio + Core', '35 min', 3, '20 seg'),
                ('miercoles', 'Hipertrofia', '45 min', 4, '10-12'),
                ('jueves', 'Descanso Activo', '20 min', 1, '10 min'),
                ('viernes', 'Hipertrofia', '45 min', 4, '10-12'),
                ('sabado', 'Cardio Intenso', '30 min', 1, '30 seg'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
            'Cardio y Resistencia - 1 Mes': [
                ('lunes', 'Cardio Intenso', '45 min', 1, '30 min'),
                ('martes', 'Entrenamiento de Resistencia', '40 min', 3, '15'),
                ('miercoles', 'Cardio Moderado', '35 min', 1, '25 min'),
                ('jueves', 'Entrenamiento de Resistencia', '40 min', 3, '15'),
                ('viernes', 'Cardio Intenso', '45 min', 1, '35 min'),
                ('sabado', 'Largo Distancia', '60 min', 1, '45 min'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
            'Subir Masa y Perder Grasa - 1 Mes': [
                ('lunes', 'Fuerza + Cardio', '50 min', 4, '10'),
                ('martes', 'Fuerza + Cardio', '50 min', 4, '10'),
                ('miercoles', 'HIIT', '25 min', 1, '30 seg'),
                ('jueves', 'Descanso Activo', '20 min', 1, '10 min'),
                ('viernes', 'Fuerza + Cardio', '50 min', 4, '10'),
                ('sabado', 'Cardio', '40 min', 1, '25 min'),
                ('domingo', 'Descanso', '-', 1, '-'),
            ],
        }
        
        for rutina_nombre, ejercicios in ejercicios_data.items():
            try:
                rutina = Rutina.objects.get(nombre=rutina_nombre)
                rutina.ejercicios.all().delete()
                
                orden = 1
                for dia, nombre, duracion, series, reps in ejercicios:
                    Ejercicio.objects.create(
                        rutina=rutina,
                        nombre=nombre,
                        descripcion='Duracion: ' + duracion,
                        series=series,
                        repeticiones=reps,
                        descanso=60,
                        dia=dia,
                        orden=orden,
                    )
                    orden += 1
                
                self.stdout.write('[OK] ' + rutina_nombre)
            except Rutina.DoesNotExist:
                self.stdout.write('[WARN] No encontrada: ' + rutina_nombre)
        
        self.stdout.write('Done!')
        self.stdout.write('Total ejercicios: ' + str(Ejercicio.objects.count()))
