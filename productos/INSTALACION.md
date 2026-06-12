# 🔧 INSTRUCCIONES DE INSTALACIÓN - Sistema de Lotes

## ⚠️ IMPORTANTE: Pasos Requeridos

Sigue estos pasos **exactamente en este orden** para que el sistema funcione correctamente:

---

## PASO 1: Aplicar Migraciones de Base de Datos

### ¿Qué hace?
Crea las nuevas tablas `lotes` y `alertas_lotes` en la base de datos.

### Comando:
```bash
# Primero generar migraciones
python manage.py makemigrations

# Luego aplicarlas
python manage.py migrate
```

### Salida esperada:
```
Operations to perform:
  Apply all migrations: admin, auth, ...
Running migrations:
  Applying productos.0001_initial... OK
  Applying productos.0002_lote_precio_unitario_fecha_compra... OK
  Applying productos.0003_alertalote... OK
```

### ✅ Si ves "OK" en todas, continúa al siguiente paso.

---

## PASO 2: Verificar que los Modelos Están Registrados

### ¿Qué hace?
Confirma que los nuevos modelos están disponibles en Django Admin.

### Comando:
```bash
python manage.py shell
```

### Dentro del shell:
```python
# Verificar modelos
from productos.models import Lote, AlertaLote

# Contar lotes existentes (debe ser 0 inicialmente)
print(f"Total de lotes: {Lote.objects.count()}")

# Contar alertas
print(f"Total de alertas: {AlertaLote.objects.count()}")

# Salir
exit()
```

### Salida esperada:
```
Total de lotes: 0
Total de alertas: 0
```

---

## PASO 3: Generar Alertas Iniciales

### ¿Qué hace?
Crea las alertas automáticas para lotes existentes (si hay).

### Comando:
```bash
python manage.py generar_alertas_lotes
```

### Salida esperada:
```
✓ Se generaron X alertas automáticas
```

---

## PASO 4: Reiniciar el Servidor Django

### ¿Qué hace?
Carga los cambios en memoria y recarga la aplicación.

### Comando:
```bash
# Si estaba corriendo, presiona Ctrl+C
# Luego ejecuta:
python manage.py runserver
```

### Salida esperada:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## ✅ VERIFICACIÓN: ¿Funcionó todo?

Sigue esta lista de verificación:

### 1️⃣ Acceso a Panel Admin
```
Ir a: http://127.0.0.1:8000/admin/
Buscar: "Lotes" en el menú
✅ Debe aparecer "Lotes" y "Alertas de Lotes"
```

### 2️⃣ Acceso a Vista de Lotes
```
Ir a: http://127.0.0.1:8000/productos/
✅ Cada producto debe tener botón 🟦 "Ver Lotes"
```

### 3️⃣ Acceso a Panel de Alertas
```
Ir a: http://127.0.0.1:8000/productos/lotes/alertas/
✅ Debe cargar el dashboard (vacío si no hay alertas)
```

### 4️⃣ API REST
```
Ir a: http://127.0.0.1:8000/productos/api/alertas-lotes/
✅ Debe retornar JSON con estructura de alertas
```

---

## 🚨 Si Algo No Funciona

### Error: "ModuleNotFoundError: No module named 'productos'"
**Solución:**
```bash
# Asegúrate de estar en la carpeta correcta
cd c:\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\
python manage.py migrate
```

### Error: "Table 'lotes' doesn't exist"
**Solución:**
```bash
# Las migraciones no se aplicaron correctamente
python manage.py migrate --verbosity 2
```

### Error: "No module named 'productos.management.commands.generar_alertas_lotes'"
**Solución:**
```bash
# Verifica que la carpeta management/commands existe
# Asegúrate que haya archivos __init__.py en:
# - productos/management/
# - productos/management/commands/
```

### Vista en blanco o error 500
**Solución:**
```bash
# Revisa los logs
python manage.py shell
>>> from productos.models import AlertaLote
>>> AlertaLote.generar_alertas_automaticas()
# Verifica si hay errores
```

---

## 📅 Configuración de Tareas Automáticas (Opcional)

Si quieres que las alertas se generen automáticamente cada día:

### Opción A: Usar Celery Beat (Recomendado)

