import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
sys.path.insert(0, project_root)
os.environ['DJANGO_SETTINGS_MODULE'] = 'gym.settings'

import django
django.setup()

from django.test import RequestFactory
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

from productos.views import detalle_producto, lista_productos
factory = RequestFactory()

print("=== LISTA PRODUCTOS ===")
request = factory.get('/productos/')
request.user = FakeUser()
request.session = SessionStore()
request._messages = FallbackStorage(request)
response = lista_productos(request)
content = response.content.decode('utf-8', errors='replace')
assert 'Gestión de Productos' in content
print("OK: lista_productos renders")

# Check VER button URL
import re
ver_links = re.findall(r'href="([^"]*detalle[^"]*)"', content)
print(f"VER links found: {ver_links[:5]}")
for link in ver_links[:5]:
    assert '/productos/' in link and '/detalle/' in link, f"Bad VER link: {link}"
print("OK: VER links point to correct URLs")

print("\n=== DETALLE PRODUCTO (id=15) ===")
request2 = factory.get('/productos/15/detalle/')
request2.user = FakeUser()
request2.session = SessionStore()
request2._messages = FallbackStorage(request2)
response2 = detalle_producto(request2, 15)
content2 = response2.content.decode('utf-8', errors='replace')
print(f"Length: {len(content2)}")

# Print a portion to see what's rendered
print(f"\nFirst 500 chars:\n{content2[:500]}")
print(f"\nLast 300 chars:\n{content2[-300:]}")

# Search for key strings
checks = {
    'Te Verde': 'product name',
    'detalle': 'detail text',
    'Lotes': 'lots section',
    'Nuevo Lote': 'new lot button',
    'lista_productos': 'back link',
}
for text, desc in checks.items():
    if text in content2:
        print(f"  [OK] {desc}: '{text}' found")
    else:
        print(f"  [FAIL] {desc}: '{text}' NOT found")

print("\n=== CHECKING OTHER PRODUCTS WITH LOTS ===")
from productos.models import Producto
for pid in [1, 2, 4]:
    p = Producto.objects.get(id_producto=pid)
    print(f"\nProduct {pid}: {p.nombre}, categoria={p.categoria}, consumible={p.categoria.es_consumible if p.categoria else 'N/A'}")
    request3 = factory.get(f'/productos/{pid}/detalle/')
    request3.user = FakeUser()
    request3.session = SessionStore()
    request3._messages = FallbackStorage(request3)
    try:
        resp = detalle_producto(request3, pid)
        c = resp.content.decode('utf-8', errors='replace')
        print(f"  Rendered OK, length={len(c)}")
        if p.nombre.split()[0] in c:
            print(f"  [OK] Product name found in output")
        else:
            print(f"  [??] Product name '{p.nombre}' may not match rendered text")
    except Exception as e:
        print(f"  ERROR: {e}")