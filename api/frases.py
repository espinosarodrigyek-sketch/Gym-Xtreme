"""
API de frases motivacionales externas.
Obtiene frases de APIs públicas y las traduce al español.
"""
import logging
import random
import requests
from functools import lru_cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

_SESSION = requests.Session()


@lru_cache(maxsize=16)
def _frase_fallback_cache():
    """Cache pequeño para respuestas de fallback sin recalcular listas."""
    return [
        {"frase": "El único entrenamiento malo es el que no haces.", "autor": "Anónimo"},
        {"frase": "La disciplina es el puente entre tus metas y tus logros.", "autor": "Jim Rohn"},
        {"frase": "Tu límite está en tu mente. Supérate cada día.", "autor": "Anónimo"},
        {"frase": "La fuerza no viene de lo físico, viene de la voluntad.", "autor": "Bruce Lee"},
        {"frase": "El éxito no es la meta, es el camino que recorres.", "autor": "Anónimo"},
    ]


def obtener_frase_motivacional():
    """
    Obtiene una frase motivacional en español desde APIs externas.
    Flujo: obtener frase en inglés de API de frases → traducir al español → retornar
    
    Returns:
        dict: {'frase': 'texto', 'autor': 'autor'}
    """
    try:
        frase_ingles = obtener_frase_api()
        frase_espanol = traducir_frase(frase_ingles['frase'])
        
        return {
            'frase': frase_espanol,
            'autor': frase_ingles['autor']
        }
    except Exception as e:
        logger.error(f"Error al obtener frase de APIs: {e}")
        return obtener_frase_fallback()


def obtener_frase_api():
    """
    Consume API externa de frases motivacionales (ZenQuotes, StoicQuotes, Quotable).
    
    Returns:
        dict: {'frase': 'texto en ingles', 'autor': 'autor'}
    """
    import time
    import hashlib
    
    random_param = str(time.time())[:10]
    
    apis = [
        {
            'url': 'https://zenquotes.io/api/random',
            'parser': lambda r: {'frase': r[0]['q'], 'autor': r[0]['a']}
        },
        {
            'url': 'https://stoicquotes.azurewebsites.net/api/quotes/random',
            'parser': lambda r: {'frase': r['text'], 'autor': r['author']}
        },
        {
            'url': f'https://api.quotable.io/random?tags=motivational',
            'parser': lambda r: {'frase': r['content'], 'autor': r['author']}
        },
        {
            'url': f'https://api.quotable.io/random?tags=inspirational',
            'parser': lambda r: {'frase': r['content'], 'autor': r['author']}
        },
        {
            'url': f'https://api.quotable.io/random?tags=success',
            'parser': lambda r: {'frase': r['content'], 'autor': r['author']}
        }
    ]
    
    random.shuffle(apis)
    
    for api in apis:
        try:
            response = _SESSION.get(api['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                return api['parser'](data)
        except Exception as e:
            logger.warning(f"API {api['url']} falló: {e}")
            continue
    
    raise Exception("Todas las APIs de frases fallaron")


def traducir_frase(texto):
    """
    Traduce texto de inglés a español usando API de traducción.
    
    Args:
        texto: Texto en inglés a traducir
        
    Returns:
        str: Texto traducido al español
    """
    apis_traduccion = [
        {
            'url': 'https://api.mymemory.translated.net/get',
            'params': {'q': texto, 'langpair': 'en|es'},
            'parser': lambda r: r['responseData']['translatedText']
        }
    ]
    
    for api in apis_traduccion:
        try:
            response = _SESSION.get(api['url'], params=api['params'], timeout=5)
            
            if response.status_code == 200:
                resultado = api['parser'](response.json())
                if resultado and len(resultado) > 5:
                    return resultado
        except Exception as e:
            logger.warning(f"API de traducción falló: {e}")
            continue
    
    raise Exception("Todas las APIs de traducción fallaron")


def obtener_frase_fallback():
    """
    Frase de fallback por si fallan todas las APIs.
    
    Returns:
        dict: {'frase': 'texto', 'autor': 'autor'}
    """
    return random.choice(_frase_fallback_cache())


def frase_api_view(request):
    """View Django para endpoint de frases - visible en navegador"""
    frase = obtener_frase_motivacional()
    return JsonResponse({
        'success': True,
        'frase': frase['frase'],
        'autor': frase['autor'],
        'fuente': 'API Externa (ZenQuotes/Quotable)',
        'traduccion': 'MyMemory API'
    })