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

from productos.views import detalle_producto
factory = RequestFactory()

request = factory.get('/productos/15/detalle/')
request.user = FakeUser()
request.session = SessionStore()
request._messages = FallbackStorage(request)
response = detalle_producto(request, 15)
content = response.content.decode('utf-8', errors='replace')

# Search for content-related strings
print("=== SEARCHING RENDERED CONTENT ===")
# Let's look for the card-dark divs that should have product info
if 'card-dark-header' in content:
    idx = content.find('card-dark-header')
    print(f"Found card-dark-header at {idx}")
    print(f"Context: {content[idx-50:idx+200]}")
else:
    print("NO card-dark-header found!")

# Search for "Categoría" which should be in the stats grid
if 'Categor' in content:
    idx = content.index('Categor')
    print(f"\nFound 'Categor' at {idx}")
    print(f"Context: {content[idx:idx+100]}")
else:
    print("\nNO 'Categor' found!")

# Let's find where the content block starts
if '{% block content %}' in content or 'contenido' in content:
    print("\nFound content block marker")

# Check the full content structure
lines = content.split('\n')
print(f"\nTotal lines: {len(lines)}")
# Find lines with actual content from the detalle template
for i, line in enumerate(lines):
    stripped = line.strip()
    if any(kw in stripped for kw in ['<title>', '</title>', 'card-dark-header', 'fa-box-open', 'Total Lotes', 'Categoría', 'Precio Costo', 'Última Compra', 'Lotes Registrados', 'Nuevo Lote', 'btn-gym']):
        print(f"  Line {i}: {stripped[:120]}")

# Check if the base.html's content block is being rendered
# The template extends base.html and should have {% block content %}
print("\n=== CHECKING TEMPLATE STRUCTURE ===")
print("Template extends base.html and should render content block")

# Let's also look at the actual template parsing
from django.template.loader import get_template
t = get_template('productos/detalle_producto.html')
print(f"\nTemplate origin: {t.origin}")
print(f"Template name: {t.template.name}")

# Debug: render the template context directly
from django.template import Context
from productos.models import Producto
producto = Producto.objects.get(id_producto=15)
from django.utils.timezone import now
from django.db.models import Count
lotes = list(producto.lotes.all().order_by('fecha_vencimiento'))
print(f"\nProduct: {producto.nombre}")
print(f"Lots count: {len(lotes)}")