**Archivo: `gym/celery.py` o similar**

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generar-alertas-lotes-diarias': {
        'task': 'productos.tasks.generar_alertas_lotes_task',
        'schedule': crontab(hour=0, minute=0),  # Cada día a medianoche
    },
}
```

**Archivo: `productos/tasks.py`**

```python
from celery import shared_task
from productos.models import AlertaLote

@shared_task
def generar_alertas_lotes_task():
    """Tarea de Celery para generar alertas automáticas"""
    alertas = AlertaLote.generar_alertas_automaticas()
    return f"Se generaron {alertas} alertas"
```

**Comandos:**
```bash
# Terminal 1: Worker
celery -A gym worker -l info

# Terminal 2: Beat (scheduler)
celery -A gym beat -l info
```

### Opción B: Usar Cron (Sistema Operativo)

**En Linux/Mac:**
```bash
# Editar crontab
crontab -e

# Agregar esta línea (ejecuta a las 0:00 cada día)
0 0 * * * cd /ruta/a/tu/proyecto && python manage.py generar_alertas_lotes
```

**En Windows:**
```
Usar Programador de Tareas (Task Scheduler)
- Acción: Ejecutar programa
- Programa: python.exe
- Argumentos: manage.py generar_alertas_lotes
- Carpeta: C:\gym_django\...
- Horario: Diariamente a las 00:00
```

---

## 📚 Documentación Disponible

Después de instalar, consulta estos archivos:

1. **RESUMEN_IMPLEMENTACION.md** - Lo que se implementó
2. **GESTION_LOTES.md** - Documentación técnica completa (300+ líneas)
3. **GUIA_RAPIDA_LOTES.md** - Guía de usuario (250+ líneas)

---

## 🎯 Próximos Pasos Recomendados

### 1. Prueba Rápida
```bash
# Crear un producto de prueba si no existe
python manage.py shell
>>> from productos.models import Producto
>>> p = Producto.objects.first()
>>> print(p.nombre)

# Ir a /productos/detalle/ del producto para ver la interfaz
```

### 2. Crear un Lote de Prueba
```
Opción A: Registrar una compra en /compras/crear/
Opción B: Crear manualmente en /admin/productos/lote/
```

### 3. Generar Alertas de Prueba
```bash
# Generar alertas para lotes próximos a vencer
python manage.py generar_alertas_lotes

# Ver en /productos/lotes/alertas/
```

---

## 🔗 URLs Principales a Recordar

Después de instalar:

| URL | Función |
|-----|---------|
| `/productos/` | Lista de productos (con botones nuevos) |
| `/productos/<id>/detalle/` | Detalles de producto + lotes |
| `/productos/lotes/alertas/` | Dashboard de alertas |
| `/productos/api/lotes/<id>/` | API JSON de lotes |
| `/productos/api/alertas-lotes/` | API JSON de alertas |
| `/admin/productos/lote/` | Admin - Gestión de lotes |
| `/admin/productos/alertalote/` | Admin - Gestión de alertas |

---

## ✅ Checklist de Instalación

- [ ] Ejecuté `python manage.py makemigrations`
- [ ] Ejecuté `python manage.py migrate`
- [ ] Verifiqué modelos en shell
- [ ] Ejecuté `python manage.py generar_alertas_lotes`
- [ ] Reinicié servidor Django
- [ ] Accedí a `/admin/productos/`
- [ ] Accedí a `/productos/`
- [ ] Probé botón "Ver Lotes"
- [ ] Accedí a `/productos/lotes/alertas/`
- [ ] Probé API en `/productos/api/alertas-lotes/`

**Si marcastes todos ✅, ¡El sistema está instalado correctamente!**

---

## 🆘 Soporte Técnico

**Si encuentras problemas:**

1. Revisa los logs: `tail -f logs/django.log`
2. Ejecuta en debug: `python manage.py shell --i ipython`
3. Verifica migraciones: `python manage.py showmigrations productos`
4. Reinicia todo: `python manage.py migrate --verbosity 2`

---

## 📞 Contacto / Preguntas

**¿Dudas sobre la instalación?**
- Revisa GESTION_LOTES.md
- Revisa GUIA_RAPIDA_LOTES.md
- Ejecuta el comando help: `python manage.py generar_alertas_lotes --help`

---

**¡Listo para usar! 🚀**

Versión: 1.0  
Fecha: 26/04/2025  
Estado: Ready for Production ✅
