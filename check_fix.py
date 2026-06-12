import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
sys.path.insert(0, project_root)
os.environ['DJANGO_SETTINGS_MODULE'] = 'gym.settings'

import django
django.setup()

print("=== 1. TEMPLATE COMPILATION CHECK ===")
from django.template.loader import get_template
try:
    t = get_template('productos/detalle_producto.html')
    print("detalle_producto.html - COMPILES OK")
except Exception as e:
    print(f"detalle_producto.html - ERROR: {e}")

try:
    t = get_template('productos/lista_productos.html')
    print("lista_productos.html - COMPILES OK")
except Exception as e:
    print(f"lista_productos.html - ERROR: {e}")

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

factory = RequestFactory()
request = factory.get('/productos/15/detalle/')
request.user = FakeUser()
request.session = SessionStore()
request._messages = FallbackStorage(request)

try:
    response = detalle_producto(request, 15)
    content = response.content.decode('utf-8', errors='replace')
    print(f"Detail view rendered, length: {len(content)}")
    assert 'Producto no encontrado' not in content, "Product not found"
    assert 'Te Verde' in content, "Product name not shown"
    print("Detail view renders correctly - OK")
except Exception as e:
    print(f"Detail view ERROR: {e}")
    import traceback; traceback.print_exc()

print("\n=== 3. VER BUTTON URL CHECK ===")
from django.urls import reverse
url = reverse('detalle_producto', kwargs={'id': 15})
print(f"URL for product 15 detail: {url}")

# Check lista_productos has the VER button pointing to the right URL
from productos.views import lista_productos
request2 = factory.get('/productos/')
request2.user = FakeUser()
request2.session = SessionStore()
request2._messages = FallbackStorage(request2)
response2 = lista_productos(request2)
content2 = response2.content.decode('utf-8', errors='replace')
if 'detalle_producto' in content2 or '/productos/15/detalle/' in content2:
    print("VER button links found in product list - OK")
else:
    print("VER button links NOT found")

print("\n=== ALL CHECKS DONE ===")