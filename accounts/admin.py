# accounts/admin.py
"""Configuración del admin para el modelo CustomUser."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    """Administrador personalizado para CustomUser."""

    # Lista (tabla principal)
    list_display = ('username', 'email', 'nombre_completo', 'tipo_usuario', 'is_active', 'fecha_creacion',)
    # Filtros laterales
    list_filter = ('tipo_usuario', 'is_active', 'is_staff', 'is_superuser', 'date_joined',)
    # Búsqueda
    search_fields = ('username', 'email', 'first_name', 'last_name',)

    # Ordenamiento por defecto
    ordering = ('-fecha_creacion',)
    # Edición inline del tipo de usuario desde la lista
    list_editable = ('tipo_usuario',)
    # Navegación por fecha (barra superior)
    date_hierarchy = 'fecha_creacion'

    # FORMULARIO DE EDICIÓN
    fieldsets = (
        (None, {'fields': ('username', 'password'),}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email'),}),
        ('Rol en el sistema', {'fields': ('tipo_usuario',), 'description': 'Define qué tipo de usuario es: paciente, médico o administrador.',}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',),}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined', 'fecha_creacion'),}),
    )

    # FORMULARIO DE CREACIÓN
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'tipo_usuario',
                'is_active',
                'is_staff',
            ),
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('last_login', 'date_joined', 'fecha_creacion')
