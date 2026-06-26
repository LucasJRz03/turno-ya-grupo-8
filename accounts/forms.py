from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import CustomUser

class LoginForm(AuthenticationForm):
    """Formulario de login basado en AuthenticationForm"""

    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario', "autofocus":True,}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))

class CustomUserCreationForm(UserCreationForm):
    """Formulario de registro simplicado"""

    email= forms.EmailField(required=True, label="Correo eletronico", widget=forms.EmailInput(attrs={'class':'form-control', 'placeholder': 'example@email.com',}))
    class Meta(UserCreationForm.Meta):

        model = CustomUser
        fields = ['username', 'email']
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Aplica bootstrap a los campos
            for field_name, field in self.fields.items():
                if isinstance(field.widget, (forms.TextInput, forms.PasswordInput, forms.EmailInput)):
                    field.widget.attrs.setdefault('class', 'form-control')

            #Placeholders para contraseñas
            self.fields['password1'].widget.attrs['placeholder'] = 'Contraseña'
            self.fields['password2'].widget.attrs['placeholder'] = 'Confirmar contraseña'
            self.fields['username'].widget.attrs['placeholder'] = 'Nombre de usuario'

        def clean_email(self):
            """Validación: email único y formato válido."""
            email = self.cleaned_data.get('email', '').strip()

            if not email:
                raise forms.ValidationError("El email es obligatorio.")

            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError("El formato del email no es válido.")

            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("Ya existe un usuario con ese email.")

            return email
        
        def clean_username(self):
            """Validación: username mínimo 4 caracteres"""
            username = self.cleaned_data.get('username', '').strip()
            if len(username) < 4:
                raise forms.ValidationError("El nombre de usuario debe tener al menos 4 caracteres.")
            return username
class PerfilForm(forms.ModelForm):
    """Formulario para editar el perfil del usuario."""
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido',
            }),
        }

    def clean_email(self):
        """Validación: email único excluyendo el propio."""
        email = self.cleaned_data.get('email', '').strip()

        if not email:
            raise forms.ValidationError("El email es obligatorio.")

        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("El formato del email no es válido.")

        qs = CustomUser.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe otro usuario con ese email.")

        return email

    def clean_first_name(self):
        """Validación: nombre obligatorio."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError("El nombre es obligatorio.")
        return first_name

        
