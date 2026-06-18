from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class LoginForm(forms.Form):
    """Formulario de inicio de sesión personalizado."""

    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))


class CustomUserCreationForm(UserCreationForm):
    """Formulario de creación de usuario personalizado que incluye campos adicionales."""

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ("tipo_usuario", "dni", "telefono", "first_name", "last_name")
        widgets = {
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        }

        def __init__(self, *args, **kwargs):
            """Personaliza los campos del formulario para que tengan clases CSS y placeholders."""
            super().__init__(*args, **kwargs)
            for field_name in self.fields:
                field = self.fields[field_name]
                if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.PasswordInput):
                    field.widget.attrs['class'] = 'form-control'
                    field.widget.attrs['placeholder'] = field.labels

        
