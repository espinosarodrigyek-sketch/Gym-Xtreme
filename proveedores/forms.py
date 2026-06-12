from django import forms
from .models import Proveedor, Devolucion
from productos.models import Producto


class ProveedorForm(forms.ModelForm):
    """Formulario para crear/editar proveedores"""
    
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'email', 'direccion', 'ciudad', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del proveedor'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Teléfono de contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'correo@ejemplo.com'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Dirección del proveedor'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ciudad'
            }),
            'estado': forms.Select(attrs={'class': 'form-input'}),
        }


class ProveedorProductoForm(forms.Form):
    """Formulario para seleccionar productos que provee el proveedor"""
    productos = forms.ModelMultipleChoiceField(
        queryset=Producto.objects.filter(estado='activo'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Productos que provee este proveedor'
    )


class DevolucionForm(forms.ModelForm):
    """Formulario para crear devoluciones"""
    
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=True,
        label='Producto',
        empty_label="Seleccione un producto",
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'id_producto'
        })
    )
    
    class Meta:
        model = Devolucion
        fields = ['proveedor', 'producto', 'cantidad', 'motivo', 'descripcion', 'imagen', 'notas_admin']
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_proveedor'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'value': '1'
            }),
            'motivo': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_motivo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Describe el motivo de la devolución...'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'notas_admin': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Notas internas (opcional)'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            if cantidad <= 0:
                raise forms.ValidationError("La cantidad debe ser mayor a 0.")
            if cantidad > producto.stock_actual:
                raise forms.ValidationError(f"La cantidad solicitada ({cantidad}) excede el stock disponible ({producto.stock_actual}).")
        
        return cleaned_data