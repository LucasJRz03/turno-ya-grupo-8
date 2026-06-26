from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, PerfilForm
from .models import CustomUser
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