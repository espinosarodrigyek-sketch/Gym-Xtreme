import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
sys.path.insert(0, project_root)
os.environ['DJANGO_SETTINGS_MODULE'] = 'gym.settings'

import django
django.setup()

# Test loading the formato_cop template tag
from django.template import engines
from django.template.loader import get_template
try:
    t = get_template('productos/detalle_producto.html')
    print("detalle_producto.html compiles OK")
except Exception as e:
    print(f"detalle_producto.html ERROR: {e}")

try:
    t = get_template('productos/lista_productos.html')
    print("lista_productos.html compiles OK")
except Exception as e:
    print(f"lista_productos.html ERROR: {e}")

# Check if formato_cop templatetag exists
from django.template import libraries
try:
    lib = libraries.Libraries()
    lib.load('formato_cop')
    print("formato_cop templatetag library found")
except Exception as e:
    print(f"formato_cop NOT found: {e}")

# List all available templatetag modules
import pkgutil
from django.template import builtins
print("\nRegistered template tag libraries:")
for name in dir(builtins):
    if not name.startswith('_'):
        print(f"  {name}")

# Check if the templatetags directory exists with formato_cop
import glob as g
templatetag_files = g.glob(f"{project_root}/**/templatetags/*.py", recursive=True)
print(f"\nTemplatetag files found: {len(templatetag_files)}")
for f in templatetag_files:
    print(f"  {f}")

# Test rendering the detail view
from django.test import RequestFactory
from productos.views import detalle_producto
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.fallback import FallbackStorage

class FakeUser:
    is_authenticated = True
    is_staff = True
    pk = 1
    is_superuser = True

try:
    factory = RequestFactory()
    request = factory.get('/productos/15/detalle/')
    request.user = FakeUser()
    request.session = SessionStore()
    request._messages = FallbackStorage(request)
    response = detalle_producto(request, 15)
    content = response.content.decode('utf-8', errors='replace')
    if 'Producto no encontrado' in content or '404' in content:
        print("\nDetail view: Product 15 not found")
    else:
        print(f"\nDetail view rendered OK, content length: {len(content)}")
        # Check for key elements
        checks = {
            'producto.nombre' in content or 'Te Verde' in content: 'product name shown',
            'lotes_disponibles' in content or 'Total Lotes' in content: 'lot section shown',
            'Nuevo Lote' in content or 'crear_compra' in content: 'new lot button',
        }
        for ok, desc in checks.items():
            status = "OK" if ok else "MISSING"
            print(f"  [{status}] {desc}")
except Exception as e:
    print(f"\nDetail view ERROR: {e}")
    import traceback; traceback.print_exc()