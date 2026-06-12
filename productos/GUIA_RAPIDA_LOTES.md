# 🚀 Guía Rápida - Sistema de Gestión de Lotes

## ⚡ Inicio Rápido

### 1. Aplicar Migraciones (REQUERIDO)
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Acceder al Sistema

**Opción A: Desde la Lista de Productos**
```
1. Ir a /productos/
2. En la tabla, hacer clic en el botón 🟦 "Ver Lotes" para cualquier producto
3. O hacer clic en "Alertas de Lotes" en la esquina superior derecha
```

**Opción B: URLs Directas**
```
- Ver lotes de producto ID 5: /productos/5/detalle/
- Ver todas las alertas: /productos/lotes/alertas/
```

## 📊 Funcionalidades Principales

### 🔍 Ver Lotes de un Producto
**Ruta:** `/productos/<id>/detalle/`

```
Mostrará:
- Información del producto (nombre, categoría, precios)
- Estadísticas: Total lotes, Disponibles, Stock, Vencidos
- Tabla con todos los lotes:
  - Número de lote (LOTE001, LOTE002, etc.)
  - Cantidad de unidades
  - Precio unitario
  - Fechas: compra, fabricación, vencimiento
  - Días para vencer
  - Estado (Disponible, Agotado, Vencido)
```

### 🚨 Dashboard de Alertas
**Ruta:** `/productos/lotes/alertas/`

```
Funcionalidades:
- Cuenta de alertas: Total, No leídas, Críticas
- Filtros por nivel: Todas, Críticas, Altas, Medias, Bajas
- Tarjetas de alertas con:
  - Nivel (🔴🟠🟡🔵)
  - Título y descripción del lote
  - Info: Producto, Lote, Vencimiento, Cantidad, Precio
  - Botones: Marcar leída, Desactivar, Ver producto

Niveles de Alerta:
🔴 CRÍTICO: Vence en 0-3 días
🟠 ALTO: Vence en 4-7 días
🟡 MEDIO: Vence en 8-14 días
🔵 BAJO: Información general
```

## 🔌 APIs REST

### Obtener Lotes de un Producto (JSON)
```
GET /productos/api/lotes/123/

Respuesta:
{
  "success": true,
  "producto": {
    "id": 123,
    "nombre": "Proteína Whey",
    "stock_actual": 150
  },
  "lotes": [
    {
      "id": 1,
      "numero_lote": "LOTE001",
      "cantidad": 50,
      "precio_unitario": "8500.00",
      "fecha_compra": "15/04/2025",
      "fecha_fabricacion": "01/03/2025",
      "fecha_vencimiento": "01/03/2026",
      "estado": "disponible",
      "dias_para_vencer": 340,
      "esta_vencido": false
    }
  ],
  "total_lotes": 3
}
```

### Obtener Todas las Alertas (JSON)
```
GET /productos/api/alertas-lotes/

Respuesta:
{
  "success": true,
  "alertas": [
    {
      "id": 1,
      "nivel": "critico",
      "titulo": "⚠️ CRÍTICO: Lote LOTE005 vence en 2 día(s)",
      "producto": "Proteína Whey",
      "lote": "LOTE005",
      "dias_para_vencer": 2,
      "fecha_vencimiento": "28/04/2025",
      "cantidad": 10,
      "leida": false
    }
  ],
  "total": 5,
  "no_leidas": 3,
  "criticas": 1
}
```

## ⚙️ Comandos Administrativos

### Generar Alertas Automáticas
```bash
# Con parámetros por defecto
python manage.py generar_alertas_lotes

# Salida:
# ✓ Se generaron 5 alertas automáticas

# Con parámetros personalizados
python manage.py generar_alertas_lotes \
  --dias-critico 2 \
  --dias-alto 5 \
  --dias-medio 10

# Parámetros:
# --dias-critico: Días para nivel crítico (default: 3)
# --dias-alto: Días para nivel alto (default: 7)
# --dias-medio: Días para nivel medio (default: 14)
```

