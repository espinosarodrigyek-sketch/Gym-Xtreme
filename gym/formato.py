"""Utilidades de formato de moneda colombiana"""


def formato_cop(valor):
    """Formatea un número como moneda colombiana: 100.000 COP"""
    try:
        num = float(valor)
        if num == int(num):
            formatted = f'{int(num):,}'.replace(',', '.')
        else:
            parts = f'{num:,.2f}'.split('.')
            formatted = parts[0].replace(',', '.') + ',' + parts[1]
        return f'{formatted} COP'
    except (ValueError, TypeError):
        return '0 COP'


def formato_cop_signo(valor):
    """Formatea un número como moneda colombiana con signo: $100.000"""
    try:
        num = float(valor)
        if num == int(num):
            formatted = f'{int(num):,}'.replace(',', '.')
        else:
            parts = f'{num:,.2f}'.split('.')
            formatted = parts[0].replace(',', '.') + ',' + parts[1]
        return f'$ {formatted}'
    except (ValueError, TypeError):
        return '$ 0'


def formato_cop_plain(valor):
    """Formatea un número como moneda colombiana: 100.000"""
    try:
        num = float(valor)
        if num == int(num):
            formatted = f'{int(num):,}'.replace(',', '.')
        else:
            parts = f'{num:,.2f}'.split('.')
            formatted = parts[0].replace(',', '.') + ',' + parts[1]
        return formatted
    except (ValueError, TypeError):
        return '0'
