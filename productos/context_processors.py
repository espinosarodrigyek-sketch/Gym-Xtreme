def carrito_total(request):
    carrito = request.session.get('carrito', {})
    total = sum(item['cantidad'] for item in carrito.values())
    return {'carrito_total': total}