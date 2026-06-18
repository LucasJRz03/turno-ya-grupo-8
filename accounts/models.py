from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Modelo de usuario personalizado para futuras extensiones."""

    TIPOS_USUARIO = [
        ('paciente', 'Paciente'),
        ('medico', 'Médico'),
        ('admin', 'Administrador'),
    ]

    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='paciente', help_text="Tipo de usuario: paciente, médico o administrador.")
    dni= models.CharField(max_length=20, blank=True, help_text="DNI del usuario")
    telefono = models.CharField(max_length=20, blank=True, help_text="Número de teléfono del usuario")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-fecha_creacion']

    def __str__(self):
        """Representación legible del usuario, mostrando su nombre de usuario y tipo de usuario."""
        return f"{self.username} ({self.get_tipo_usuario_display()})"

    def nombre_completo(self):
        """Devuelve el nombre completo del usuario, combinando su nombre y apellido."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def es_paciente(self):
        """Indica si el usuario es un paciente."""
        return self.tipo_usuario == 'paciente'
    
    def es_medico(self):
        """Indica si el usuario es un médico."""
        return self.tipo_usuario == 'medico'    
    
    def es_admin(self):
        """Indica si el usuario es un administrador."""
        return self.tipo_usuario == 'admin'     

