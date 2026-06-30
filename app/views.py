"""Vistas iniciales para navegar médicos y pantalla de inicio."""

from django.views.generic import ListView, TemplateView, CreateView, DetailView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .forms import TurnoForm, AusenciaForm
from .models import Medico, Turno, Paciente, Ausencia
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
class HomeView(TemplateView):
    """Vista de inicio. Muestra estadísticas o los próximos turnos del usuario."""

    template_name = "clinica/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user= self.request.user
        
        # Si es administrador, muestra estadísticas globales
        if user.is_staff:
            context['total_medicos'] = Medico.objects.count()
            context['total_pacientes'] = Paciente.objects.count()
            context['total_turnos'] = Turno.objects.count()
            context['turnos_pendientes'] = Turno.objects.filter(estado='PENDIENTE').count()
        else:
            # Si es médico o paciente, muestra sus próximos turnos
            try:
                if user.es_medico:
                    context['mis_turnos'] = Turno.objects.filter(
                        medico__usuario=user,
                        estado__in=['PENDIENTE', 'CONFIRMADO'],
                        fecha_hora__gte=timezone.now()
                    ).select_related('paciente__usuario').order_by('fecha_hora')[:5]
                elif user.es_paciente:
                    context['mis_turnos'] = Turno.objects.filter(
                        paciente__usuario=user,
                        estado__in=['PENDIENTE', 'CONFIRMADO'],
                        fecha_hora__gte=timezone.now()
                    ).select_related('medico__usuario').order_by('fecha_hora')[:5]
            except Exception:
                context['mis_turnos'] = []

        return context
class MedicoListView(LoginRequiredMixin, ListView):
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

        #Si es administrador, ve todo.
        if user.is_staff:
            return Turno.objects.all().select_related("paciente", "medico")

        # Usa las propiedades del CustomUser
        if user.es_medico:
            try:
                return Turno.objects.filter(
                    medico__usuario=user
                ).select_related("paciente__usuario")
            except Exception:
                return Turno.objects.none()
        elif user.es_paciente:
            try:
                return Turno.objects.filter(
                    paciente__usuario=user
                ).select_related("medico__usuario")
            except Exception:
                return Turno.objects.none()
        return Turno.objects.none()   
class TurnoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo turno."""
    model = Turno
    form_class = TurnoForm
    template_name = "clinica/nuevo_turno.html"
    success_url = reverse_lazy("app:lista_turnos")

    def get_initial(self):
        initial = super().get_initial()

        medico_id = self.request.GET.get('medico')

        if medico_id:
            initial['medico'] = medico_id

        return initial

    def form_valid(self, form):
        """
        Crea un turno usando el patrón Turno.new().
        Esto garantiza que se respeten todas las validaciones del modelo
        (fecha futura, superposición de turnos, etc.)
        """
        # 1. Verificar que el usuario tenga perfil de paciente
        try:
            paciente = self.request.user.paciente
        except Paciente.DoesNotExist:
            messages.error(
                self.request,
                "Debes completar tu perfil de paciente antes de sacar un turno."
            )
            return self.form_invalid(form)

        # 2. Extraer datos limpios del formulario
        medico = form.cleaned_data.get('medico')
        fecha_hora = form.cleaned_data.get('fecha_hora')
        motivo = form.cleaned_data.get('motivo', '')

        # 3. Llamar al patrón de creación del modelo
        instancia, errores = Turno.new(
            medico=medico,
            paciente=paciente,
            fecha_hora=fecha_hora,
            motivo=motivo,
            estado='PENDIENTE'
        )

        # 4. Manejar errores de validación del modelo
        if errores:
            for error in errores:
                # add_error(None, ...) agrega el error como "non-field error"
                form.add_error(None, error)
            return self.form_invalid(form)

        # 5. Éxito: asignar la instancia y redirigir
        self.object = instancia
        messages.success(self.request, "Turno creado correctamente.")
        return HttpResponseRedirect(self.get_success_url())
class PacienteListView(LoginRequiredMixin, ListView):
    """Lista todos los pacientes registrados."""
    model = Paciente
    template_name = "clinica/lista_pacientes.html"
    context_object_name = "pacientes"
    ordering = ['usuario__last_name', 'usuario__first_name'] # Ordenar por apellido y nombre 

    def test_func(self):
        # Esta es la prueba de seguridad: ¿El usuario es Staff/Admin?
        return self.request.user.is_staff

    def handle_no_permission(self):
        # Si no es staff, en lugar de mandarlo al login, le mostramos un error 403 (Prohibido)
        raise PermissionDenied("No tienes permisos para acceder a esta sección.")

    def get_queryset(self):
        # select_related para evitar N+1 queries al acceder al usuario
        return Paciente.objects.select_related('usuario').all()
class MedicoDetailView(LoginRequiredMixin, DetailView): 
    """Vista para ver el detalle de un médico.
    Muestra información del médico, obras sociales que atiende y sus ausencias.
    Accesible para cualquier usuario autenticado (pacientes, médicos y admins)."""
    model = Medico
    template_name = "clinica/detalle_medico.html"
    context_object_name = "medico"

    def get_context_data(self, **kwargs):
        """Agrega obras sociales y ausencias al contexto del template."""
        context = super().get_context_data(**kwargs)
        medico = self.get_object()
        
        # Obras sociales que atiende el médico
        context['obras_sociales'] = medico.obras_sociales.all()
        # Ausencias futuras (desde hoy en adelante)
        context['ausencias'] = medico.ausencias.filter(
            fecha_inicio__gte=timezone.now().date()
        ).order_by('fecha_inicio')
        
        return context
class TurnoCancelView(LoginRequiredMixin, UpdateView):
    """Vista para cancelar un turno existente."""
    model = Turno
    fields = [] # Solo es necesario cambiar el estado
    template_name = "clinica/cancelar_turno_confirm.html"

    def post(self, request, *args, **kwargs):
        turno = self.get_object()

        # Verificar que el turno esté pendiente
        if turno.estado != 'PENDIENTE':
            messages.error(self.request, "Solo se pueden cancelar turnos pendientes.")
            return HttpResponseRedirect(reverse("app:lista_turnos"))

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

        # Verificar que el turno esté pendiente
        if turno.estado != 'PENDIENTE':
            messages.error(self.request, "Solo se pueden confirmar turnos pendientes.")
            return HttpResponseRedirect(reverse("app:lista_turnos"))

        if request.user.is_staff or (hasattr(request.user, 'medico') and request.user.medico == turno.medico):
            turno.confirmar()
            messages.success(self.request, "El turno ha sido confirmado.")
        else:
            messages.error(self.request, "No tienes permiso para confirmar este turno.")
        
        return HttpResponseRedirect(reverse("app:lista_turnos"))  
class TurnoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para que un paciente (o admin) edite un turno pendiente."""
    model = Turno
    form_class = TurnoForm
    template_name = "clinica/nuevo_turno.html"  # Reutilizamos el mismo template
    success_url = reverse_lazy("app:lista_turnos")

    def get_queryset(self):
        """
        Restringe los turnos que se pueden editar.
        - Un admin puede editar cualquier turno.
        - Un paciente solo puede editar sus propios turnos y solo si están PENDIENTES.
        """
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(paciente__usuario=self.request.user, estado='PENDIENTE')

    def form_valid(self, form):
        """Sobrescribimos form_valid para usar el patrón turno.update() en lugar de form.save()"""
        turno = self.get_object()
        
        # Doble chequeo de seguridad
        if turno.estado != 'PENDIENTE':
            messages.error(self.request, "Solo se pueden editar turnos que estén pendientes.")
            return HttpResponseRedirect(self.get_success_url())

        # Extraer datos limpios del formulario
        medico = form.cleaned_data.get('medico')
        fecha_hora = form.cleaned_data.get('fecha_hora')
        motivo = form.cleaned_data.get('motivo', '')

        # Llamar al método update del modelo (esto valida superposiciones, fechas pasadas, etc.)
        errores = turno.update(
            medico=medico,
            fecha_hora=fecha_hora,
            motivo=motivo
        )

        # Si el modelo devuelve errores, los inyectamos en el formulario
        if errores:
            for error in errores:
                form.add_error(None, error)
            return self.form_invalid(form)

        # Éxito
        messages.success(self.request, "Turno actualizado correctamente.")
        return HttpResponseRedirect(self.get_success_url())
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