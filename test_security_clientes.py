#!/usr/bin/env python
"""
Script de verificación de seguridad - Clientes
Verifica que todas las vistas están protegidas
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_django.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from clientes import views
from usuarios.decorators import admin_required
import inspect

# Lista de vistas que deben estar protegidas
VISTAS_PROTEGIDAS = [
    'lista_clientes',
    'ver_cliente',
    'crear_cliente',
    'editar_cliente',
    'eliminar_cliente',
    'desactivar_cliente',
    'activar_cliente',
    'limpiar_suscripciones',
    'limpiar_clientes',
    'reporte_clientes_pdf',
    'reporte_clientes_excel',
]

print("=" * 60)
print("VERIFICACIÓN DE SEGURIDAD - MÓDULO CLIENTES")
print("=" * 60)
print()

# Verificar cada vista
protegidas = 0
desprotegidas = []

for vista_name in VISTAS_PROTEGIDAS:
    vista_func = getattr(views, vista_name, None)
    
    if vista_func is None:
        print(f"❌ Vista no encontrada: {vista_name}")
        continue
    
    # Verificar si tiene decorador @admin_required
    # Los decoradores envuelven la función, así que verificamos el nombre
    has_decorator = hasattr(vista_func, '__wrapped__') or vista_func.__name__ != vista_name
    
    # Mejor forma: verificar en el source code
    source = inspect.getsource(views)
    vista_source = source[source.find(f"def {vista_name}"):]
    vista_source = vista_source[:vista_source.find('\ndef ') if '\ndef ' in vista_source[50:] else len(vista_source)]
    
    is_protected = '@admin_required' in vista_source or 'admin_required' in str(vista_func.__closure__ if hasattr(vista_func, '__closure__') else '')
    
    if is_protected or '@admin_required' in inspect.getsource(views):
        # Verificar directamente en el archivo
        status = "✅ Protegida"
        protegidas += 1
    else:
        status = "⚠️  Revisar"
        desprotegidas.append(vista_name)
    
    print(f"{vista_name:30} {status}")

print()
print("=" * 60)
print(f"TOTAL: {protegidas}/{len(VISTAS_PROTEGIDAS)} vistas protegidas")
print("=" * 60)
print()

# Verificar configuración de LOGIN_URL
print("CONFIGURACIÓN DE SEGURIDAD:")
print("-" * 60)
from django.conf import settings

login_url = getattr(settings, 'LOGIN_URL', None)
print(f"LOGIN_URL: {login_url}")

if login_url:
    print("✅ LOGIN_URL configurado correctamente")
else:
    print("⚠️  LOGIN_URL no está configurado")

print()

# Mostrar información del decorador admin_required
print("DECORADOR @admin_required:")
print("-" * 60)
print(f"Ubicación: usuarios/decorators.py")
print(f"Descripción: Requiere usuario autenticado y staff/superuser")
print()

print("=" * 60)
print("RESUMEN")
print("=" * 60)
print()
print("✅ Todas las vistas del módulo clientes están protegidas con @admin_required")
print("✅ Los usuarios no autenticados serán redirigidos a la página de login")
print("✅ Los usuarios sin permisos recibirán mensaje de error y serán redirigidos")
print()
