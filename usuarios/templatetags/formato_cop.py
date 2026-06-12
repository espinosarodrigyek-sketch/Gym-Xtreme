from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def cop(value):
    """Formatea un número como moneda colombiana: 100.000 COP"""
    try:
        if value is None or value == '':
            return '0 COP'
        num = float(value)
        # Formatear con punto como separador de miles (formato colombiano)
        if num == int(num):
            formatted = f'{int(num):,}'.replace(',', '.')
        else:
            # Para decimales, formatear parte entera y decimal
            parts = f'{num:,.2f}'.split('.')
            formatted = parts[0].replace(',', '.') + ',' + parts[1]
        return f'{formatted} COP'
    except (ValueError, TypeError, InvalidOperation):
        return '0 COP'


@register.filter
def cop_raw(value):
    """Formatea un número con punto como separador de miles, sin 'COP'"""
    try:
        if value is None or value == '':
            return '0'
        num = float(value)
        if num == int(num):
            return f'{int(num):,}'.replace(',', '.')
        else:
            parts = f'{num:,.2f}'.split('.')
            return parts[0].replace(',', '.') + ',' + parts[1]
    except (ValueError, TypeError, InvalidOperation):
        return '0'


@register.filter
def cop_signo(value):
    """Formatea un número como moneda colombiana con signo $: $100.000 COP"""
    try:
        if value is None or value == '':
            return '$ 0 COP'
        num = float(value)
        if num == int(num):
            formatted = f'{int(num):,}'.replace(',', '.')
        else:
            parts = f'{num:,.2f}'.split('.')
            formatted = parts[0].replace(',', '.') + ',' + parts[1]
        return f'$ {formatted} COP'
    except (ValueError, TypeError, InvalidOperation):
        return '$ 0 COP'
