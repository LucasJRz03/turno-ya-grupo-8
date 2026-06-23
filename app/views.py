"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from django.views.generic import ListView, TemplateView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import TurnoForm
from .models import Medico, Turno, Paciente
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect


class HomeView(TemplateView):
    """Vista de inicio. Por ahora vacía — completar con estadísticas."""

    template_name = "clinica/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_medicos'] = Medico.objects.count()
        context['total_pacientes'] = Paciente.objects.count()
        context['total_turnos'] = Turno.objects.count()

        context['turnos_pendientes'] = Turno.objects.filter(estado='PENDIENTE').count()
    
        return context

class MedicoListView(ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"


class TurnoListView(LoginRequiredMixin, ListView):
    """Lista los turnos asociados a un paciente o medico."""

    model = Turno
    template_name = "clinica/lista_turnos.html"
    context_object_name = "turnos"

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "medico"):
            return Turno.objects.filter(medico__usuario= user).select_related("paciente")
        elif hasattr(user, "paciente"):
            return Turno.objects.filter(paciente__usuario=user).select_related("medico")
        else:
            return Turno.objects.none()

class TurnoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo turno."""

    model = Turno
    form_class = TurnoForm
    template_name = "clinica/nuevo_turno.html"
    success_url = reverse_lazy("app:lista_turnos")

    def form_valid(self, form):
        """Asigna el paciente actual al turno antes de guardarlo."""
        form.instance.paciente = self.request.user.paciente
        messages.success(self.request, "Turno creado correctamente.")
        return super().form_valid(form)

class PacienteListView(ListView):
    """Lista todos los pacientes registrados."""
    model = Paciente
    template_name = "clinica/lista_pacientes.html"
    context_object_name = "pacientes"
    ordering = ['apellido', 'nombre'] # Ordenar por apellido y nombre 

class MedicoDetailView(DetailView):
    """Muestra el detalle de un médico"""
    model = Medico
    template_name = "clinica/detalle_medico.html"
    context_object_name = "medico"

class TurnoCancelView(LoginRequiredMixin, UpdateView):
    """Vista para cancelar un turno existente."""
    model = Turno
    fields = [] # Solo es necesario cambiar el estado
    template_name = "clinica/cancelar_turno_confirm.html"

    def post(self, request, *args, **kwargs):
        turno = self.get_object()
        # verificar permisos: solo el paciente o el médico en cuestion pueden cancelar
        if request.user == turno.paciente.usuario or request.user == turno.medico.usuario:
            turno.cancelar() 
            messages.success(self.request, "El turno fue cancelado con éxito.")
        else:
            messages.error(self.request, "No tienes permiso para cancelar el turno.")
        
        return HttpResponseRedirect(reverse("app:lista_turnos"))




