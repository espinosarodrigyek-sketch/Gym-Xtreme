import sys, os
with open('C:/gym_django/gym_django/gym_django/gym_dangoo (1)/gym_djangoo (1)/gym_django/gym/compras/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

insert_idx = 0
for i, line in enumerate(lines):
    if '@admin_required' in line and (i+1 < len(lines) and 'def reporte_compras_pdf' in lines[i+1]):
        insert_idx = i
        break

funcion = '''

@admin_required
def get_next_lote(request, producto_id):
    """API endpoint to get the next lot number for a product"""
    if request.method != "GET":
        from django.http import JsonResponse
        return JsonResponse({"success": False, "error": "Method not allowed"})
    
    try:
        from productos.models import Producto, Lote
        producto = Producto.objects.get(id_producto=producto_id)
    except Producto.DoesNotExist:
        from django.http import JsonResponse
        return JsonResponse({"success": False, "error": "Producto no encontrado"})
    
    ultimo_lote = Lote.objects.filter(producto=producto).order_by('-id_lote').first()
    
    if ultimo_lote:
        import re
        match = re.search(r'(\\d+)$', ultimo_lote.numero_lote)
        if match:
            siguiente_numero = int(match.group(1)) + 1
            siguiente_lote = f"LOTE{siguiente_numero:03d}"
        else:
            siguiente_lote = "LOTE001"
    else:
        siguiente_lote = "LOTE001"
    
    from django.http import JsonResponse
    return JsonResponse({"success": True, "next_lote": siguiente_lote})

'''

nuevo = ''.join(lines[:insert_idx] + [funcion] + lines[insert_idx:])

with open('C:/gym_django/gym_django/gym_django/gym_dangoo (1)/gym_djangoo (1)/gym_django/gym/compras/views.py', 'w', encoding='utf-8') as f:
    f.write(nuevo)

print('Agregada get_next_lote')
