# Sistema de Gestión de Gimnasio - Django

## Descripción
Sistema integral para la administración de un gimnasio con módulos de clientes, planes, productos, proveedores, maquinaria y economía.

## Características

### Módulos
- **Clientes**: Gestión de clientes con suscripciones, historial de peso, metas
- **Planes**: Planes de membresía (diario, mensual, trimestral, semestral, anual)
- **Productos**: Inventario de suplementos y accesorios
- **Proveedores**: Gestión de proveedores con devoluciones
- **Maquinaria**: Control de equipos del gimnasio vinculados a proveedores
- **Compras**: Registro de compras a proveedores con detalles
- **Economía**: Dashboard con gráficos de ingresos y gastos

### Funcionalidades
- Carga masiva desde CSV
- Exportación a PDF y Excel
- Gráficos interactivos con Chart.js
- Sistema de notificaciones
- Frases motivacionales (1000+ frases únicas)
- Limpieza de datos en cada módulo
- Diseño tema gimnasionio (rojo, negro, blanco)

## Estructura de CSV para carga masiva

| Archivo | Descripción |
|---------|-------------|
| `usuarios.csv` | username,email,password,first_name,last_name,rol,telefono,direccion |
| `productos.csv` | nombre,descripcion,categoria,precio_costo,precio_venta,stock_actual,estado,imagen |
| `planes.csv` | nombre,tipo,precio,descripcion,duracion_dias,imagen |
| `proveedores.csv` | nombre,telefono,email,direccion,ciudad,estado |
| `maquinaria.csv` | nombre,descripcion,tipo,ubicacion,estado,precio_compra,fecha_compra,imagen |
| `compras.csv` | proveedor,producto,cantidad,precio_unitario,estado,notas |
| `ventas.csv` | username,plan,precio,dias |
| `maquinaria_proveedor.csv` | nombre_maquina,nombre_proveedor,precio_venta |
| `productos_maquina.csv` | nombre_producto,nombre_maquina |

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Cargar datos (opcional)
python manage.py cargar_datos --todo csv_datos

# Cargar frases motivacionales
python manage.py cargar_frases

# Ejecutar servidor
python manage.py runserver
```

## Comandos útiles

```bash
# Cargar datos masivos
python manage.py cargar_datos --todo /ruta/csv

# Cargar frases motivacionales
python manage.py cargar_frases

# Eliminar todos los datos
python manage.py eliminar_datos

# Respaldar base de datos
python manage.py backup_db

# Ejecutar tests
python manage.py test gym.tests
```

## Rutas principales

| Ruta | Descripción |
|------|-------------|
| `/admin-panel/` | Dashboard principal |
| `/panel/clientes/` | Lista de clientes |
| `/admin-panel/planes/` | Gestión de planes |
| `/productos/` | Inventario de productos |
| `/proveedores/` | Lista de proveedores |
| `/compras/` | Registro de compras |
| `/maquinaria/` | Equipos del gimnasio |
| `/admin-panel/economia/` | Dashboard económico |

## Tecnologías

- Django 4.2
- Bootstrap 5.3
- Chart.js
- MariaDB/MySQL
- xhtml2pdf (PDF)
- Python 3.14

## Licencia
Privado - Uso interno
