from django.core.management.base import BaseCommand
from productos.models import AlertaLote


class Command(BaseCommand):
    help = 'Genera alertas automáticas para lotes próximos a vencer'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-critico',
            type=int,
            default=7,
            help='Días para considerar nivel crítico (default: 7)'
        )
        parser.add_argument(
            '--dias-alto',
            type=int,
            default=14,
            help='Días para considerar nivel alto (default: 14)'
        )
        parser.add_argument(
            '--dias-medio',
            type=int,
            default=30,
            help='Días para considerar nivel medio (default: 30)'
        )
    
    def handle(self, *args, **options):
        dias_critico = options['dias_critico']
        dias_alto = options['dias_alto']
        dias_medio = options['dias_medio']
        
        alertas_creadas = AlertaLote.generar_alertas_automaticas(
            dias_critico=dias_critico,
            dias_alto=dias_alto,
            dias_medio=dias_medio
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Se generaron {alertas_creadas} alertas automáticas'
            )
        )
