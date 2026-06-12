from django import forms
from .models import Venta
from django.utils.timezone import now
from datetime import datetime


class VentaForm(forms.ModelForm):
    """Formulario para crear/editar ventas con fecha manual"""
    
    fecha = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control tarjeta-input',
                'style': 'padding: 15px 18px; font-size: 1.1rem; border: 2px solid #333; border-radius: 12px; background: #0a0a0a; color: white;',
            }
        ),
        required=True,
        label='Fecha de la Venta',
        help_text='Selecciona la fecha y hora de la venta',
    )
    
    class Meta:
        model = Venta
        fields = ['fecha', 'metodo_pago', 'estado', 'notas']
        widgets = {
            'metodo_pago': forms.Select(attrs={
                'class': 'form-control tarjeta-input',
                'style': 'padding: 15px 18px; font-size: 1.1rem; border: 2px solid #333; border-radius: 12px; background: #0a0a0a; color: white;',
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control tarjeta-input',
                'style': 'padding: 15px 18px; font-size: 1.1rem; border: 2px solid #333; border-radius: 12px; background: #0a0a0a; color: white;',
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control tarjeta-input',
                'rows': 4,
                'placeholder': 'Notas adicionales (opcional)',
                'style': 'padding: 15px 18px; font-size: 1.1rem; border: 2px solid #333; border-radius: 12px; background: #0a0a0a; color: white;',
            }),
        }
        labels = {
            'fecha': 'Fecha de la Venta',
            'metodo_pago': 'Método de Pago',
            'estado': 'Estado de la Venta',
            'notas': 'Notas',
        }


class FechaVentaForm(forms.Form):
    """Formulario simple para seleccionar solo la fecha de la venta en pago"""
    
    fecha = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control tarjeta-input',
                'style': 'padding: 15px 18px; font-size: 1.1rem; border: 2px solid #333; border-radius: 12px; background: #0a0a0a; color: white;',
            }
        ),
        required=True,
        label='Fecha de la Venta',
        initial=datetime.now,
    )


class FiltroVentasForm(forms.Form):
    """Formulario para filtrar ventas en lista_ventas"""
    
    id_venta = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                'type': 'number',
                'class': 'form-input',
                'placeholder': 'ID Venta',
            }
        )
    )
    
    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-input',
            }
        )
    )
    
    total_min = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                'type': 'number',
                'class': 'form-input',
                'placeholder': 'Total min',
                'step': '0.01',
            }
        )
    )
    
    total_max = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                'type': 'number',
                'class': 'form-input',
                'placeholder': 'Total max',
                'step': '0.01',
            }
        )
    )
