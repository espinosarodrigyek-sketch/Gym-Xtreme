import csv
import os
from django.contrib.auth.models import User
from django.core.management import call_command
from usuarios.models import Perfil
from productos.models import Producto, Categoria  # ✅ agregado Categoria
from planes.models import Plan


def importar_usuarios_desde_csv(file_path):
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
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
                continue
                
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            Perfil.objects.create(
                user=user,
                rol=rol,
                telefono=telefono,
                direccion=direccion
            )
            cantidad += 1
            
    return cantidad


def importar_productos_desde_csv(file_path):
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            descripcion = row.get('descripcion', '').strip()
            categoria = row.get('categoria', '').strip()
            precio_costo = row.get('precio_costo', '0')
            precio_venta = row.get('precio_venta', '0')
            stock_actual = row.get('stock_actual', '0')
            estado = row.get('estado', 'activo').strip()
            
            if not nombre:
                continue
                
            if Producto.objects.filter(nombre=nombre).exists():
                continue
            
            # ✅ FIX AQUÍ (convertir string a objeto Categoria)
            categoria_obj, _ = Categoria.objects.get_or_create(
                nombre=categoria
            )
            
            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria_obj,  # ✅ corregido
                precio_costo=precio_costo,
                precio_venta=precio_venta,
                stock_actual=int(stock_actual),
                estado=estado
            )
            producto.save()
            cantidad += 1
            
    return cantidad


def importar_planes_desde_csv(file_path):
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            tipo = row.get('tipo', '1_mes').strip()
            precio = row.get('precio', '0')
            descripcion = row.get('descripcion', '').strip()
            duracion_dias = row.get('duracion_dias', '30')
            
            if not nombre:
                continue
                
            if Plan.objects.filter(nombre=nombre).exists():
                continue
            
            plan = Plan(
                nombre=nombre,
                tipo=tipo,
                precio=precio,
                descripcion=descripcion,
                duracion_dias=int(duracion_dias)
            )
            plan.save()
            cantidad += 1
            
    return cantidad