"""Configuración básica del admin para los modelos de la app."""

from django.contrib import admin
from django.contrib import messages as django_messages
from unfold.admin import ModelAdmin 
from .models import Medico, Especialidad, Paciente, Turno, ObraSocial, Ausencia, SolicitudMedico
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
    fieldsets = (
        ("Información Personal", {
            "fields": ("usuario",)
        }),
        ("Información Profesional", {
            "fields": ("matricula", "especialidad")
        })
    )
    
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

    fieldsets = (
        ("Datos Identificatorios",{
            "fields": ("usuario", "dni")
        }),
        ("información de Contacto", {
            "fields": ("telefono",)
        }),
    )
    
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
    search_fields = ("paciente__usuario__last_name", "paciente__dni", "medico__usuario__last_name", "motivo")
    date_hierarchy = "fecha_hora"

    fieldsets = (
        ("Datos del Turno", {
            "fields": ("medico", "paciente", "fecha_hora", "motivo", "estado")
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
@admin.register(SolicitudMedico)
class SolicitudMedicoAdmin(ModelAdmin):
    """Administrador para las solicitudes de médico."""
    
    list_display = (
        'usuario',
        'matricula',
        'especialidad',
        'estado',
        'fecha_solicitud',
        'fecha_resolucion'
    )
    
    list_filter = ('estado', 'especialidad', 'fecha_solicitud')
    search_fields = (
        'usuario__username',
        'usuario__email',
        'usuario__first_name',
        'usuario__last_name',
        'matricula'
    )
    
    ordering = ('-fecha_solicitud',)
    date_hierarchy = 'fecha_solicitud'
    
    fieldsets = (
        (None, {
            'fields': ('usuario', 'matricula', 'especialidad')
        }),
        ('Estado de la solicitud', {
            'fields': ('estado', 'fecha_solicitud', 'fecha_resolucion', 'comentario_admin'),
            'description': 'El administrador puede aprobar o rechazar la solicitud.'
        }),
    )
    
    readonly_fields = ('fecha_solicitud', 'fecha_resolucion')
    
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']
    
    @admin.action(description="Aprobar solicitudes seleccionadas")
    def aprobar_solicitudes(self, request, queryset):
        """Aprueba las solicitudes seleccionadas."""
        aprobadas = 0
        errores = 0
        
        for solicitud in queryset.filter(estado='PENDIENTE'):
            exito, errors = solicitud.aprobar(comentario=f"Aprobado por {request.user.username}")
            if exito:
                aprobadas += 1
            else:
                errores += 1
                django_messages.error(
                    request,
                    f"Error al aprobar solicitud de {solicitud.usuario.username}: {errors[0]}"
                )
        
        if aprobadas > 0:
            django_messages.success(
                request,
                f"{aprobadas} solicitud(es) aprobada(s) correctamente."
            )
        
        if errores > 0:
            django_messages.warning(
                request,
                f"{errores} solicitud(es) no pudieron ser aprobadas."
            )
    
    @admin.action(description="Rechazar solicitudes seleccionadas")
    def rechazar_solicitudes(self, request, queryset):
        """Rechaza las solicitudes seleccionadas."""
        rechazadas = 0
        
        for solicitud in queryset.filter(estado='PENDIENTE'):
            exito, errors = solicitud.rechazar(comentario=f"Rechazado por {request.user.username}")
            if exito:
                rechazadas += 1
        
        if rechazadas > 0:
            django_messages.success(
                request,
                f"{rechazadas} solicitud(es) rechazada(s) correctamente."
            )