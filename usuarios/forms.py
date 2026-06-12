from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from .models import Rutina, Ejercicio


def validar_contrasena(password):
    """
    Valida que la contraseña cumpla con los requisitos de seguridad.
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    errores = []

    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")

    if not re.search(r'[A-Z]', password):
        errores.append("La contraseña debe contener al menos una letra mayúscula.")

    if not re.search(r'[a-z]', password):
        errores.append("La contraseña debe contener al menos una letra minúscula.")

    if not re.search(r'[0-9]', password):
        errores.append("La contraseña debe contener al menos un número.")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-=+;/\'\\`~]', password):
        errores.append("La contraseña debe contener al menos un carácter especial (!@#$%^&*(), etc.).")

    # Contraseñas débiles comunes
    contrasenas_debiles = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'password1', 'password123', '123456789', 'letmein',
        'welcome', 'admin', 'iloveyou', '111111', '123123',
        'sunshine', 'princess', 'dragon', 'master', 'gym123',
        'gymxtreme', 'gimnasio', 'musculo', 'fitness', 'gym'
    ]
    if password.lower() in contrasenas_debiles:
        errores.append("La contraseña es demasiado común. Elige una más segura.")

    # Nombre de usuario no debe estar en la contraseña
    # (se validará después cuando se tenga el username)

    if errores:
        raise ValidationError(errores)

    return password


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión con validaciones de seguridad"""
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu usuario',
            'autocomplete': 'username',
            'maxlength': '150',
        }),
        required=True,
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña',
            'autocomplete': 'current-password',
            'maxlength': '128',
        }),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].strip = True

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Verificar si la cuenta está bloqueada por intentos fallidos
            from django.core.cache import cache
            cache_key = f'login_attempts_{username}'
            attempts = cache.get(cache_key, 0)

            if attempts >= 5:
                raise ValidationError(
                    "Tu cuenta está temporalmente bloqueada por múltiples intentos fallidos. "
                    "Inténtalo de nuevo en 15 minutos."
                )

        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if password:
            # Validar longitud mínima
            if len(password) < 8:
                raise ValidationError(
                    "La contraseña debe tener al menos 8 caracteres."
                )
        return password


class RegistroForm(forms.Form):
    """Formulario de registro con validaciones de seguridad"""
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Elige un nombre de usuario',
            'autocomplete': 'username',
            'maxlength': '150',
        }),
        required=True,
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email',
            'maxlength': '254',
        }),
        required=True,
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Crea una contraseña segura',
            'autocomplete': 'new-password',
            'maxlength': '128',
        }),
        required=True,
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña',
            'autocomplete': 'new-password',
            'maxlength': '128',
        }),
        required=True,
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        if len(username) < 3:
            raise ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        if len(username) > 150:
            raise ValidationError("El nombre de usuario no puede superar los 150 caracteres.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("El nombre de usuario solo puede contener letras, números y guiones bajos.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if password:
            validar_contrasena(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password', '')
        password_confirm = cleaned_data.get('password_confirm', '')

        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data


class RutinaForm(forms.ModelForm):
    """Formulario para crear y editar rutinas"""

    class Meta:
        fields = ['nombre', 'descripcion', 'nivel', 'duracion_dias', 'activa', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de la rutina'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Descripción de la rutina...'
            }),
            'nivel': forms.Select(attrs={'class': 'form-input'}),
            'duracion_dias': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'placeholder': 'Días'
            }),
            'activa': forms.CheckboxInput(attrs={
                'style': 'width:20px;height:20px;'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres")
        return nombre
    
    def clean_duracion_dias(self):
        duracion = self.cleaned_data.get('duracion_dias')
        if duracion and duracion < 1:
            raise forms.ValidationError("La duración debe ser al menos 1 día")
        return duracion


class EjercicioForm(forms.ModelForm):
    """Formulario para ejercicios individuales"""
    
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'descripcion', 'series', 'repeticiones', 'descanso', 'dia', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre del ejercicio'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 2,
                'placeholder': 'Instrucciones...'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'max': '20'
            }),
            'repeticiones': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: 10-12'
            }),
            'descanso': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'placeholder': 'Segundos'
            }),
            'dia': forms.Select(attrs={'class': 'form-input'}),
            'orden': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1'
            }),
        }


class EjercicioInlineForm(forms.ModelForm):
    """Formulario para ejercicios inline en el formulario de rutina"""
    
    class Meta:
        model = Ejercicio
        fields = ['nombre', 'descripcion', 'series', 'repeticiones', 'descanso', 'dia', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ejercicio'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Descripción'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:60px'
            }),
            'repeticiones': forms.TextInput(attrs={
                'class': 'form-input',
                'style': 'width:80px',
                'placeholder': '10-12'
            }),
            'descanso': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:60px',
                'placeholder': '60s'
            }),
            'dia': forms.Select(attrs={
                'class': 'form-input',
                'style': 'width:120px'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-input',
                'style': 'width:50px'
            }),
        }
