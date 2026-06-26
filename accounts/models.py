from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    """Modelo de usuario personalizado
    Solo contiene datos de autenticacion y rol"""

    TIPOS_USUARIO = [
        ('paciente', 'Paciente'),
        ('medico', 'Médico'),
        ('admin', 'Administrador'),
    ]

    #Campos

    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='paciente', help_text="Tipo de usuario: paciente, médico o administrador.")
    email= models.EmailField(unique=True, help_text="Email del Usuario")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-fecha_creacion']

    def __str__(self):
        """Representación legible del usuario"""
        return f"{self.username} ({self.get_tipo_usuario_display()})"
    
    #Propiedades

    @property
    def es_paciente(self):
        """Indica si el usuario es un paciente."""
        return self.tipo_usuario == 'paciente'
    
    @property
    def es_medico(self):
        """Indica si el usuario es un médico."""
        return self.tipo_usuario == 'medico'
    
    @property
    def es_admin(self):
        """Indica si el usuario es un administrador."""
        return self.tipo_usuario == 'admin'     

    def nombre_completo(self):
        """Devuelve el nombre completo, si esta vacio, retorna el username"""
        nombre = f"{self.first_name} {self.last_name}".strip()
        return nombre if nombre else self.username
    
    #Patron validate/new/update

    def validate(self):
        """Valida los datos del usuario."""

        errors = []

        # Validar username
        if not self.username or not self.username.strip():
            errors.append("El nombre de usuario es obligatorio.")
        elif len(self.username) < 4:
            errors.append("El nombre de usuario debe tener al menos 4 caracteres.")
        else:
            # Verificar unicidad del username
            qs_user = CustomUser.objects.filter(username=self.username)
            if self.pk:
                qs_user = qs_user.exclude(pk=self.pk)
            if qs_user.exists():
                errors.append("Ya existe un usuario con ese nombre de usuario.")

        # Validar email
        if not self.email or not self.email.strip():
            errors.append("El email es obligatorio.")
        else:
            try:
                validate_email(self.email)
            except ValidationError:
                errors.append("El formato del email no es válido.")
            else:
                # Verificar unicidad del email
                qs_email = CustomUser.objects.filter(email=self.email)
                if self.pk:
                    qs_email = qs_email.exclude(pk=self.pk)
                if qs_email.exists():
                    errors.append("Ya existe un usuario con ese email.")

        # Validar tipo_usuario
        if self.tipo_usuario not in dict(self.TIPOS_USUARIO):
            errors.append("El tipo de usuario no es válido.")

        return errors
    
    @classmethod
    def new(cls, username, email, password, tipo_usuario='paciente', first_name='', last_name=''):
        """Crea un nuevo usuario si los datos son válidos."""
        user = cls(
            username=username,
            email=email,
            tipo_usuario=tipo_usuario,
            first_name=first_name,
            last_name=last_name,
        )
        errors = user.validate()
        if errors:
            return None, errors
        #Hasheo de contraseña
        user.set_password(password)
        user.save()
        return user, []
    
    def update(self, email=None, first_name=None, last_name=None, tipo_usuario=None):
        """Actualiza los datos del usuario. """
        if email is not None:
            self.email = email
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if tipo_usuario is not None:
            self.tipo_usuario = tipo_usuario

        errors = self.validate()
        if errors:
            return errors
        
        self.save()
        return []
            