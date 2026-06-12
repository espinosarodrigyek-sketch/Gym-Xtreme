import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from usuarios.models import Perfil, Suscripcion, Venta
from productos.models import Producto, Categoria
from planes.models import Plan
from proveedores.models import Proveedor
from maquinaria.models import Maquinaria
from compras.models import Compra, DetalleCompra


class Command(BaseCommand):
    help = 'Carga datos masivamente desde archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--todo',
            type=str,
            help='Ruta al directorio que contiene los archivos CSV'
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Límite de registros a importar (sin límite por defecto)'
        )

    def safe_strip(self, val):
        """Safe string strip que maneja None/empty."""
        return val.strip() if val else ''

    def safe_float(self, val):
        """Safe float conversion."""
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def safe_int(self, val):
        """Safe int conversion."""
        try:
            return int(val) if val else 0
        except (ValueError, TypeError):
            return 0

    def handle(self, *args, **options):
        base_path = options.get('todo', '')
        limite = options.get('limite')
        
        if not base_path:
            self.stdout.write(self.style.ERROR('Debe especificar --todo con la ruta al directorio'))
            return
            
        total_importados = 0
        
        # ==========================================
        # USUARIOS
        # ==========================================
        usuarios_path = os.path.join(base_path, 'usuarios.csv')
        if os.path.exists(usuarios_path):
            cantidad = 0
            contador = 0
            with open(usuarios_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    username = row.get('username', '').strip()
                    email = row.get('email', '').strip()
                    password = row.get('password', 'password123')
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    rol = row.get('rol', 'cliente').strip()
                    telefono = row.get('telefono', '').strip()
                    direccion = row.get('direccion', '').strip()
                    
                    if not username:
                        continue
                    if User.objects.filter(username=username).exists():
                        try:
                            user = User.objects.get(username=username)
                            try:
                                perfil = Perfil.objects.get(user=user)
                                perfil.rol = rol
                                perfil.telefono = telefono
                                perfil.direccion = direccion
                                perfil.save()
                            except Perfil.DoesNotExist:
                                Perfil.objects.create(
                                    user=user,
                                    rol=rol,
                                    telefono=telefono,
                                    direccion=direccion
                                )
                            cantidad += 1
                            contador += 1
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'[W] Error actualizando usuario {username}: {e}'))
                        continue
                        
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    
                    # El signal ya crea el perfil automáticamente, solo actualizamos
                    try:
                        perfil = Perfil.objects.get(user=user)
                        perfil.rol = rol
                        perfil.telefono = telefono
                        perfil.direccion = direccion
                        perfil.save()
                    except Perfil.DoesNotExist:
                        Perfil.objects.create(
                            user=user,
                            rol=rol,
                            telefono=telefono,
                            direccion=direccion
                        )
                    cantidad += 1
                    contador += 1
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Usuarios importados'))
            total_importados += cantidad
            
        # ==========================================
        # PRODUCTOS
        # ==========================================
        productos_path = os.path.join(base_path, 'productos.csv')
        if os.path.exists(productos_path):
            cantidad = 0
            contador = 0
            with open(productos_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    nombre = row.get('nombre', '').strip()
                    descripcion = row.get('descripcion', '').strip()
                    categoria = self.safe_strip(row.get('categoria'))
                    precio_costo = row.get('precio_costo', '0')
                    precio_venta = row.get('precio_venta', '0')
                    stock_actual = row.get('stock_actual', '0')
                    estado = row.get('estado', 'activo').strip()
                    imagen_nombre = row.get('imagen', '').strip()
                    
                    if not nombre:
                        continue
                    if Producto.objects.filter(nombre=nombre).exists():
                        continue
                    
                    try:
                        # Convertir categoria string a objeto
                        categoria_obj, _ = Categoria.objects.get_or_create(nombre=categoria)
                        
                        producto = Producto(
                            nombre=nombre,
                            descripcion=descripcion,
                            categoria=categoria_obj,
                            precio_costo=self.safe_float(row.get('precio_costo')),
                            precio_venta=self.safe_float(row.get('precio_venta')),
                            stock_actual=self.safe_int(row.get('stock_actual')),
                            estado=estado
                        )
                        
                        # Si hay nombre de imagen, buscar en media/productos
                        if imagen_nombre:
                            ruta_imagen = os.path.join(settings.MEDIA_ROOT, 'productos', imagen_nombre)
                            if os.path.exists(ruta_imagen):
                                from django.core.files.images import ImageFile
                                with open(ruta_imagen, 'rb') as f:
                                    producto.imagen.save(imagen_nombre, ImageFile(f), save=True)
                            else:
                                self.stdout.write(self.style.WARNING(f"[W] Imagen no encontrada: {imagen_nombre}"))
                        
                        producto.save()
                        cantidad += 1
                        contador += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"[W] Error con producto {nombre}: {e}"))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Productos importados'))
            total_importados += cantidad
            
        # ==========================================
        # PLANES
        # ==========================================
        planes_path = os.path.join(base_path, 'planes.csv')
        if os.path.exists(planes_path):
            cantidad = 0
            contador = 0
            with open(planes_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    nombre = row.get('nombre', '').strip()
                    tipo = row.get('tipo', '1_mes').strip()
                    precio = row.get('precio', '0')
                    descripcion = row.get('descripcion', '').strip()
                    duracion_dias = row.get('duracion_dias', '30')
                    imagen_nombre = row.get('imagen', '').strip()
                    
                    if not nombre:
                        continue
                    if Plan.objects.filter(nombre=nombre).exists():
                        continue
                    
                    try:
                        plan = Plan(
                            nombre=nombre,
                            tipo=tipo,
                            precio=self.safe_float(row.get('precio')),
                            descripcion=descripcion,
                            duracion_dias=self.safe_int(row.get('duracion_dias'))
                        )
                        
                        if imagen_nombre:
                            plan.imagen = 'planes/' + imagen_nombre
                        
                        plan.save()
                        cantidad += 1
                        contador += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error con plan {nombre}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Planes importados'))
            total_importados += cantidad
            
        # ==========================================
        # PROVEEDORES
        # ==========================================
        proveedores_path = os.path.join(base_path, 'proveedores.csv')
        if os.path.exists(proveedores_path):
            cantidad = 0
            contador = 0
            with open(proveedores_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    nombre = row.get('nombre', '').strip()
                    telefono = row.get('telefono', '').strip()
                    email = row.get('email', '').strip()
                    direccion = row.get('direccion', '').strip()
                    ciudad = row.get('ciudad', '').strip()
                    estado = row.get('estado', 'activo').strip()
                    
                    if not nombre:
                        continue
                    if Proveedor.objects.filter(nombre=nombre).exists():
                        continue
                    
                    try:
                        proveedor = Proveedor(
                            nombre=nombre,
                            telefono=telefono,
                            email=email,
                            direccion=direccion,
                            ciudad=ciudad,
                            estado=estado
                        )
                        proveedor.save()
                        cantidad += 1
                        contador += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error con proveedor {nombre}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Proveedores importados'))
            total_importados += cantidad
            
        # ==========================================
        # PROVEEDORES - PRODUCTOS (Relación)
        # ==========================================
        proveedores_productos_path = os.path.join(base_path, 'proveedores_productos.csv')
        if os.path.exists(proveedores_productos_path):
            cantidad = 0
            contador = 0
            with open(proveedores_productos_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    proveedor_nombre = row.get('proveedor', '').strip()
                    producto_nombre = row.get('producto', '').strip()
                    
                    if not proveedor_nombre or not producto_nombre:
                        continue
                    
                    try:
                        proveedor = Proveedor.objects.filter(nombre__iexact=proveedor_nombre).first()
                        producto = Producto.objects.filter(nombre__iexact=producto_nombre).first()
                        
                        if proveedor and producto:
                            proveedor.productos.add(producto)
                            cantidad += 1
                        contador += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error ligando {producto_nombre} a {proveedor_nombre}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[X] Se ligaron {cantidad} productos a proveedores'))
            total_importados += cantidad
            
        # ==========================================
        # MAQUINARIA
        # ==========================================
        maquinaria_path = os.path.join(base_path, 'maquinaria.csv')
        if os.path.exists(maquinaria_path):
            cantidad = 0
            contador = 0
            with open(maquinaria_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if limite and contador >= limite:
                        break
                    nombre = row.get('nombre', '').strip()
                    descripcion = row.get('descripcion', '').strip()
                    tipo = row.get('tipo', 'otro').strip()
                    ubicacion = row.get('ubicacion', '').strip()
                    estado = row.get('estado', 'activo').strip()
                    precio_compra = row.get('precio_compra', '')
                    fecha_compra = row.get('fecha_compra', '')
                    imagen_nombre = row.get('imagen', '').strip()
                    
                    if not nombre:
                        continue
                    if Maquinaria.objects.filter(nombre=nombre).exists():
                        continue
                    
                    try:
                        maquinaria = Maquinaria(
                            nombre=nombre,
                            descripcion=descripcion,
                            tipo=tipo,
                            ubicacion=ubicacion,
                            estado=estado,
                            precio_compra=float(precio_compra) if precio_compra else None,
                            fecha_compra=fecha_compra or None
                        )
                        
                        # Si hay nombre de imagen, buscar en media/maquinaria
                        if imagen_nombre:
                            ruta_imagen = os.path.join(settings.MEDIA_ROOT, 'maquinaria', imagen_nombre)
                            if os.path.exists(ruta_imagen):
                                from django.core.files.images import ImageFile
                                with open(ruta_imagen, 'rb') as f:
                                    maquinaria.imagen.save(imagen_nombre, ImageFile(f), save=True)
                            else:
                                self.stdout.write(self.style.WARNING(f"[W] Imagen no encontrada: {imagen_nombre}"))
                        
                        maquinaria.save()
                        cantidad += 1
                        contador += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error con maquinaria {nombre}: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[X] Se importaron {cantidad} equipos de maquinaria'))
            total_importados += cantidad

        # ==========================================
        # MAQUINARIA - ACTUALIZAR PROVEEDOR
        # ==========================================
        maquinaria_proveedor_path = os.path.join(base_path, 'maquinaria_proveedor.csv')
        if os.path.exists(maquinaria_proveedor_path):
            cantidad = 0
            with open(maquinaria_proveedor_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    nombre_maquina = row.get('nombre_maquina', '').strip()
                    nombre_proveedor = row.get('nombre_proveedor', '').strip()
                    precio_venta = row.get('precio_venta', '').strip()

                    if not nombre_maquina or not nombre_proveedor:
                        continue

                    try:
                        maquina = Maquinaria.objects.get(nombre=nombre_maquina)
                        proveedor = Proveedor.objects.get(nombre=nombre_proveedor)
                        maquina.proveedor = proveedor
                        if precio_venta:
                            maquina.precio_venta = float(precio_venta)
                        maquina.save()
                        cantidad += 1
                    except Maquinaria.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Maquinaria no encontrada: {nombre_maquina}'))
                    except Proveedor.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Proveedor no encontrado: {nombre_proveedor}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Maquinaria Actualizada con Proveedor'))
            total_importados += cantidad

        # ==========================================
        # PRODUCTOS - VINCULAR A MAQUINARIA
        # ==========================================
        productos_maquina_path = os.path.join(base_path, 'productos_maquina.csv')
        if os.path.exists(productos_maquina_path):
            cantidad = 0
            with open(productos_maquina_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    nombre_producto = row.get('nombre_producto', '').strip()
                    nombre_maquina = row.get('nombre_maquina', '').strip()

                    if not nombre_producto or not nombre_maquina:
                        continue

                    try:
                        producto = Producto.objects.get(nombre=nombre_producto)
                        maquina = Maquinaria.objects.get(nombre=nombre_maquina)
                        producto.tiene_maquina = True
                        producto.maquina_id = maquina.id_maquina
                        producto.save()
                        cantidad += 1
                    except Producto.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Producto no encontrado: {nombre_producto}'))
                    except Maquinaria.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Maquinaria no encontrada: {nombre_maquina}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Productos Vinculados a Maquinaria'))
            total_importados += cantidad

        # ==========================================
        # COMPRAS (COMPRAS A PROVEEDORES)
        # ==========================================
        compras_path = os.path.join(base_path, 'compras.csv')
        if os.path.exists(compras_path):
            cantidad = 0
            with open(compras_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    nombre_proveedor = row.get('proveedor', '').strip()
                    nombre_producto = row.get('producto', '').strip()
                    cantidad_prod = row.get('cantidad', '1').strip()
                    precio_unitario = row.get('precio_unitario', '0').strip()
                    fecha_str = row.get('fecha', '').strip()
                    estado = row.get('estado', 'confirmada').strip()
                    notas = row.get('notas', '').strip()

                    if not nombre_proveedor or not nombre_producto:
                        continue

                    try:
                        proveedor = Proveedor.objects.get(nombre=nombre_proveedor)
                        producto = Producto.objects.get(nombre=nombre_producto)

                        compra = Compra.objects.create(
                            proveedor=proveedor,
                            estado=estado,
                            notas=notas
                        )
                        if fecha_str:
                            try:
                                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                                compra.fecha = fecha
                                compra.save()
                            except:
                                pass

                        DetalleCompra.objects.create(
                            compra=compra,
                            producto=producto,
                            cantidad=self.safe_int(row.get('cantidad')),
                            precio_unitario=self.safe_float(row.get('precio_unitario'))
                        )

                        cantidad += 1
                    except Proveedor.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Proveedor no encontrado: {nombre_proveedor}'))
                    except Producto.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Producto no encontrado: {nombre_producto}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error en compra: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Compras importadas'))
            total_importados += cantidad

        # ==========================================
        # VENTAS (SUSCRIPCIONES A CLIENTES)
        # ==========================================
        ventas_path = os.path.join(base_path, 'ventas.csv')
        if os.path.exists(ventas_path):
            cantidad = 0
            with open(ventas_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    username = row.get('username', '').strip()
                    nombre_plan = row.get('plan', '').strip()
                    precio = row.get('precio', '0').strip()
                    fecha_str = row.get('fecha', '').strip()
                    dias_duracion = row.get('dias', '30').strip()

                    if not username or not nombre_plan:
                        continue

                    try:
                        user = User.objects.get(username=username)
                        plan = Plan.objects.get(nombre=nombre_plan)

                        from datetime import timedelta
                        from django.utils import timezone

                        fecha_inicio = timezone.now().date()
                        dias = int(dias_duracion) if dias_duracion else 30
                        fecha_fin = fecha_inicio + timedelta(days=dias)

                        suscripcion = Suscripcion.objects.create(
                            usuario=user,
                            plan=plan,
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin,
                            activa=True
                        )

                        Venta.objects.create(
                            usuario=user,
                            plan=plan,
                            precio=float(precio) if precio else plan.precio
                        )

                        cantidad += 1
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Usuario no encontrado: {username}'))
                    except Plan.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Plan no encontrado: {nombre_plan}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error en venta: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Ventas/Suscripciones importadas'))
            total_importados += cantidad

        # ==========================================
        # SUSCRIPCIONES (RENOVACIONES)
        # ==========================================
        suscripciones_path = os.path.join(base_path, 'suscripciones.csv')
        if os.path.exists(suscripciones_path):
            cantidad = 0
            with open(suscripciones_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    username = row.get('username', '').strip()
                    nombre_plan = row.get('plan', '').strip()
                    dias = row.get('dias', '30').strip()
                    objetivo = row.get('objetivo', 'mantener').strip()

                    if not username or not nombre_plan:
                        continue

                    try:
                        user = User.objects.get(username=username)
                        plan = Plan.objects.get(nombre=nombre_plan)

                        from datetime import timedelta
                        from django.utils import timezone

                        fecha_inicio = timezone.now().date()
                        dias_int = int(dias) if dias else 30
                        fecha_fin = fecha_inicio + timedelta(days=dias_int)

                        suscripcion = Suscripcion.objects.create(
                            usuario=user,
                            plan=plan,
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin,
                            activa=True,
                            objetivo_rutina=objetivo
                        )

                        cantidad += 1
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Usuario no encontrado: {username}'))
                    except Plan.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'[W] Plan no encontrado: {nombre_plan}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'[W] Error en suscripcion: {e}'))
            self.stdout.write(self.style.SUCCESS(f'[{cantidad}] Suscripciones importadas'))
            total_importados += cantidad

        self.stdout.write(self.style.SUCCESS(f'Carga masiva completada! Total: {total_importados} registros'))
