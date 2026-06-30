"""Pruebas unitarias para las vistas de TurnoYa."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Medico, Especialidad, Paciente, Ausencia

User = get_user_model()

class VistasTurnoYaTestCase(TestCase):

    def setUp(self):
        # Configuramos el cliente que simula el navegador
        self.client = Client()

        # Creamos usuarios con sus roles
        self.user_admin = User.objects.create_superuser(
            username="admin_test", email="admin@test.com", password="123"
        )
        
        self.user_paciente = User.objects.create_user(
            username="paciente_test", email="pac@test.com", password="123"
        )
        
        self.user_medico = User.objects.create_user(
            username="medico_test", email="med@test.com", password="123"
        )

        # Creamos datos base
        self.especialidad, _ = Especialidad.new(nombre="Cardiología")
        self.medico, _ = Medico.new(nombre="Juan", apellido="Perez", matricula="MP-1", especialidad=self.especialidad)
        self.medico.usuario = self.user_medico
        self.medico.save()

        self.paciente, _ = Paciente.new(
            usuario=self.user_paciente, nombre="Ana", apellido="Gomez", dni="11222333", email="ana@test.com"
        )

        # --- VISTAS PÚBLICAS ---
    def test_home_view_acceso_publico(self):
        """Verifica que el Home cargue correctamente."""
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/home.html")

    def test_lista_medicos_view(self):
        """Verifica que la lista de médicos sea pública y devuelva código 200."""
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_medicos.html")

    def test_lista_pacientes_view(self):
        """Verifica que la lista de pacientes cargue correctamente."""
        response = self.client.get(reverse("app:lista_pacientes"))
        self.assertEqual(response.status_code, 200)
    
    # --- VISTAS PROTEGIDAS (Requieren permisos específicos) ---
    def test_detalle_medico_requiere_staff(self):
        """
        Verifica que MedicoDetailView pida ser staff.
        Si entra un paciente normal, debería dar 403 (Prohibido).
        """
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:detalle_medico", args=[self.medico.pk]))
        self.assertEqual(response.status_code, 403)

    def test_detalle_medico_acceso_staff(self):
        """Verifica que el administrador sí pueda ver el detalle del médico."""
        self.client.login(username="admin_test", password="123")
        response = self.client.get(reverse("app:detalle_medico", args=[self.medico.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/detalle_medico.html")

    # --- VISTAS CON LOGIN REQUIRED ---
    def test_lista_turnos_redirecciona_sin_login(self):
        """Si un usuario anónimo intenta ver turnos, debe ser enviado al login (302)."""
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) # O tu URL de login

    def test_lista_turnos_con_login(self):
        """Si el usuario está logueado, debe ver la página de turnos."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_turnos.html")

    def test_nuevo_turno_con_login(self):
        """Verifica que el formulario de crear turno cargue para usuarios logueados."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:nuevo_turno"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/nuevo_turno.html")

    def test_crear_ausencia_requiere_login(self):
        """Verifica que un anónimo no pueda cargar ausencias."""
        response = self.client.get(reverse("app:crear_ausencia"))
        self.assertEqual(response.status_code, 302)

    def test_crear_ausencia_con_login(self):
        """Verifica que el formulario de ausencias cargue para usuarios autorizados."""
        self.client.login(username="admin_test", password="123")
        response = self.client.get(reverse("app:crear_ausencia"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/ausencia_form.html")
    
    def test_crear_ausencia_post_guarda_en_bd(self):
        """Verifica que enviar el formulario POST realmente cree la Ausencia."""
        self.client.login(username="medico_test", password="123")
        
        # Simula completar y enviar el formulario
        datos_formulario = {
            "medico": self.medico.pk,
            "fecha_inicio": "2026-07-01",
            "fecha_fin": "2026-07-10",
            "motivo": "Congreso médico"
        }
        response = self.client.post(reverse("app:crear_ausencia"), data=datos_formulario)
        
        #  CreateView redirigen (código 302) al éxito
        self.assertEqual(response.status_code, 302)
        
        # Verificamos que realmente se haya guardado
        self.assertTrue(Ausencia.objects.filter(medico=self.medico, motivo="Congreso médico").exists())