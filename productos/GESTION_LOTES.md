# Sistema de Gestión de Lotes - Documentación Completa

## 📋 Descripción General

El sistema de gestión de lotes permite administrar completamente los lotes de productos consumibles, incluyendo:

- **Creación automática de lotes** al registrar compras
- **Seguimiento de información** de lotes (fecha de compra, fabricación, vencimiento, precio)
- **Alertas automáticas** para lotes próximos a vencer
- **Visualización detallada** de lotes por producto
- **Dashboard de alertas** con diferentes niveles de severidad

## 🏗️ Estructura de Modelos

### Modelo: `Lote`

Representa un lote de producto con información de vencimiento y seguimiento de stock.

**Campos:**
- `id_lote`: ID único (BigAutoField)
- `producto`: ForeignKey a Producto
- `numero_lote`: Generado automáticamente (ej: LOTE001, LOTE002)
- `cantidad`: Cantidad de unidades en el lote
- `precio_unitario`: Precio unitario de compra del lote
- `fecha_compra`: Fecha cuando se compró el lote
- `fecha_fabricacion`: Fecha de fabricación del producto
- `fecha_vencimiento`: Fecha de vencimiento
- `estado`: 'disponible', 'agotado', 'vencido'
- `fecha_creacion`: Timestamp de creación automática
- `notas`: Notas adicionales (opcional)

**Meta:**
- Tabla: `lotes`
- Ordenamiento: Por fecha_vencimiento
- Índices únicos: (producto, numero_lote)

**Métodos útiles:**
- `esta_vencido()`: Verifica si el lote ha vencido
- `dias_para_vencer()`: Retorna días restantes hasta vencimiento
- `clase_css_estado()`: Retorna clase CSS para estilos

### Modelo: `AlertaLote`

Representa una alerta automática generada para lotes próximos a vencer.

**Campos:**
- `id_alerta`: ID único (BigAutoField)
- `lote`: ForeignKey a Lote
- `nivel`: 'bajo', 'medio', 'alto', 'critico'
- `dias_para_vencer`: Días restantes cuando se generó la alerta
- `titulo`: Título descriptivo de la alerta
- `descripcion`: Información detallada del lote
- `leida`: Boolean para marcar como leída
- `activa`: Boolean para activar/desactivar alertas
- `fecha_creacion`: Timestamp automático
- `fecha_lectura`: Timestamp cuando se marcó como leída

**Meta:**
- Tabla: `alertas_lotes`
- Ordenamiento: Por -fecha_creacion (más recientes primero)

**Métodos útiles:**
- `marcar_como_leida()`: Marca la alerta como leída
- `generar_alertas_automaticas()`: Método de clase para crear alertas automáticas
- `obtener_alertas_activas()`: Método de clase para obtener alertas ordenadas por severidad

## 🔄 Flujo de Creación de Lotes

### 1. Registro de Compra
```
Usuario registra compra en /compras/crear/
    ↓
Se ingresa: proveedor, producto, cantidad, precio unitario
Se ingresa: fecha de fabricación, fecha de vencimiento
    ↓
Sistema genera automáticamente el número de lote (LOTE001, LOTE002, etc.)
    ↓
Se crea registro en tabla `lotes`
Se actualiza stock del producto
```

### 2. Generación Automática de Alertas
```
Nightly cron job ejecuta: python manage.py generar_alertas_lotes
    ↓
Para cada lote disponible:
    - Si vence en ≤ 3 días → Alerta CRÍTICA (🔴)
    - Si vence en ≤ 7 días → Alerta ALTA (🟠)
    - Si vence en ≤ 14 días → Alerta MEDIA (🟡)
    ↓
Se registran alertas en tabla `alertas_lotes`
```

## 🚀 Vistas y URLs Disponibles

### Vistas de Productos

| URL | Vista | Descripción |
|-----|-------|-------------|
| `/productos/<id>/detalle/` | `detalle_producto` | Información completa del producto + todos sus lotes |
| `/productos/lotes/alertas/` | `alertas_lotes_prox_vencer` | Dashboard de alertas de vencimiento |
| `/productos/lotes/alerta/<id>/marcar-leida/` | `marcar_alerta_leida` | Marca una alerta como leída (AJAX) |
| `/productos/lotes/alerta/<id>/desactivar/` | `desactivar_alerta` | Desactiva una alerta (AJAX) |

### APIs REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/productos/api/lotes/<producto_id>/` | GET | JSON con todos los lotes de un producto |
| `/productos/api/alertas-lotes/` | GET | JSON con todas las alertas activas |

## 📊 Ejemplos de Uso

### Ejemplo 1: Ver Lotes de un Producto
```
1. Ir a /productos/ (lista de productos)
2. Hacer clic en el botón 🟦 (Ver Lotes) para el producto
3. Se abre /productos/123/detalle/ con:
   - Información del producto
   - Tabla de todos los lotes
   - Estadísticas de lotes disponibles/vencidos
   - Botón para crear nuevo lote
```