## 🎯 Casos de Uso Prácticos

### Caso 1: Revisar qué productos vencen pronto
```
1. Ir a /productos/lotes/alertas/
2. Ver las alertas críticas (🔴)
3. Hacer clic en "Ver" para abrir detalles del producto
4. Planear acciones: promociones, liquidación, etc.
```

### Caso 2: Consultar lotes específicos de un producto
```
1. Ir a /productos/
2. Buscar producto en la lista
3. Clic en 🟦 "Ver Lotes"
4. Se muestra:
   - Información completa del producto
   - Tabla con todos los lotes y sus estados
   - Resumen de estadísticas
```

### Caso 3: Usar API en aplicación externa
```javascript
// En tu app frontend
async function obtenerLotes(productoId) {
  const response = await fetch(`/productos/api/lotes/${productoId}/`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`Producto: ${data.producto.nombre}`);
    console.log(`Lotes disponibles: ${data.lotes.length}`);
    
    data.lotes.forEach(lote => {
      console.log(`${lote.numero_lote}: ${lote.cantidad} uds - Vence ${lote.fecha_vencimiento}`);
    });
  }
}

// En tu app backend
async function verificarAlertasCriticas() {
  const response = await fetch('/productos/api/alertas-lotes/');
  const data = await response.json();
  
  if (data.criticas > 0) {
    console.log(`⚠️ ALERTA: ${data.criticas} lotes críticos!`);
  }
}
```

## 🔐 Panel Admin Django

Acceso completo en `/admin/productos/`

### Gestión de Lotes
```
/admin/productos/lote/

Acciones:
- Ver todos los lotes
- Buscar por número de lote o producto
- Filtrar por estado o fecha de vencimiento
- Editar cantidad o notas
- Ver campos readonly: número_lote, fecha_creación
```

### Gestión de Alertas
```
/admin/productos/alertalote/

Acciones:
- Ver todas las alertas
- Buscar por título o producto
- Filtrar por nivel o estado de lectura
- Marcar como activa/inactiva
- Ver historial de lecturas
```

## 📈 Estadísticas Útiles

En la vista de detalle del producto (`/productos/<id>/detalle/`):

```
Información visible:
┌─────────────────────────────────────────┐
│ Producto: Proteína Whey                 │
├─────────────────────────────────────────┤
│ Total Lotes: 5      Disponibles: 4      │
│ Stock Total: 150    Vencidos: 1         │
├─────────────────────────────────────────┤
│ Lotes:                                  │
│ LOTE001: 50 uds - Vence 01/03/2026     │
│ LOTE002: 30 uds - Vence 15/02/2026     │
│ LOTE003: 40 uds - Vence 20/05/2025     │
│ LOTE004: 20 uds - Vence 10/04/2025 🔴  │
│ LOTE005: 10 uds - VENCIDO ❌            │
└─────────────────────────────────────────┘
```

## 🆘 Preguntas Frecuentes

**P: ¿Cómo se crean los lotes?**
A: Automáticamente cuando se registra una compra en el módulo de compras.

**P: ¿Puedo editar un lote después de crearlo?**
A: Sí, desde el panel admin `/admin/productos/lote/` o desde la vista detalle_producto.

**P: ¿Qué pasa con los lotes vencidos?**
A: Se marcan automáticamente como "vencido" pero permanecen en el sistema para auditoría.

**P: ¿Cómo deshabilito las alertas para un lote?**
A: En la vista `/productos/lotes/alertas/`, haz clic en "Desactivar".

**P: ¿Se pueden exportar las alertas?**
A: Por ahora en JSON vía API. Futuras versiones incluirán PDF/CSV.

**P: ¿Es obligatorio poner el precio unitario?**
A: Sí, se registra automáticamente desde el precio de compra del detalle.

---

**Versión:** 1.0  
**Última actualización:** 26/04/2025  
**Desarrollador:** Django Expert
