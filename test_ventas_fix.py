#!/usr/bin/env python
"""
Script de prueba para verificar que los cambios en ventas funcionen correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_django.settings')
sys.path.insert(0, '/path/to/gym')
django.setup()

from ventas.forms import FiltroVentasForm, FechaVentaForm
from ventas.models import Venta
from datetime import datetime
from django.contrib.auth.models import User

print("✓ Importaciones exitosas")
print()

# Prueba 1: Verificar que FiltroVentasForm funciona
print("PRUEBA 1: Verificar FiltroVentasForm")
print("-" * 50)
test_data = {
    'id_venta': '1',
    'fecha': '2026-05-22',
    'total_min': '1000',
    'total_max': '5000'
}
form = FiltroVentasForm(test_data)
print(f"Form válido: {form.is_valid()}")
if form.is_valid():
    print(f"Datos limpios: {form.cleaned_data}")
    print(f"  - ID Venta: {form.cleaned_data.get('id_venta')}")
    print(f"  - Fecha: {form.cleaned_data.get('fecha')}")
    print(f"  - Total Min: {form.cleaned_data.get('total_min')}")
    print(f"  - Total Max: {form.cleaned_data.get('total_max')}")
else:
    print(f"Errores: {form.errors}")
print()

# Prueba 2: Verificar que FechaVentaForm funciona
print("PRUEBA 2: Verificar FechaVentaForm")
print("-" * 50)
test_data_fecha = {
    'fecha': '2026-05-22T14:30'
}
form_fecha = FechaVentaForm(test_data_fecha)
print(f"Form válido: {form_fecha.is_valid()}")
if form_fecha.is_valid():
    print(f"Datos limpios: {form_fecha.cleaned_data}")
    print(f"  - Fecha: {form_fecha.cleaned_data.get('fecha')}")
else:
    print(f"Errores: {form_fecha.errors}")
print()

# Prueba 3: Verificar que el modelo Venta tiene auto_now_add=False
print("PRUEBA 3: Verificar modelo Venta")
print("-" * 50)
fecha_field = Venta._meta.get_field('fecha')
print(f"Campo fecha:")
print(f"  - auto_now_add: {fecha_field.auto_now_add}")
print(f"  - auto_now: {fecha_field.auto_now}")
print(f"  - null: {fecha_field.null}")
print(f"  - blank: {fecha_field.blank}")
print()

# Prueba 4: Crear una venta con fecha manual
print("PRUEBA 4: Crear venta con fecha manual")
print("-" * 50)
try:
    # Obtener o crear un usuario de prueba
    user, created = User.objects.get_or_create(username='testuser')
    
    # Crear una venta con fecha manual
    fecha_manual = datetime(2026, 5, 22, 14, 30)
    venta = Venta.objects.create(
        usuario=user,
        total=5000.00,
        fecha=fecha_manual
    )
    print(f"✓ Venta creada exitosamente")
    print(f"  - ID: {venta.id_venta}")
    print(f"  - Fecha: {venta.fecha}")
    print(f"  - Usuario: {venta.usuario.username}")
    print(f"  - Total: {venta.total}")
    
    # Limpiar (eliminar la venta de prueba)
    venta.delete()
    print(f"✓ Venta de prueba eliminada")
except Exception as e:
    print(f"✗ Error al crear venta: {e}")
print()

print("=" * 50)
print("TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 50)
