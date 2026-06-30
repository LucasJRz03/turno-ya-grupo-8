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

    @classmethod
    def validate(cls, username, email, tipo_usuario, exclude_pk=None):
        """Valida los datos del usuario. Retorna una lista de errores."""
        errors = []
        
        # 1. Validar username
        username_limpio = str(username).strip() if username else ""
        if not username_limpio:
            errors.append("El nombre de usuario es obligatorio.")
        elif len(username_limpio) < 4:
            errors.append("El nombre de usuario debe tener al menos 4 caracteres.")
        else:
            qs_user = cls.objects.filter(username=username_limpio)
            if exclude_pk:
                qs_user = qs_user.exclude(pk=exclude_pk)
            if qs_user.exists():
                errors.append("Ya existe un usuario con ese nombre de usuario.")

        # 2. Validar email
        email_limpio = str(email).strip() if email else ""
        if not email_limpio:
            errors.append("El email es obligatorio.")
        else:
            try:
                validate_email(email_limpio)
            except ValidationError:
                errors.append("El formato del email no es válido.")
            else:
                qs_email = cls.objects.filter(email=email_limpio)
                if exclude_pk:
                    qs_email = qs_email.exclude(pk=exclude_pk)
                if qs_email.exists():
                    errors.append("Ya existe un usuario con ese email.")

        # 3. Validar tipo_usuario
        if tipo_usuario not in dict(cls.TIPOS_USUARIO):
            errors.append("El tipo de usuario no es válido.")

        return errors
    
    @classmethod
    def new(cls, username, email, password, tipo_usuario='paciente', first_name='', last_name=''):
        """Crea un nuevo usuario si los datos son válidos."""

        errors = cls.validate(username, email, tipo_usuario)
        if errors:
            return None, errors
        
        user = cls(
            username=username,
            email=email,
            tipo_usuario=tipo_usuario,
            first_name=first_name,
            last_name=last_name,
        )

        #Hasheo de contraseña
        user.set_password(password)
        user.save()
        return user, []
    
    def update(self, **kwargs):
        """Actualiza los datos del usuario si son válidos."""

        datos_futuros = {
            "username": self.username,
            "email": self.email, 
            "first_name": self.first_name, 
            "last_name": self.last_name, 
            "tipo_usuario": self.tipo_usuario
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(
            username=datos_futuros["username"],
            email=datos_futuros["email"],
            tipo_usuario=datos_futuros["tipo_usuario"],
            exclude_pk=self.pk
        )
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save()
        return []