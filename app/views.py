"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from django.views.generic import ListView, TemplateView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import TurnoForm, AusenciaForm
from .models import Medico, Turno, Paciente, Ausencia
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

    def get_queryset(self):
        queryset = super().get_queryset()
        # Busca si en la URL viene un parámetro 
        especialidad_id = self.request.GET.get('especialidad')

        if especialidad_id:
            # Si hay parámetro, filtra
            queryset = queryset.filter(especialidad_id=especialidad_id)

        return queryset

    def get_context_data(self, **kwargs):
        # Agrega las especialidades al contexto para poder armar el <select> en el HTML
        context = super().get_context_data(**kwargs)
        from .models import Especialidad
        context['especialidades'] = Especialidad.objects.all()
        return context


class TurnoListView(LoginRequiredMixin, ListView):
    """Lista los turnos asociados a un paciente o medico."""

    model = Turno
    template_name = "clinica/lista_turnos.html"
    context_object_name = "turnos"

    def get_queryset(self):
        user = self.request.user
        
        # 1. Si es administrador, ve todo.
        if user.is_staff:
            return Turno.objects.all().select_related("paciente", "medico")
        
        # 2. Si es médico, solo ve lo suyo.
        if hasattr(user, "medico"):
            return Turno.objects.filter(medico__usuario=user).select_related("paciente")
        
        # 3. Si es paciente, solo ve lo suyo.
        elif hasattr(user, "paciente"):
            return Turno.objects.filter(paciente__usuario=user).select_related("medico")
        
        # 4. Por si no es ninguno de los otros, no ve nada.
        return Turno.objects.none()

class TurnoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo turno."""

    model = Turno
    form_class = TurnoForm
    template_name = "clinica/nuevo_turno.html"
    success_url = reverse_lazy("app:lista_turnos")

    def form_valid(self, form):
       # Extrae los datos del formulario
       medico = form.cleaned_data.get('medico')
       fecha_hora = form.cleaned_data.get('fecha_hora')
       motivo = form.cleaned_data.get('motivo', '')

       # Obtiene el paciente logueado
       # Si el usuario tiene el perfil de paciente creado
       paciente = self.request.user.paciente

       # Llama al patrón de creación
       instancia, errores = Turno.new(
        medico=medico,
        paciente=paciente,
        fecha_hora=fecha_hora,
        motivo=motivo
       )

       # Maneja los errores que devuelve el modelo
       if errores:
           for error in errores:
            form.add_error(None, error)
           return self.form_invalid(form)

       self.object = instancia
       messages.success(self.request, "Turno creado correctamente.")
       return HttpResponseRedirect(self.get_success_url())

      

class PacienteListView(ListView):
    """Lista todos los pacientes registrados."""
    model = Paciente
    template_name = "clinica/lista_pacientes.html"
    context_object_name = "pacientes"
    ordering = ['apellido', 'nombre'] # Ordenar por apellido y nombre 

class MedicoDetailView(UserPassesTestMixin, DetailView):
    """Vista para ver el detalle de un médico, sus obras sociales y ausencias"""
    model = Medico
    template_name = "clinica/detalle_medico.html"
    context_object_name = "medico"

    def test_func(self):
        """
        Condición de seguridad del UserPassesTestMixin.
        Si retorna True, entra a la página. Si retorna False, tira error 403 (Prohibido.
        """
        return self.request.user.is_authenticated and self.request.user.is_staff

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

class TurnoConfirmarView(LoginRequiredMixin, UpdateView):
    """Vista para que un médico confirme un turno pendiente."""
    model = Turno
    fields = []
    template_name = "clinica/confirmar_turno.html"

    def post(self, request, *args, **kwargs):
        turno = self.get_object()

        if request.user.is_staff or (hasattr(request.user, 'medico') and request.user.medico == turno.medico):
            turno.confirmar()
            messages.success(self.request, "El turno ha sido confirmado.")
        else:
            messages.error(self.request, "No tienes permiso para confirmar este turno.")
        
        return HttpResponseRedirect(reverse("app:lista_turnos"))
    

class AusenciaCreateView(LoginRequiredMixin, CreateView):
    """Vista para que el personal cargue una nueva ausencia de un médico."""
    model = Ausencia
    template_name = "clinica/ausencia_form.html"
    form_class = AusenciaForm
    success_url = reverse_lazy('app:lista_medicos')

    def form_valid(self, form):
        medico = form.cleaned_data['medico']
        motivo = form.cleaned_data['motivo']
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']

        instancia, errores = Ausencia.new(medico,motivo,fecha_inicio, fecha_fin)

        if errores:
            for error in errores:
                form.add_error(None,error)
            return self.form_invalid(form)
        
        # Solución del problema de copiado de django
        self.object = instancia
        return HttpResponseRedirect(self.get_success_url())
    
