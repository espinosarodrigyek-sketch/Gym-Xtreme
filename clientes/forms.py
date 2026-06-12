from django import forms
from usuarios.models import Suscripcion


class SuscripcionForm(forms.ModelForm):

    class Meta:
        model = Suscripcion
        fields = ['usuario', 'plan', 'activa']