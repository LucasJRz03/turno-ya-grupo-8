"""Rutas públicas de la aplicación principal."""

from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    # Inicio
    path("", views.HomeView.as_view(), name="home"),
    # Medicos
    path("medicos/", views.MedicoListView.as_view(), name="lista_medicos"),
    path("medicos/<int:pk>/", views.MedicoDetailView.as_view(), name="detalle_medico"),
    # Pacientes
    path("pacientes/", views.PacienteListView.as_view(), name="lista_pacientes"),
    # Turnos
    path("turnos/", views.TurnoListView.as_view(), name="lista_turnos"),
    path("turnos/nuevo/", views.TurnoCreateView.as_view(), name="nuevo_turno"),
    path("turnos/<int:pk>/cancelar/", views.TurnoCancelView.as_view(), name="cancelar_turno"),  
    #Ausencias
    path("ausencias/nueva/", views.AusenciaCreateView.as_view(), name="crear_ausencia")
    # TODO:
    # path("medicos/<int:pk>/", views.DetalleMedicoView.as_view(), name="detalle_medico"),
    # path("turnos/", views.ListaTurnosView.as_view(), name="lista_turnos"),
    # path("turnos/nuevo/", views.NuevoTurnoView.as_view(), name="nuevo_turno"),
    # path("turnos/<int:pk>/cancelar/", views.CancelarTurnoView.as_view(), name="cancelar_turno"),
]