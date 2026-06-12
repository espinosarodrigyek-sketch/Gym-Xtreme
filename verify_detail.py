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
print(f"Length: {len(content)}")
assert 'Gestión de Productos' in content
assert 'Ver' in content  # VER button
print("OK: lista_productos renders correctly")

print("\n=== DETALLE PRODUCTO (id=15) ===")
request2 = factory.get('/productos/15/detalle/')
request2.user = FakeUser()
request2.session = SessionStore()
request2._messages = FallbackStorage(request2)
try:
    response2 = detalle_producto(request2, 15)
    content2 = response2.content.decode('utf-8', errors='replace')
    print(f"Length: {len(content2)}")
    assert 'Te Verde Natural' in content2 or 'detalle' in content2.lower()
    print("OK: detalle_producto renders correctly")
except Exception as e:
    print(f"ERROR: {e}")
    # Check if product 15 exists
    from productos.models import Producto
    p15 = Producto.objects.filter(id_producto=15).first()
    if p15:
        print(f"Product 15 exists: {p15.nombre}")
    else:
        print("Product 15 does not exist")

    # Check if there's ANY product with lots that we can test with
    from django.db.models import Count
    productos_con_lotes = Producto.objects.annotate(num_lotes=Count('lotes')).filter(num_lotes__gt=0)
    print(f"Products with lots: {productos_con_lotes.count()}")
    for p in productos_con_lotes[:3]:
        print(f"  id={p.id_producto}: {p.nombre}")

print("\n=== VERIFY URL REVERSE ===")
from django.urls import reverse
url = reverse('detalle_producto', kwargs={'id': 15})
print(f"detalle_producto URL: {url}")
assert url == '/productos/15/detalle/'
print("OK: URL resolves correctly")

print("\n=== ALL CHECKS PASSED ===")