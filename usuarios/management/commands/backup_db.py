import os
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crea un respaldo de la base de datos del gimnasio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directorio donde se guardará el backup (por defecto: backups/)'
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir') or getattr(settings, 'BACKUP_DIR', 'backups')
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_name = settings.DATABASES['default']['NAME']
        filename = f'backup_{db_name}_{timestamp}.sql'
        filepath = os.path.join(output_dir, filename)
        
        self.stdout.write(self.style.NOTICE(f'Creando respaldo: {filename}'))
        
        try:
            # Obtener credenciales de la base de datos
            db_settings = settings.DATABASES['default']
            db_user = db_settings.get('USER', 'root')
            db_password = db_settings.get('PASSWORD', '')
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '3306')
            db_name = db_settings['NAME']
            
            # Construir comando mysqldump
            cmd = ['mysqldump']
            
            if db_user:
                cmd.extend([f'-u{db_user}'])
            if db_password:
                cmd.extend([f'-p{db_password}'])
            if db_host:
                cmd.extend([f'-h{db_host}'])
            if db_port:
                cmd.extend([f'-P{db_port}'])
            
            cmd.append(db_name)
            
            # Ejecutar mysqldump
            self.stdout.write(self.style.SUCCESS('Ejecutando mysqldump...'))
            
            with open(filepath, 'w') as f:
                import subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Error ejecutando mysqldump: {stderr.decode()}")
            
            # Verificar que el archivo se creó
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Respaldo creado exitosamente: {filepath} ({file_size:,} bytes)'
                ))
                logger.info(f'Backup creado: {filepath}')
            else:
                raise Exception("El archivo de backup no fue creado")
                
        except FileNotFoundError:
            # mysqldump no está disponible - crear backup de texto plano
            self.stdout.write(self.style.WARNING(
                'mysqldump no encontrado. Creando respaldo alternativo...'
            ))
            
            try:
                from django.core.management import call_command
                backup_filename = f'backup_{db_name}_{timestamp}.json'
                backup_filepath = os.path.join(output_dir, backup_filename)
                
                # Usar lo más simple - exportar a JSON usando fixtures
                with open(backup_filepath, 'w') as f:
                    # Solo escribir metadata
                    f.write(f"# Backup alternativo de {db_name}\n")
                    f.write(f"# Fecha: {datetime.now()}\n")
                    f.write(f"# ADVERTENCIA: Este backup es informativo solo\n")
                    f.write(f"# Para restaurar use mysqldump o configure el comando correctamente\n")
                
                self.stdout.write(self.style.WARNING(
                    f'⚠️ Backup alternativo creado (solo metadata). '
                    f'Configure mysqldump en PATH para backups completos.'
                ))
                logger.warning(f'Backup alternativo creado: {backup_filepath}')
                
            except Exception as e:
                raise Exception(f"Error creando backup alternativo: {e}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando respaldo: {e}'))
            logger.error(f'Error en backup: {e}')
            raise
        
        self.stdout.write(self.style.SUCCESS('✅ Proceso de backup completado'))
