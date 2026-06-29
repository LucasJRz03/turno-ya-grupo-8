"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from unfold.admin import ModelAdmin 
from .models import Medico, Especialidad, Paciente, Turno, ObraSocial, Ausencia


@admin.register(Especialidad)
class EspecialidadAdmin(ModelAdmin):
    list_display = ( "nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Medico)
class MedicoAdmin(ModelAdmin):
    list_display = ("apellido", "nombre", "matricula", "especialidad")
    search_fields = ("apellido", "nombre", "matricula")
    list_filter = ("especialidad",)
    ordering = ("apellido", "nombre")

    # Customización para el formulario. Agrupa los campos en secciones visuales.
    fieldsets = (
        ("Información Personal", {
            "fields": ("nombre", "apellido", "usuario")
        }),
        ("Información Profesional", {
            "fields": ("matricula", "especialidad")
        })
    )

@admin.register(Paciente)
class PacienteAdmin(ModelAdmin):
    list_display = ("apellido", "nombre", "dni", "email", "telefono")
    search_fields = ("apellido", "nombre", "dni")
    
    fieldsets = (
        ("Datos Identificatorios",{
            "fields": ("nombre", "apellido", "dni", "usuario")
        }),
        ("información de Contacto", {
            "fields": ("email", "telefono")
        }),
    )

@admin.register(Turno)
class TurnoAdmin(ModelAdmin):
    list_display = ("fecha_hora", "medico", "paciente","estado")
    list_filter = ("estado", "fecha_hora", "medico")
    search_fields = ("paciente__apellido", "paciente__dni","medico__apellido", "motivo")
    date_hierarchy = "fecha_hora"

    fieldsets = (
        ("Asignación de Turnos", {
            "fields":("medico", "paciente")
        }),
        ("Detalles de la Cita", {
            "fields": ("fecha_hora", "motivo", "estado")
        }),
    )

@admin.register(ObraSocial)
class ObraSocialAdmin(ModelAdmin):
    list_display = ("nombre", "sitio_web", "requiere_token")
    search_fields = ("nombre",)
    filter_horizontal = ("medicos_disponibles",)

@admin.register(Ausencia)
class AusenciaAdmin(ModelAdmin):
    list_display = ("medico", "fecha_inicio", "fecha_fin", "motivo")
    list_filter = ("medico", "fecha_inicio")

