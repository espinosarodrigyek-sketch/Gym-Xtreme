import sys, os
project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
sys.path.insert(0, project_root)
os.environ['DJANGO_SETTINGS_MODULE'] = 'gym.settings'
import django; django.setup()
from django.test import RequestFactory
from productos.views import detalle_producto
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.fallback import FallbackStorage

class FakeUser:
    is_authenticated = True; is_staff = True; pk = 1; is_superuser = True
    username = 'admin'; first_name = 'Admin'; id = 1
    perfil = type('P', (), {'foto': None})()

factory = RequestFactory()
req = factory.get('/productos/15/detalle/')
req.user = FakeUser(); req.session = SessionStore(); req._messages = FallbackStorage(req)
resp = detalle_producto(req, 15)
c = resp.content.decode('utf-8', errors='replace')

# Search for specific rendered content
import re
# Find category section
m = re.search(r'Categor.{0,3}</p>\s*<p[^>]*>(.+?)</p>', c)
if m: print(f"Category shown: {m.group(1).strip()}")

# Find if the table rows have lot data
rows = re.findall(r'<strong>(.+?)</strong>', c)
print(f"Strong tags: {rows[:10]}")

# Check for the product header name
h1 = re.search(r'<h1[^>]*>(.+?)</h1>', c)
if h1: print(f"Product h1: {h1.group(1).strip()}")

# Check the lotes table for content
tds = re.findall(r'<td style="padding:12px;color:#fff;">(.+?)</td>', c, re.DOTALL)
print(f"Table cells (first 5): {[t.strip()[:40] for t in tds[:5]]}")

# Check for accesorios products (non-consumable)
print(f"\n'Accesorios' in page: {'Accesorios' in c}")
print(f"'Sin categoría' in page: {'Sin categoría' in c}")