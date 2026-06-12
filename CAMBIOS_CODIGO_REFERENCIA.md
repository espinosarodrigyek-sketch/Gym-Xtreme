# Cambios de Código - Referencia Rápida

## models.py - Productos

### Métodos agregados a clase Producto:

```python
def tiene_lotes_vigentes(self):
    """Verifica si tiene lotes aún vigentes"""
    from django.utils.timezone import now
    current_date = now().date()
    return self.lotes.filter(
        estado='disponible',
        fecha_vencimiento__gte=current_date
    ).exists()

def esta_vencido(self):
    """Verifica si TODOS los lotes del producto están vencidos"""
    from django.utils.timezone import now
    current_date = now().date()
    
    # Si tiene lotes disponibles no vencidos, NO está vencido
    if self.tiene_lotes_vigentes():
        return False
    
    # Si tiene lotes pero todos están vencidos, sí está vencido
    if self.lotes.exists():
        return True
    
    # Si no tiene lotes, no está vencido
    return False
```

---

## views.py - Productos

### 1. Importar formato al inicio del archivo:

```python
from gym.formato import formato_cop_signo
```

### 2. Actualizar `agregar_carrito()`:

**Ubicación:** Línea ~269

**Agregado:**
```python
# Validar que el producto no esté vencido
if producto.esta_vencido():
    messages.error(request, f'"{producto.nombre}" está vencido y no está disponible para la venta.')
    return redirect('catalogo')
```

**Contexto completo:**
```python
@login_required
def agregar_carrito(request, id):
    producto = get_object_or_404(Producto, id_producto=id)
    cantidad = int(request.POST.get("cantidad", 1))

    if cantidad <= 0:
        messages.error(request, "La cantidad debe ser mayor a 0.")
        return redirect('catalogo')

    # NUEVO: Validar vencimiento
    if producto.esta_vencido():
        messages.error(request, f'"{producto.nombre}" está vencido y no está disponible para la venta.')
        return redirect('catalogo')

    # ... resto del código
```

### 3. Actualizar `detalle_producto()`:

**Ubicación:** Línea ~520

```python
@admin_required
def detalle_producto(request, id):
    """Vista detallada de un producto con sus lotes asociados"""
    from .models import Lote
    from gym.formato import formato_cop_signo
    
    producto = get_object_or_404(Producto, id_producto=id)
    lotes = Lote.objects.filter(producto=producto).order_by('fecha_vencimiento')
    
    # Calcular estadísticas de lotes
    lotes_disponibles = lotes.filter(estado='disponible')
    lotes_vencidos = lotes.filter(estado='vencido')
    lotes_agotados = lotes.filter(estado='agotado')
    
    total_stock_lotes = sum(lote.cantidad for lote in lotes_disponibles)
    
    # Formatear precios
    producto_con_precios = {
        'producto': producto,
        'precio_costo_fmt': formato_cop_signo(producto.precio_costo),
        'precio_venta_fmt': formato_cop_signo(producto.precio_venta),
    }
    
    context = {
        'producto': producto,
        'precio_costo_fmt': formato_cop_signo(producto.precio_costo),
        'precio_venta_fmt': formato_cop_signo(producto.precio_venta),
        'lotes': lotes,
        'lotes_disponibles': lotes_disponibles,
        'lotes_vencidos': lotes_vencidos,
        'lotes_agotados': lotes_agotados,
        'total_stock_lotes': total_stock_lotes,
        'cantidad_lotes': lotes.count(),
        'formato_cop_signo': formato_cop_signo,
    }
    
    return render(request, 'productos/detalle_producto.html', context)
```

### 4. Actualizar `alertas_lotes_prox_vencer()`:

**Ubicación:** Línea ~564

```python
@admin_required
def alertas_lotes_prox_vencer(request):
    """
    Vista para mostrar alertas de lotes próximos a vencer.
    
    Clasificación por días restantes:
    - CRÍTICA: ≤ 7 días (🔴 rojo)
    - ALTA: 8-14 días (🟠 naranja)
    - MEDIA: 15-30 días (🟡 amarillo)
    - BAJA: > 30 días (🟢 verde)
    """
    from .models import Lote
    from gym.formato import formato_cop_signo
    
    # Obtener todos los lotes disponibles (no vencidos)
    lotes_vigentes = Lote.objects.filter(
        estado='disponible'
    ).order_by('fecha_vencimiento')
    
    # Clasificar lotes por nivel de alerta
    alertas_criticas = []      # ≤ 7 días
    alertas_altas = []         # 8-14 días
    alertas_medias = []        # 15-30 días
    alertas_bajas = []         # > 30 días
    lotes_sin_alerta = []      # Ya vencidos
    
    from django.utils.timezone import now
    today = now().date()
    
    for lote in lotes_vigentes:
        dias = lote.dias_para_vencer()
        
        # Calcular información del lote
        lote_info = {
            'lote': lote,
            'producto': lote.producto,
            'dias_restantes': dias,
            'fecha_vencimiento': lote.fecha_vencimiento,
            'cantidad': lote.cantidad,
            'precio_unitario': lote.precio_unitario,
            'precio_unitario_fmt': formato_cop_signo(lote.precio_unitario),  # NUEVO
            'numero_lote': lote.numero_lote,
        }
        
        # Clasificar según días
        if dias <= 0:
            lotes_sin_alerta.append(lote_info)
        elif dias <= 7:
            alertas_criticas.append(lote_info)
        elif dias <= 14:
            alertas_altas.append(lote_info)
        elif dias <= 30:
            alertas_medias.append(lote_info)
        else:
            alertas_bajas.append(lote_info)
    
    # Estadísticas
    total_alertas = len(alertas_criticas) + len(alertas_altas) + len(alertas_medias) + len(alertas_bajas)
    
    context = {
        'alertas_criticas': alertas_criticas,
        'alertas_altas': alertas_altas,
        'alertas_medias': alertas_medias,
        'alertas_bajas': alertas_bajas,
        'total_alertas': total_alertas,
        'total_criticas': len(alertas_criticas),
        'total_altas': len(alertas_altas),
        'total_medias': len(alertas_medias),
        'total_bajas': len(alertas_bajas),
        'lotes_vencidos': len(lotes_sin_alerta),
        'formato_cop_signo': formato_cop_signo,  # NUEVO
    }
    
    return render(request, 'productos/alertas_lotes.html', context)
```

