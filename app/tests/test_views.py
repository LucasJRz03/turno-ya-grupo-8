"""Pruebas unitarias para las vistas de TurnoYa."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from app.models import Medico, Especialidad, Paciente, Ausencia, Turno

User = get_user_model()


class VistasPublicasTest(TestCase):
    """Tests para vistas accesibles sin autenticación."""

    def setUp(self):
        self.client = Client()
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")

    def test_home_view_acceso_publico(self):
        """El Home es público y muestra estadísticas."""
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/home.html")
        # Verifica que el contexto tenga las estadísticas
        self.assertIn("total_medicos", response.context)
        self.assertIn("total_pacientes", response.context)
        self.assertIn("total_turnos", response.context)

    def test_home_view_contexto_admin(self):
        """Si el usuario es staff, el Home muestra estadísticas globales."""
        admin = User.objects.create_user(
            username="admin", email="admin@test.com",
            password="123", is_staff=True, tipo_usuario="admin"
        )
        self.client.login(username="admin", password="123")
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_medicos", response.context)

    def test_home_view_contexto_paciente(self):
        """Si el usuario es paciente, el Home muestra sus próximos turnos."""
        paciente_user = User.objects.create_user(
            username="paciente", email="pac@test.com",
            password="123", tipo_usuario="paciente",
            first_name="Ana", last_name="Gómez"
        )
        self.client.login(username="paciente", password="123")
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("mis_turnos", response.context)


class VistasProtegidasLoginTest(TestCase):
    """Tests para vistas que requieren autenticación (LoginRequiredMixin)."""

    def setUp(self):
        self.client = Client()
        self.user_paciente = User.objects.create_user(
            username="paciente_test", email="pac@test.com",
            password="123", tipo_usuario="paciente",
            first_name="Ana", last_name="Gómez"
        )
        self.user_medico = User.objects.create_user(
            username="medico_test", email="med@test.com",
            password="123", tipo_usuario="medico",
            first_name="Juan", last_name="Pérez"
        )
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        self.medico = Medico.objects.create(
            usuario=self.user_medico,
            matricula="MP-1001",
            especialidad=self.especialidad
        )
        self.paciente = Paciente.objects.create(
            usuario=self.user_paciente,
            dni="11222333",
            telefono="2901-11-11-11"
        )

    # --- MedicoListView ---
    def test_lista_medicos_redirecciona_sin_login(self):
        """Sin login, redirige al login (302)."""
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_lista_medicos_con_login(self):
        """Con login, muestra la lista de médicos."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_medicos.html")
        self.assertIn("medicos", response.context)

    def test_lista_medicos_filtro_por_especialidad(self):
        """El filtro por especialidad funciona correctamente."""
        otra_esp = Especialidad.objects.create(nombre="Pediatría")
        otro_medico_user = User.objects.create_user(
            username="pediatra", email="ped@test.com",
            password="123", tipo_usuario="medico",
            first_name="Sofía", last_name="López"
        )
        Medico.objects.create(
            usuario=otro_medico_user,
            matricula="MP-2002",
            especialidad=otra_esp
        )

        self.client.login(username="paciente_test", password="123")
        
        # Sin filtro: debe mostrar ambos médicos
        response = self.client.get(reverse("app:lista_medicos"))
        self.assertEqual(len(response.context["medicos"]), 2)

        # Con filtro: debe mostrar solo 1
        response = self.client.get(
            reverse("app:lista_medicos") + f"?especialidad={self.especialidad.pk}"
        )
        self.assertEqual(len(response.context["medicos"]), 1)
        self.assertEqual(response.context["medicos"][0].matricula, "MP-1001")

    # --- MedicoDetailView ---
    def test_detalle_medico_acceso_paciente(self):
        """Un paciente autenticado puede ver el detalle de un médico."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(
            reverse("app:detalle_medico", args=[self.medico.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/detalle_medico.html")
        self.assertIn("obras_sociales", response.context)
        self.assertIn("ausencias", response.context)

    def test_detalle_medico_redirecciona_sin_login(self):
        """Sin login, redirige al login."""
        response = self.client.get(
            reverse("app:detalle_medico", args=[self.medico.pk])
        )
        self.assertEqual(response.status_code, 302)

    # --- TurnoListView ---
    def test_lista_turnos_redirecciona_sin_login(self):
        """Sin login, redirige al login."""
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 302)

    def test_lista_turnos_paciente_ve_sus_turnos(self):
        """Un paciente solo ve sus propios turnos."""
        Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Consulta",
            estado="PENDIENTE"
        )
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["turnos"]), 1)

    def test_lista_turnos_medico_ve_sus_turnos(self):
        """Un médico solo ve sus propios turnos."""
        Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Consulta",
            estado="PENDIENTE"
        )
        self.client.login(username="medico_test", password="123")
        response = self.client.get(reverse("app:lista_turnos"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["turnos"]), 1)

    # --- TurnoCreateView ---
    def test_nuevo_turno_redirecciona_sin_login(self):
        """Sin login, redirige al login."""
        response = self.client.get(reverse("app:nuevo_turno"))
        self.assertEqual(response.status_code, 302)

    def test_nuevo_turno_con_login(self):
        """Con login, muestra el formulario de nuevo turno."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:nuevo_turno"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/nuevo_turno.html")

    def test_nuevo_turno_post_crea_turno(self):
        """POST con datos válidos crea un turno usando Turno.new()."""
        self.client.login(username="paciente_test", password="123")
        datos = {
            "medico": self.medico.pk,
            "fecha_hora": (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "motivo": "Consulta de rutina"
        }
        response = self.client.post(reverse("app:nuevo_turno"), data=datos)
        self.assertEqual(response.status_code, 302)  # Redirige al éxito
        self.assertTrue(Turno.objects.filter(paciente=self.paciente).exists())

    def test_nuevo_turno_post_fecha_pasada_falla(self):
        """POST con fecha pasada no crea el turno."""
        self.client.login(username="paciente_test", password="123")
        datos = {
            "medico": self.medico.pk,
            "fecha_hora": (timezone.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "motivo": "Consulta"
        }
        response = self.client.post(reverse("app:nuevo_turno"), data=datos)
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(Turno.objects.filter(paciente=self.paciente).exists())


class VistasProtegidasPorPermisosTest(TestCase):
    """Tests para vistas que requieren permisos específicos (UserPassesTestMixin)."""

    def setUp(self):
        self.client = Client()
        self.user_admin = User.objects.create_user(
            username="admin_test", email="admin@test.com",
            password="123", is_staff=True, tipo_usuario="admin"
        )
        self.user_paciente = User.objects.create_user(
            username="paciente_test", email="pac@test.com",
            password="123", tipo_usuario="paciente"
        )
        self.user_medico = User.objects.create_user(
            username="medico_test", email="med@test.com",
            password="123", tipo_usuario="medico"
        )
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        self.medico = Medico.objects.create(
            usuario=self.user_medico,
            matricula="MP-1001",
            especialidad=self.especialidad
        )

    # --- PacienteListView (requiere is_staff) ---
    def test_lista_pacientes_admin_accede(self):
        """El admin puede ver la lista de pacientes."""
        self.client.login(username="admin_test", password="123")
        response = self.client.get(reverse("app:lista_pacientes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/lista_pacientes.html")

    def test_lista_pacientes_paciente_recibe_403(self):
        """Un paciente normal recibe 403 (Prohibido)."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.get(reverse("app:lista_pacientes"))
        self.assertEqual(response.status_code, 403)

    def test_lista_pacientes_medico_recibe_403(self):
        """Un médico normal recibe 403 (Prohibido)."""
        self.client.login(username="medico_test", password="123")
        response = self.client.get(reverse("app:lista_pacientes"))
        self.assertEqual(response.status_code, 403)

    def test_lista_pacientes_busqueda_por_dni(self):
        """El admin puede buscar pacientes por DNI."""
        paciente_user = User.objects.create_user(
            username="juan", email="juan@test.com",
            password="123", tipo_usuario="paciente",
            first_name="Juan", last_name="Díaz"
        )
        Paciente.objects.create(
            usuario=paciente_user,
            dni="12345678",
            telefono="2901-11-11-11"
        )
        self.client.login(username="admin_test", password="123")
        response = self.client.get(reverse("app:lista_pacientes") + "?q=12345678")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["pacientes"]), 1)


class VistasDeAccionTest(TestCase):
    """Tests para vistas que realizan acciones (cancelar, confirmar, actualizar)."""

    def setUp(self):
        self.client = Client()
        self.user_paciente = User.objects.create_user(
            username="paciente_test", email="pac@test.com",
            password="123", tipo_usuario="paciente",
            first_name="Ana", last_name="Gómez"
        )
        self.user_medico = User.objects.create_user(
            username="medico_test", email="med@test.com",
            password="123", tipo_usuario="medico",
            first_name="Juan", last_name="Pérez"
        )
        self.user_otro = User.objects.create_user(
            username="otro_test", email="otro@test.com",
            password="123", tipo_usuario="paciente",
            first_name="Otro", last_name="Usuario"
        )
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        self.medico = Medico.objects.create(
            usuario=self.user_medico,
            matricula="MP-1001",
            especialidad=self.especialidad
        )
        self.paciente = Paciente.objects.create(
            usuario=self.user_paciente,
            dni="11222333",
            telefono="2901-11-11-11"
        )
        self.turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Consulta",
            estado="PENDIENTE"
        )

    # --- TurnoCancelView ---
    def test_cancelar_turno_paciente_propietario(self):
        """El paciente dueño del turno puede cancelarlo."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CANCELADO")

    def test_cancelar_turno_medico_propietario(self):
        """El médico dueño del turno puede cancelarlo."""
        self.client.login(username="medico_test", password="123")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CANCELADO")

    def test_cancelar_turno_otro_usuario_no_puede(self):
        """Un usuario que no es dueño del turno no puede cancelarlo."""
        otro_paciente = Paciente.objects.create(
            usuario=self.user_otro,
            dni="99999999",
            telefono="2901-99-99-99"
        )
        self.client.login(username="otro_test", password="123")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "PENDIENTE")  # No cambió

    def test_cancelar_turno_ya_cancelado_falla(self):
        """No se puede cancelar un turno que ya está cancelado."""
        self.turno.estado = "CANCELADO"
        self.turno.save()
        self.client.login(username="paciente_test", password="123")
        response = self.client.post(
            reverse("app:cancelar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CANCELADO")  # Sigue cancelado

    # --- TurnoConfirmarView ---
    def test_confirmar_turno_medico_propietario(self):
        """El médico dueño del turno puede confirmarlo."""
        self.client.login(username="medico_test", password="123")
        response = self.client.post(
            reverse("app:confirmar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    def test_confirmar_turno_paciente_no_puede(self):
        """Un paciente no puede confirmar un turno."""
        self.client.login(username="paciente_test", password="123")
        response = self.client.post(
            reverse("app:confirmar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "PENDIENTE")  # No cambió

    def test_confirmar_turno_admin_puede(self):
        """Un admin (is_staff) puede confirmar cualquier turno."""
        admin = User.objects.create_user(
            username="admin", email="admin@test.com",
            password="123", is_staff=True, tipo_usuario="admin"
        )
        self.client.login(username="admin", password="123")
        response = self.client.post(
            reverse("app:confirmar_turno", args=[self.turno.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    # --- TurnoUpdateView ---
    def test_actualizar_turno_paciente_propietario(self):
        """El paciente dueño del turno puede actualizarlo."""
        self.client.login(username="paciente_test", password="123")
        nueva_fecha = timezone.now() + timedelta(days=3)
        datos = {
            "medico": self.medico.pk,
            "fecha_hora": nueva_fecha.strftime("%Y-%m-%d %H:%M"),
            "motivo": "Consulta actualizada"
        }
        response = self.client.post(
            reverse("app:editar_turno", args=[self.turno.pk]),
            data=datos
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta actualizada")

    def test_actualizar_turno_ya_confirmado_falla(self):
        """No se puede actualizar un turno que ya está confirmado."""
        self.turno.estado = "CONFIRMADO"
        self.turno.save()
        self.client.login(username="paciente_test", password="123")
        datos = {
            "medico": self.medico.pk,
            "fecha_hora": (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "motivo": "Intento de actualización"
        }
        response = self.client.post(
            reverse("app:editar_turno", args=[self.turno.pk]),
            data=datos
        )
        self.assertEqual(response.status_code, 302)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta")  # No cambió


class VistasAusenciaTest(TestCase):
    """Tests para la vista de creación de ausencias."""

    def setUp(self):
        self.client = Client()
        self.user_medico = User.objects.create_user(
            username="medico_test", email="med@test.com",
            password="123", tipo_usuario="medico",
            first_name="Juan", last_name="Pérez"
        )
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        self.medico = Medico.objects.create(
            usuario=self.user_medico,
            matricula="MP-1001",
            especialidad=self.especialidad
        )

    def test_crear_ausencia_redirecciona_sin_login(self):
        """Sin login, redirige al login."""
        response = self.client.get(reverse("app:crear_ausencia"))
        self.assertEqual(response.status_code, 302)

    def test_crear_ausencia_con_login(self):
        """Con login, muestra el formulario de ausencias."""
        self.client.login(username="medico_test", password="123")
        response = self.client.get(reverse("app:crear_ausencia"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clinica/ausencia_form.html")

    def test_crear_ausencia_post_guarda_en_bd(self):
        """POST con datos válidos crea la ausencia."""
        self.client.login(username="medico_test", password="123")
        datos = {
            "medico": self.medico.pk,
            "motivo": "Congreso médico",
            "fecha_inicio": "2026-07-01",
            "fecha_fin": "2026-07-10"
        }
        response = self.client.post(reverse("app:crear_ausencia"), data=datos)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Ausencia.objects.filter(
                medico=self.medico,
                motivo="Congreso médico"
            ).exists()
        )

    def test_crear_ausencia_fechas_invalidas_falla(self):
        """POST con fecha_fin < fecha_inicio no crea la ausencia."""
        self.client.login(username="medico_test", password="123")
        datos = {
            "medico": self.medico.pk,
            "motivo": "Vacaciones",
            "fecha_inicio": "2026-07-10",
            "fecha_fin": "2026-07-01"  # ← Inválida
        }
        response = self.client.post(reverse("app:crear_ausencia"), data=datos)
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(Ausencia.objects.filter(medico=self.medico).exists())