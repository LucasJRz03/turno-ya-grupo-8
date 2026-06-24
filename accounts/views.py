from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import FormView, RedirectView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, LoginForm
from .models import CustomUser

class LoginView(FormView):
    """Vista para manejar el inicio de sesión de los usuarios."""

    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("app:home")

    def form_valid(self, form):
        """Autentica al usuario y lo redirige a la página principal si las credenciales son correctas."""
        #Recupera el nombre de usuario y la contraseña del formulario
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")

        #Autentica al usuario usando las credenciales proporcionadas
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            #Si el usuario es válido, inicia sesión y muestra un mensaje de bienvenida
            login(self.request, user)
            messages.success(self.request, f"Bienvenido, {user.username}!")
            return super().form_valid(form)
        else:
            #Si las credenciales son inválidas, muestra un mensaje de error
            messages.error(self.request, "Credenciales inválidas. Por favor, inténtalo de nuevo.")
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        """Muestra un mensaje de error si el formulario no es válido."""
        messages.error(self.request, "Error en el formulario. Por favor, corrige los errores e inténtalo de nuevo.")
        #Vuelve a renderizar la página con el formulario y los mensajes de error
        return self.render_to_response(self.get_context_data(form=form))

class LogoutView(RedirectView):
    """Vista para manejar el cierre de sesión de los usuarios."""

    url = reverse_lazy("app:home")

    def get(self, request, *args, **kwargs):
        """Cierra la sesión del usuario y redirige a la página de inicio de sesión."""
        logout(request)
        messages.info(request, "Has cerrado sesión correctamente.")
        return super().get(request, *args, **kwargs)

class RegisterView(FormView):
    """Vista para manejar el registro de nuevos usuarios."""

    template_name = "accounts/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("app:home")

    def form_valid(self, form):
        """Crea un nuevo usuario con TODOS los datos del formulario y lo autentica."""
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Bienvenido, {user.username}! Tu cuenta ha sido creada correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Muestra un mensaje de error si el formulario no es válido."""
        messages.error(self.request, "Error en el formulario. Por favor, corrige los errores e inténtalo de nuevo.")
        return self.render_to_response(self.get_context_data(form=form))