### Ejemplo 2: Consultar Alertas
```
1. Ir a /productos/lotes/alertas/
2. Se muestra dashboard con:
   - Contadores: Total, No leídas, Críticas
   - Filtros por nivel (Crítica, Alta, Media, Baja)
   - Tarjetas con detalles de cada alerta
3. Opciones por alerta:
   - Marcar como leída
   - Desactivar alerta
   - Ver producto completo
```

### Ejemplo 3: Usar API de Lotes (JavaScript)
```javascript
// Obtener lotes de un producto
fetch('/productos/api/lotes/123/')
    .then(r => r.json())
    .then(data => {
        console.log('Producto:', data.producto.nombre);
        console.log('Total lotes:', data.total_lotes);
        data.lotes.forEach(lote => {
            console.log(`${lote.numero_lote}: ${lote.cantidad} uds vence ${lote.fecha_vencimiento}`);
        });
    });

// Obtener alertas activas
fetch('/productos/api/alertas-lotes/')
    .then(r => r.json())
    .then(data => {
        console.log(`${data.criticas} alertas críticas`);
        data.alertas.forEach(alerta => {
            console.log(`[${alerta.nivel}] ${alerta.titulo}`);
        });
    });
```

## 🛠️ Configuración y Comandos

### Comando: Generar Alertas Automáticas

```bash
# Generar con parámetros por defecto (3, 7, 14 días)
python manage.py generar_alertas_lotes

# Con parámetros personalizados
python manage.py generar_alertas_lotes --dias-critico 2 --dias-alto 5 --dias-medio 10
```

### Integración con Tareas Programadas (Celery)

Para ejecutar automáticamente cada día:

```python
# En settings.py o celery.py
CELERY_BEAT_SCHEDULE = {
    'generar-alertas-lotes': {
        'task': 'productos.tasks.generar_alertas_lotes_task',
        'schedule': crontab(hour=0, minute=0),  # Cada día a medianoche
    },
}
```

## 🎯 Niveles de Alertas

| Nivel | Icono | Color | Descripción | Días |
|-------|-------|-------|-------------|------|
| Crítico | 🔴 | Rojo | Urgencia máxima de venta/consumo | ≤ 3 |
| Alto | 🟠 | Naranja | Vencimiento próximo | ≤ 7 |
| Medio | 🟡 | Amarillo | Supervisión necesaria | ≤ 14 |
| Bajo | 🔵 | Azul | Información | > 14 |

## 💾 Información Guardada por Lote

Cada lote mantiene un registro completo:

```json
{
    "numero_lote": "LOTE001",
    "producto": "Proteína Whey 1kg",
    "cantidad": 50,
    "precio_unitario": 8500,
    "fecha_compra": "2025-04-15",
    "fecha_fabricacion": "2025-03-01",
    "fecha_vencimiento": "2026-03-01",
    "estado": "disponible",
    "dias_para_vencer": 340,
    "fecha_creacion": "2025-04-15 14:30:00"
}
```

## 📈 Panel Admin Django

El sistema está completamente integrado en Django Admin:

1. **ProductoAdmin**: Gestión de productos
2. **LoteAdmin**: CRUD de lotes con campos readonly automáticos
3. **AlertaLoteAdmin**: Visualización y gestión de alertas

Acceso: `/admin/productos/`

## 🔐 Permisos

Todas las vistas de lotes requieren:
- Decorador: `@admin_required`
- Necesita usuario autenticado y con permisos de administrador

## 🐛 Solución de Problemas

### Problema: Las alertas no se generan
**Solución:**
```bash
# Verificar que el modelo está registrado
python manage.py shell
>>> from productos.models import AlertaLote
>>> AlertaLote.generar_alertas_automaticas()

# Verificar tareas celery
celery -A gym worker -l info
```

### Problema: Lotes no se crean al registrar compra
**Solución:**
1. Verificar que DetalleCompra.crear_lote_desde_detalle() se ejecuta
2. Revisar el template form_compra.html y que envíe fechas
3. Verificar errores en Django logs

### Problema: Stock no se actualiza
**Solución:**
1. Verificar método save() del modelo Lote
2. Usar `F()` para operaciones atómicas
3. Revisar permisos de base de datos

## 📚 Archivos Modificados

- `productos/models.py`: Agregados modelos Lote y AlertaLote
- `productos/views.py`: Nuevas vistas para lotes y alertas
- `productos/urls.py`: Nuevas URLs
- `productos/admin.py`: Registros en Django Admin
- `productos/templates/productos/detalle_producto.html`: Template nuevo
- `productos/templates/productos/alertas_lotes.html`: Template nuevo
- `compras/models.py`: Actualizado crear_lote_desde_detalle()

## 🔮 Características Futuras

- [ ] Notificaciones por email de alertas críticas
- [ ] Exportar alertas a CSV/PDF
- [ ] Historial de cambios de estado de lotes
- [ ] Gráficos de vencimientos por mes
- [ ] API de consumo de lotes (FIFO)
- [ ] QR codes para seguimiento de lotes

---

**Última actualización:** 26/04/2025
**Versión:** 1.0