---

## alertas_lotes.html - Template

### Modal corregido:

**ANTES:**
```html
<div id="modalLimpiar" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;align-items:center;justify-content:center;">
    <div style="background:#1a1a1a;border-radius:8px;padding:30px;max-width:400px;color:#fff;">
        <form method="POST" action="{% url 'limpiar_alertas' %}" style="display:grid;gap:10px;">
            {% csrf_token %}
            <input type="hidden" name="confirmacion" value="no" id="confirmacion">
            <button type="button" onclick="confirmarLimpiar()" ...>
                Sí, eliminar todas
            </button>
```

**DESPUÉS:**
```html
<div id="modalLimpiar" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;align-items:center;justify-content:center;flex-direction:column;">
    <div style="background:#1a1a1a;border-radius:8px;padding:30px;max-width:400px;color:#fff;">
        <form method="POST" action="{% url 'limpiar_alertas' %}" id="formLimpiar" style="display:grid;gap:10px;">
            {% csrf_token %}
            <input type="hidden" name="confirmacion" value="no" id="confirmacion">
            <button type="submit" onclick="confirmarLimpiar(event)" ...>
                Sí, eliminar todas
            </button>
```

### JavaScript actualizado:

**ANTES:**
```javascript
function confirmarLimpiar() {
    document.getElementById('confirmacion').value = 'si';
    document.querySelector('form').submit();
}
```

**DESPUÉS:**
```javascript
function confirmarLimpiar(event) {
    if(event) event.preventDefault();
    document.getElementById('confirmacion').value = 'si';
    document.getElementById('formLimpiar').submit();
}
```

### Precios actualizados (4 lugares):

**TODAS ESTAS LÍNEAS:**
```html
<p>${{ alerta.precio_unitario }}</p>
```

**REEMPLAZADAS POR:**
```html
<p>{{ alerta.precio_unitario_fmt }}</p>
```

---

## detalle_producto.html - Template

### Precios en header:

**ANTES:**
```html
<p style="color:#fff;font-size:1.1rem;font-weight:bold;margin:5px 0 0;">${{ producto.precio_costo }}</p>
<p style="color:#fff;font-size:1.1rem;font-weight:bold;margin:5px 0 0;">${{ producto.precio_venta }}</p>
```

**DESPUÉS:**
```html
<p style="color:#fff;font-size:1.1rem;font-weight:bold;margin:5px 0 0;">{{ precio_costo_fmt }}</p>
<p style="color:#fff;font-size:1.1rem;font-weight:bold;margin:5px 0 0;">{{ precio_venta_fmt }}</p>
```

### Precio en tabla de lotes:

**ANTES:**
```html
<td style="padding:12px;color:#fff;">
    ${{ lote.precio_unitario }}
</td>
```

**DESPUÉS:**
```html
<td style="padding:12px;color:#fff;">
    $ {{ lote.precio_unitario|floatformat:0 }} COP
</td>
```

---

## Línea Temporal de Implementación

```
1. Modelos (models.py)
   └─ Agregar: tiene_lotes_vigentes()
   └─ Agregar: esta_vencido()

2. Vistas (views.py)
   └─ Importar: formato_cop_signo
   └─ Actualizar: agregar_carrito() - validación vencimiento
   └─ Actualizar: detalle_producto() - precios formateados
   └─ Actualizar: alertas_lotes_prox_vencer() - precios formateados

3. Templates
   └─ alertas_lotes.html - corregir modal + precios
   └─ detalle_producto.html - precios COP
```

---

## Verificación Rápida

```bash
# Verificar modelo Producto tiene métodos
grep -n "def esta_vencido" productos/models.py

# Verificar vista valida vencimiento
grep -n "if producto.esta_vencido" productos/views.py

# Verificar imports de formato
grep -n "formato_cop_signo" productos/views.py

# Verificar template modal tiene ID
grep -n "id=\"formLimpiar\"" productos/templates/productos/alertas_lotes.html

# Verificar precios formateados
grep -n "precio_unitario_fmt" productos/templates/productos/alertas_lotes.html
```

