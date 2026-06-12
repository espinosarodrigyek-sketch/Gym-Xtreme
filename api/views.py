from django.http import JsonResponse
from .frases import obtener_frase_motivacional


def frase_motivacional(request):
    """API ligera para obtener una frase motivacional aleatoria."""
    return JsonResponse(obtener_frase_motivacional())