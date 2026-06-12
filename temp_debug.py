import django
from decimal import Decimal
from django.contrib.auth.models import User
from usuarios.models import Perfil, HistorialPeso, Suscripcion
from planes.models import Plan
from django.utils import timezone
from datetime import timedelta
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from clientes.views import lista_clientes

django.setup()

admin = User.objects.create_user(username="admin_dbg6", password="StrongPass123!", is_staff=True)
cliente = User.objects.create_user(username="cliente_dbg6", email="dbg6@example.com", password="StrongPass123!")
perfil, _ = Perfil.objects.get_or_create(user=cliente, defaults={"rol": "cliente"})
perfil.peso = None
perfil.estatura = None
perfil.save()
plan = Plan.objects.create(nombre="Plan Debug6", precio=35000, descripcion="x", duracion_dias=30)
Suscripcion.objects.create(usuario=cliente, plan=plan, fecha_inicio=timezone.now().date()-timedelta(days=5), fecha_fin=timezone.now().date()+timedelta(days=25), activa=True, estado="activa", objetivo_rutina="mantener")
h = HistorialPeso.objects.create(usuario=cliente, peso=Decimal("68.50"), estatura=Decimal("1.70"))
print("historial", h.id, h.peso, h.estatura)
request = RequestFactory().get(reverse("lista_clientes"))
request.user = admin
mw = SessionMiddleware(lambda req: None)
mw.process_request(request)
request.session.save()
response = lista_clientes(request)
print("status", response.status_code)
print("context len", len(response.context_data["clientes_data"]))
for item in response.context_data["clientes_data"]:
    print("username", item["usuario"].username)
    print("peso", item["perfil"].peso, type(item["perfil"].peso))
    print("estatura", item["perfil"].estatura, type(item["perfil"].estatura))
