import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
sys.path.insert(0, project_root)
os.environ['DJANGO_SETTINGS_MODULE'] = 'gym.settings'

import django
django.setup()

print("=== 1. TEMPLATE COMPILATION ===")
from django.template.loader import get_template
try:
    t = get_template('productos/detalle_producto.html')
    print("detalle_producto.html - COMPILES OK")
except Exception as e:
    print(f"detalle_producto.html - ERROR: {e}")

print("\n=== 2. VIEW RENDERING ===")
from django.test import RequestFactory
from productos.views import detalle_producto
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.fallback import FallbackStorage

class FakeUser:
    is_authenticated = True
    is_staff = True
    pk = 1
    is_superuser = True
    username = 'admin'
    first_name = 'Admin'
    id = 1
    perfil = type('Perfil', (), {'foto': None})()

factory = RequestFactory()
request = factory.get('/productos/15/detalle/')
request.user = FakeUser()
request.session = SessionStore()
request._messages = FallbackStorage(request)

try:
    response = detalle_producto(request, 15)
    content = response.content.decode('utf-8', errors='replace')
    print(f"Rendered OK, length: {len(content)}")

    checks = {
        'Te Verde': 'product name',
        'categoria': 'category shown',
        'Total Lotes': 'lots stats',
        'Lotes Registrados': 'lots table',
        'Nuevo Lote': 'new lot button',
        'Volver a Productos': 'back button',
        'Editar Producto': 'edit button',
    }
    all_ok = True
    for text, desc in checks.items():
        if text in content:
            print(f"  [OK] {desc}")
        else:
            print(f"  [FAIL] {desc}: '{text}' NOT found")
            all_ok = False

    # Check for VER links in lista_productos too
    request2 = factory.get('/productos/')
    request2.user = FakeUser()
    request2.session = SessionStore()
    request2._messages = FallbackStorage(request2)
    from productos.views import lista_productos
    response2 = lista_productos(request2)
    content2 = response2.content.decode('utf-8', errors='replace')
    if '/productos/15/detalle/' in content2:
        print("  [OK] VER button links to /productos/15/detalle/")
    else:
        print("  [FAIL] VER button link not found")

    if all_ok:
        print("\n=== ALL CHECKS PASSED ===")
    else:
        print("\n=== SOME CHECKS FAILED ===")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()