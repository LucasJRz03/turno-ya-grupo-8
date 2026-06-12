"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from .models import Medico, Especialidad, Paciente, Turno

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ( "nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "matricula", "especialidad")
    search_fields = ("apellido", "nombre", "matricula")
    list_filter = ("especialidad",)
    ordering = ("apellido", "nombre")

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("apellido", "nombre", "dni", "email", "telefono")
    search_fields = ("apellido", "nombre", "dni")

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "medico", "paciente","estado")
    list_filter = ("estado", "fecha_hora", "medico")
    search_fields = ("paciente__apellido", "paciente__dni","medico__apellido", "motivo")
    date_hierarchy = "fecha_hora"