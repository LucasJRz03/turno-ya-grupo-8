"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from unfold.admin import ModelAdmin 
from .models import Medico, Especialidad, Paciente, Turno


@admin.register(Especialidad)
class EspecialidadAdmin(ModelAdmin):
    list_display = ( "nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ("get_apellido", "get_nombre", "matricula", "especialidad")
    search_fields = ("usuario__last_name", "usuario__first_name", "matricula")
    list_filter = ("especialidad",)
    ordering = ("usuario__last_name", "usuario__first_name")

    @admin.display(description='Apellido', ordering='usuario__last_name')
    def get_apellido(self, obj):
        return obj.usuario.last_name if obj.usuario else "-"

    @admin.display(description='Nombre', ordering='usuario__first_name')
    def get_nombre(self, obj):
        return obj.usuario.first_name if obj.usuario else "-"

@admin.register(Paciente)
class PacienteAdmin(ModelAdmin):
    list_display = ("get_apellido", "get_nombre", "dni", "get_email", "telefono")
    search_fields = ("usuario__last_name", "usuario__first_name", "dni")

    @admin.display(description='Apellido', ordering='usuario__last_name')
    def get_apellido(self, obj):
        return obj.usuario.last_name if obj.usuario else "-"

    @admin.display(description='Nombre', ordering='usuario__first_name')
    def get_nombre(self, obj):
        return obj.usuario.first_name if obj.usuario else "-"

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.usuario.email if obj.usuario else "-"

@admin.register(Turno)
class TurnoAdmin(ModelAdmin):
    list_display = ("fecha_hora", "medico", "paciente","estado")
    list_filter = ("estado", "fecha_hora", "medico")
    search_fields = ("paciente__usuario__last_name", "paciente__dni","medico__usuario__last_name", "motivo")
    date_hierarchy = "fecha_hora"