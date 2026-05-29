"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from django.views.generic import ListView, TemplateView, CreateView
from django.contrib import messages
from .forms import TurnoForm
from .models import Medico, Turno
from django.urls import reverse_lazy


class HomeView(TemplateView):
    """Vista de inicio. Por ahora vacía — completar con estadísticas."""

    template_name = "clinica/home.html"


class ListaMedicosView(ListView):
    """Lista todos los médicos."""

    model = Medico
    template_name = "clinica/lista_medicos.html"
    context_object_name = "medicos"

class TurnoCreateView(CreateView):
    """Vista para crear un nuevo turno."""

    model = Turno
    form_class = TurnoForm
    fields = ["medico", "paciente", "fecha_hora", "motivo",]
    template_name = "clinica/nuevo_turno.html"
    success_url = reverse_lazy("app:lista_turnos")

    def form_valid(self, form):
        """Asigna el paciente actual al turno antes de guardarlo."""
        form.instance.paciente = self.request.user.paciente
        messages.success(self.request, "Turno creado correctamente.")
        return super().form_valid(form)

# TODO: implementar las siguientes vistas:
# class DetalleMedicoView(...): ...
# class ListaTurnosView(...): ...
# class NuevoTurnoView(...): ...
# class CancelarTurnoView(...): ...
# class ListaPacientesView(...): ...