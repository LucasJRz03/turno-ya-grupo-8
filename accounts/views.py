from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, PerfilForm, SolicitudMedicoForm
from .models import CustomUser
from django.shortcuts import get_object_or_404, redirect
from app.models import Paciente, SolicitudMedico
class LoginView(DjangoLoginView):
    """Vista para manejar el inicio de sesión de los usuarios."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("app:home")

    def form_valid(self, form):
        """Muestra un mensaje de bienvenida si el formulario es valido."""
        messages.success(self.request, f"Bienvenido, {self.request.user.username}!")
        return super().form_valid(form)
      
    def form_invalid(self, form):
        """Muestra un mensaje de error si el formulario no es válido."""
        messages.error(self.request, "Credenciales inválidas. Verificá tu usuario y contraseña.")
        return super().form_invalid(form)    
class LogoutView(DjangoLogoutView):
    """Vista de logout"""
    pass
class RegisterView(CreateView):
    """Vista de registro de nuevos usuarios."""

    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("app:home")

    def form_valid(self, form):
        """Crea un nuevo usuario y lo autentica."""
        user = form.save(commit=False)
        user.tipo_usuario = 'paciente'
        user.save()
        #Auto-login despues del registro
        login(self.request, user)
        messages.success(self.request, f"Bienvenido, {user.username}! Tu cuenta ha sido creada correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Muestra un mensaje de error si el formulario no es válido."""
        messages.error(self.request, "Error en el formulario. Corregi los errores e inténtalo de nuevo.")
        return super().form_invalid(form)
class PerfilView(LoginRequiredMixin, UpdateView):
    """Vista de perfil que permite:
    1. Editar datos básicos del usuario (email, nombre, apellido)
    2. Solicitar el rol de médico (si es paciente)"""

    model = CustomUser
    form_class = PerfilForm
    template_name = "accounts/perfil.html"
    success_url = reverse_lazy("accounts:perfil")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar si el usuario ya es médico
        if self.request.user.es_medico:
            context['es_medico'] = True
            try:
                context['medico_obj'] = self.request.user.medico
            except Exception:
                context['medico_obj'] = None
        else:
            context['es_medico'] = False
            
            # Verificar si tiene una solicitud pendiente
            try:
                solicitud = SolicitudMedico.objects.get(usuario=self.request.user)
                context['tiene_solicitud'] = True
                context['solicitud'] = solicitud
                context['estado_solicitud'] = solicitud.get_estado_display()
            except SolicitudMedico.DoesNotExist:
                context['tiene_solicitud'] = False
                # Agregar formulario de solicitud al contexto
                if 'solicitud_form' not in kwargs:
                    context['solicitud_form'] = SolicitudMedicoForm()
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Detectar si viene del formulario de perfil o de solicitud médica
        if 'matricula' in request.POST:
            return self.handle_solicitud(request)
        else:
            return super().post(request, *args, **kwargs)

    def handle_solicitud(self, request):
        """Maneja el envío del formulario de solicitud de médico."""
        form = SolicitudMedicoForm(request.POST)
        
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            
            # Validar usando el patrón del modelo
            errors = SolicitudMedico.validate(
                usuario=solicitud.usuario, 
                matricula=solicitud.matricula, 
                especialidad=solicitud.especialidad)
            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('accounts:perfil')
            
            solicitud.save()
            messages.success(
                request,
                "Tu solicitud para ser médico ha sido enviada. "
                "El administrador la revisará pronto."
            )
            return redirect('accounts:perfil')
        else:
            # Si el formulario tiene errores, mostrarlos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('accounts:perfil')