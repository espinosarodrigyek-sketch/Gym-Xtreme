from django.urls import path
from . import views
from .frases import frase_api_view

app_name = 'api'

urlpatterns = [
    path('frase/', views.frase_motivacional, name='frase_motivacional'),
    path('frases/', frase_api_view, name='frase_api_view'),
    path('frases/nueva/', views.frase_motivacional, name='api_frases'),
]
