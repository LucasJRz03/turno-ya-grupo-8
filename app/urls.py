"""Rutas públicas de la aplicación principal."""

from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    # Inicio
    path("", views.HomeView.as_view(), name="home"),
    # Medicos
    path("medicos/", views.ListaMedicosView.as_view(), name="lista_medicos"),
    path("medicos/<int:pk>/", views.DetalleMedicoView.as_view(), name="detalle_medico"),
    # Turnos
    path("turnos/", views.TurnoListView.as_view(), name="lista_turnos"),
    path("turnos/nuevo/", views.TurnoCreateView.as_view(), name="nuevo_turno"),
    path("turnos/<int:pk>/cancelar/", views.CancelarTurnoView.as_view(), name="cancelar_turno")   

    # TODO:
    # path("medicos/<int:pk>/", views.DetalleMedicoView.as_view(), name="detalle_medico"),
    # path("turnos/", views.ListaTurnosView.as_view(), name="lista_turnos"),
    # path("turnos/nuevo/", views.NuevoTurnoView.as_view(), name="nuevo_turno"),
    # path("turnos/<int:pk>/cancelar/", views.CancelarTurnoView.as_view(), name="cancelar_turno"),
]