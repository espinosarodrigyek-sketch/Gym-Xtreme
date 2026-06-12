from django.contrib import admin
from .models import Plan

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo', 'precio', 'duracion_dias']
    list_filter = ['tipo']
    search_fields = ['nombre', 'descripcion']
