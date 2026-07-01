"""Pruebas unitarias de los modelos de TurnoYa."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from app.models import (
    Medico, Turno, Paciente, Especialidad,
    Ausencia, ObraSocial, SolicitudMedico
)

User = get_user_model()

class EspecialidadModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def test_str_retorna_nombre(self):
        esp = Especialidad.objects.create(nombre="Cardiología")
        self.assertEqual(str(esp), "Cardiología")

    # --- validate ---
    def test_validate_nombre_vacio_retorna_error(self):
        errores = Especialidad.validate(nombre="")
        self.assertIn("El nombre de la especialidad es obligatorio.", errores)

    def test_validate_nombre_valido_retorna_lista_vacia(self):
        errores = Especialidad.validate(nombre="Neurología")
        self.assertEqual(errores, [])

    # --- new ---
    def test_new_crea_especialidad(self):
        esp, errores = Especialidad.new(nombre="Neurología")
        self.assertEqual(errores, [])
        self.assertEqual(esp.nombre, "Neurología")
        self.assertTrue(Especialidad.objects.filter(nombre="Neurología").exists())

    def test_new_con_nombre_vacio_no_crea(self):
        count_antes = Especialidad.objects.count()
        esp, errores = Especialidad.new(nombre="")
        self.assertIsNone(esp)
        self.assertTrue(len(errores) > 0)
        self.assertEqual(Especialidad.objects.count(), count_antes)

    # --- update ---
    def test_update_modifica_datos(self):
        esp = Especialidad.objects.create(nombre="Cardiología")
        errores = esp.update(nombre="Cardiología Intervencionista", descripcion="Actualizada")
        self.assertEqual(errores, [])
        esp.refresh_from_db()
        self.assertEqual(esp.nombre, "Cardiología Intervencionista")

class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="lauraromero",
            email="laura@gmail.com",
            password="testpass123",
            first_name="Laura",
            last_name="Romero"
        )
        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría",
            descripcion="Especialidad infantil"
        )
        self.medico = Medico.objects.create(
            usuario=self.user,
            matricula="MP-9999",
            especialidad=self.especialidad,
        )

    # --- __str__ y métodos simples ---
    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Romero", str(self.medico))
        self.assertIn("Laura", str(self.medico))

    def test_nombre_completo(self):
        self.assertEqual(self.medico.nombre_completo(), "Laura Romero")

    def test_cantidad_turnos_inicial_es_cero(self):
        self.assertEqual(self.medico.cantidad_turnos(), 0)

    # --- validate ---
    def test_validate_datos_correctos(self):
        errors = Medico.validate(self.user, "MP-0001", self.especialidad)
        self.assertEqual(errors, [])

    def test_validate_sin_usuario(self):
        errors = Medico.validate(None, "MP-0001", self.especialidad)
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_vacia(self):
        errors = Medico.validate(self.user, "", self.especialidad)
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_duplicada(self):
        """La matrícula debe ser única."""
        errors = Medico.validate(self.user, "MP-9999", self.especialidad)
        self.assertTrue(any("matrícula" in e.lower() for e in errors))

    def test_validate_matricula_duplicada_excluye_self(self):
        """Al actualizar, no debe fallar por la propia matrícula."""
        errors = Medico.validate(
            self.user, "MP-9999", self.especialidad,
            exclude_pk=self.medico.pk
        )
        self.assertEqual(errors, [])

    # --- new ---
    def test_new_crea_medico(self):
        nuevo_user = User.objects.create_user(
            username="carlos", email="carlos@gmail.com",
            password="pass1234", first_name="Carlos", last_name="López"
        )
        medico, errors = Medico.new(nuevo_user, "MP-1234", self.especialidad)
        self.assertEqual(errors, [])
        self.assertIsNotNone(medico)
        self.assertTrue(Medico.objects.filter(matricula="MP-1234").exists())

    def test_new_con_datos_invalidos_no_crea(self):
        count_antes = Medico.objects.count()
        medico, errors = Medico.new(None, "", "")
        self.assertIsNone(medico)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Medico.objects.count(), count_antes)

    # --- update ---
    def test_update_modifica_datos(self):
        """update() ahora usa **kwargs."""
        cardio = Especialidad.objects.create(nombre="Cardiología")
        errors = self.medico.update(matricula="MP-9999", especialidad=cardio)
        self.assertEqual(errors, [])
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.especialidad.nombre, "Cardiología")

    def test_update_matricula_duplicada_falla(self):
        """No se puede actualizar a una matrícula ya existente."""
        otro_user = User.objects.create_user(
            username="otro", email="otro@gmail.com",
            password="pass1234", first_name="Otro", last_name="User"
        )
        Medico.new(otro_user, "MP-5555", self.especialidad)

        errors = self.medico.update(matricula="MP-5555")
        self.assertTrue(len(errors) > 0)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.matricula, "MP-9999")  # No cambió

class PacienteModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="juandiaz",
            email="juan@gmail.com",
            password="12345",
            first_name="Juan",
            last_name="Díaz"
        )
        self.paciente = Paciente.objects.create(
            usuario=self.user,
            dni="123456789",
            telefono="2901-55-11-11"
        )

    # --- __str__ y métodos simples ---
    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Díaz", str(self.paciente))
        self.assertIn("Juan", str(self.paciente))

    def test_nombre_completo(self):
        self.assertEqual(self.paciente.nombre_completo(), "Juan Díaz")

    def test_dni(self):
        self.assertEqual(self.paciente.dni, "123456789")

    def test_telefono(self):
        self.assertEqual(self.paciente.telefono, "2901-55-11-11")

    # --- validate ---
    def test_validate_datos_correctos(self):
        errors = Paciente.validate(
            usuario=self.user, dni="987654321", telefono="2901-44-11-11"
        )
        self.assertEqual(errors, [])

    def test_validate_dni_vacio(self):
        errors = Paciente.validate(
            usuario=self.user, dni="", telefono="2901-44-11-11"
        )
        self.assertIn("El DNI es obligatorio.", errors)

    def test_validate_dni_no_numerico(self):
        errors = Paciente.validate(
            usuario=self.user, dni="ABC123", telefono=""
        )
        self.assertTrue(any("números" in e for e in errors))

    # --- new ---
    def test_new_crea_paciente(self):
        nuevo_user = User.objects.create_user(
            username="carlos", email="carlos@gmail.com",
            password="contra123", first_name="Carlos", last_name="López"
        )
        paciente, errors = Paciente.new(
            usuario=nuevo_user, dni="11223344", telefono="2901-44-22-22"
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(paciente)
        # El nombre viene del CustomUser, no del Paciente
        self.assertEqual(paciente.usuario.first_name, "Carlos")
        self.assertEqual(Paciente.objects.count(), 2)

    def test_new_con_datos_invalidos_no_crea(self):
        datos_user = User.objects.create_user(
            username="pepe", email="pepe@gmail.com", password="hola"
        )
        paciente, errors = Paciente.new(
            usuario=datos_user, dni="", telefono=""
        )
        self.assertIsNone(paciente)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Paciente.objects.count(), 1)

    # --- update ---
    def test_update_modifica_datos_correctamente(self):
        """update() solo modifica dni y telefono (usuario no se puede cambiar)."""
        errors = self.paciente.update(
            dni="123456789",
            telefono="2901-55-11-11"
        )
        self.assertEqual(errors, [])
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.dni, "123456789")
        self.assertEqual(self.paciente.telefono, "2901-55-11-11")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.paciente.update(
            dni="ACB123456",
            telefono="Telefono celular"
        )
        self.assertTrue(len(errors) > 0)
        self.paciente.refresh_from_db()
        # El nombre viene del CustomUser (no cambió)
        self.assertEqual(self.paciente.usuario.first_name, "Juan")

class TurnoModelTest(TestCase):
    """Pruebas para el modelo Turno."""

    def setUp(self):
        self.usuario_medico = User.objects.create_user(
            username="lauraromero", email="laura@gmail.com",
            password="testpass", first_name="Laura", last_name="Romero"
        )
        self.usuario_paciente = User.objects.create_user(
            username="juanperez", email="juan@gmail.com",
            password="testpass", first_name="Juan", last_name="Pérez"
        )
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
        self.medico = Medico.objects.create(
            usuario=self.usuario_medico,
            matricula="MP-9999",
            especialidad=self.especialidad
        )
        self.paciente = Paciente.objects.create(
            usuario=self.usuario_paciente,
            dni="12345678",
            telefono="2901-11-11-11"
        )
        self.turno = Turno.objects.create(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Consulta general",
            estado="PENDIENTE",
        )

    # --- __str__ ---
    def test_str_incluye_paciente_medico_fecha(self):
        self.assertIn(str(self.turno.paciente), str(self.turno))
        self.assertIn(str(self.turno.medico), str(self.turno))
        self.assertIn(
            self.turno.fecha_hora.strftime('%Y-%m-%d %H:%M'),
            str(self.turno)
        )

    # --- validate ---
    def test_validate_fecha_pasada(self):
        fecha_pasada = timezone.now() - timedelta(days=1)
        errors = Turno.validate(
            self.medico, self.paciente, fecha_pasada,
            self.turno.motivo, self.turno.estado
        )
        self.assertTrue(len(errors) > 0)

    def test_validate_fecha_futura(self):
        errors = Turno.validate(
            self.medico, self.paciente, self.turno.fecha_hora,
            self.turno.motivo, self.turno.estado
        )
        self.assertEqual(errors, [])

    def test_validate_estado_invalido(self):
        errors = Turno.validate(
            self.medico, self.paciente, self.turno.fecha_hora,
            self.turno.motivo, "INVALIDO"
        )
        self.assertTrue(len(errors) > 0)

    def test_validate_sin_medico(self):
        errors = Turno.validate(
            None, self.paciente, self.turno.fecha_hora,
            self.turno.motivo, "PENDIENTE"
        )
        self.assertTrue(any("médico" in e.lower() or "obligatorio" in e.lower() for e in errors))

    # --- new ---
    def test_new_crea_turno(self):
        turno, errors = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=2),
            motivo="Consulta general",
            estado="PENDIENTE"
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(turno)
        self.assertTrue(Turno.objects.filter(id=turno.id).exists())

    def test_new_con_fecha_pasada_no_crea(self):
        count_antes = Turno.objects.count()
        turno, errors = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() - timedelta(days=1),
            motivo="",
            estado="PENDIENTE"
        )
        self.assertIsNone(turno)
        self.assertEqual(Turno.objects.count(), count_antes)

    # --- update ---
    def test_update_modifica_datos(self):
        errors = self.turno.update(
            motivo="Consulta de seguimiento",
            estado="CONFIRMADO"
        )
        self.assertEqual(errors, [])
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta de seguimiento")
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    # --- cancelar / confirmar ---
    def test_cancelar_turno_pendiente(self):
        exito, errors = self.turno.cancelar()
        self.assertTrue(exito)
        self.assertEqual(errors, [])
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CANCELADO")

    def test_cancelar_turno_ya_cancelado_falla(self):
        self.turno.estado = "CANCELADO"
        self.turno.save()
        exito, errors = self.turno.cancelar()
        self.assertFalse(exito)
        self.assertTrue(len(errors) > 0)

    def test_confirmar_turno_pendiente(self):
        exito, errors = self.turno.confirmar()
        self.assertTrue(exito)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    def test_confirmar_turno_ya_confirmado_falla(self):
        self.turno.estado = "CONFIRMADO"
        self.turno.save()
        exito, errors = self.turno.confirmar()
        self.assertFalse(exito)
        self.assertTrue(len(errors) > 0)

    def test_validar_superposicion_de_turnos(self):
        """Dos turnos con el mismo médico a la misma hora deben fallar."""
        misma_hora = timezone.now() + timedelta(days=5)
        self.turno.fecha_hora = misma_hora
        self.turno.save()

        turno2, errors = Turno.new(
            medico=self.medico, paciente=self.paciente,
            fecha_hora=misma_hora, motivo="Otro turno", estado="PENDIENTE"
        )
        self.assertIsNone(turno2)
        self.assertTrue(any("ya tiene un turno" in e for e in errors))

class AusenciaModelTest(TestCase):
    """Pruebas unitarias para el modelo Ausencia."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="lauraromero", email="laura@gmail.com",
            password="testpass123", first_name="Laura", last_name="Romero"
        )
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
        self.medico = Medico.objects.create(
            usuario=self.user, matricula="MP-9999",
            especialidad=self.especialidad
        )

    # --- validate (ahora es @classmethod) ---
    def test_validate_fechas_invalidas(self):
        """La fecha de inicio no puede ser posterior a la de fin."""
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio - timedelta(days=2)
        errores = Ausencia.validate(
            self.medico, "Vacaciones", fecha_inicio, fecha_fin
        )
        self.assertIn("La fecha fin no puede ser mayor a la fecha de inicio.", errores)

    def test_validate_motivo_vacio(self):
        errores = Ausencia.validate(
            self.medico, "", timezone.now().date(),
            timezone.now().date() + timedelta(days=1)
        )
        self.assertIn("El motivo no puede estar vacío.", errores)

    def test_validate_sin_medico(self):
        errores = Ausencia.validate(
            None, "Congreso",
            timezone.now().date(),
            timezone.now().date() + timedelta(days=1)
        )
        self.assertTrue(len(errores) > 0)

    # --- new ---
    def test_new_crea_ausencia_correcta(self):
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=5)
        ausencia, errores = Ausencia.new(
            self.medico, "Congreso", fecha_inicio, fecha_fin
        )
        self.assertEqual(errores, [])
        self.assertIsNotNone(ausencia)
        self.assertEqual(ausencia.motivo, "Congreso")

    def test_new_con_fechas_invalidas_no_crea(self):
        count_antes = Ausencia.objects.count()
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio - timedelta(days=2)  # ← Inválida
        ausencia, errores = Ausencia.new(
            self.medico, "Vacaciones", fecha_inicio, fecha_fin
        )
        self.assertIsNone(ausencia)
        self.assertEqual(Ausencia.objects.count(), count_antes)

    # --- update ---
    def test_update_modifica_ausencia(self):
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=5)
        ausencia, _ = Ausencia.new(
            self.medico, "Congreso", fecha_inicio, fecha_fin
        )
        errores = ausencia.update(motivo="Congreso actualizado")
        self.assertEqual(errores, [])
        ausencia.refresh_from_db()
        self.assertEqual(ausencia.motivo, "Congreso actualizado")

class ObraSocialModelTest(TestCase):
    """Pruebas unitarias para el modelo ObraSocial."""

    # --- validate (ahora es @classmethod) ---
    def test_validate_nombre_vacio(self):
        errores = ObraSocial.validate(nombre="")
        self.assertIn("El nombre de la obra social no puede estar vacío.", errores)

    def test_validate_nombre_valido(self):
        errores = ObraSocial.validate(nombre="OSDE")
        self.assertEqual(errores, [])

    # --- new ---
    def test_new_crea_obra_social(self):
        obra_social, errores = ObraSocial.new(nombre="OSDE", requiere_token=True)
        self.assertEqual(errores, [])
        self.assertEqual(obra_social.nombre, "OSDE")
        self.assertTrue(obra_social.requiere_token)

    def test_new_con_nombre_vacio_no_crea(self):
        count_antes = ObraSocial.objects.count()
        obra_social, errores = ObraSocial.new(nombre="")
        self.assertIsNone(obra_social)
        self.assertEqual(ObraSocial.objects.count(), count_antes)

    def test_new_con_medicos_asociados(self):
        """Se pueden asociar médicos al crear la obra social."""
        user = User.objects.create_user(
            username="medico1", email="medico1@gmail.com",
            password="pass1234", first_name="Medico", last_name="Test"
        )
        esp = Especialidad.objects.create(nombre="Cardiología")
        medico, _ = Medico.new(user, "MP-1111", esp)

        obra_social, errores = ObraSocial.new(
            nombre="Swiss Medical", medicos=[medico]
        )
        self.assertEqual(errores, [])
        self.assertIn(medico, obra_social.medicos_disponibles.all())

class SolicitudMedicoModelTest(TestCase):
    """Pruebas para el modelo SolicitudMedico."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="paciente1",
            email="paciente1@gmail.com",
            password="pass1234",
            tipo_usuario='paciente',
            first_name="Juan",
            last_name="Pérez"
        )
        self.especialidad = Especialidad.objects.create(nombre='Cardiología')

    # --- new ---
    def test_new_solicitud_valida(self):
        """new() crea una solicitud correctamente."""
        solicitud, errors = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, 'PENDIENTE')

    def test_new_solicitud_matricula_duplicada_en_medico(self):
        """new() falla si la matrícula ya existe en un médico."""
        medico_user = User.objects.create_user(
            username="medico1", email="medico1@gmail.com",
            password="pass1234", tipo_usuario='medico'
        )
        Medico.new(
            usuario=medico_user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )

        solicitud, errors = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )
        self.assertIsNone(solicitud)
        self.assertTrue(any('matrícula' in e.lower() for e in errors))

    def test_new_solicitud_usuario_no_paciente(self):
        """new() falla si el usuario no es paciente."""
        self.user.tipo_usuario = 'medico'
        self.user.save()

        solicitud, errors = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )
        self.assertIsNone(solicitud)
        self.assertTrue(any('paciente' in e.lower() for e in errors))

    # --- aprobar ---
    def test_aprobar_solicitud_crea_medico(self):
        """aprobar() crea el médico y cambia el rol del usuario."""
        solicitud, _ = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )

        exito, errors = solicitud.aprobar(comentario='Aprobado')
        self.assertTrue(exito)
        self.assertEqual(errors, [])

        # Verificar que se creó el médico
        self.assertTrue(Medico.objects.filter(usuario=self.user).exists())

        # Verificar que el usuario ahora es médico
        self.user.refresh_from_db()
        self.assertEqual(self.user.tipo_usuario, 'medico')

        # Verificar que la solicitud está aprobada
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'APROBADO')
        self.assertIsNotNone(solicitud.fecha_resolucion)

    # --- rechazar ---
    def test_rechazar_solicitud(self):
        """rechazar() no crea el médico."""
        solicitud, _ = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )

        exito, errors = solicitud.rechazar(comentario='Documentación incompleta')
        self.assertTrue(exito)
        self.assertEqual(errors, [])

        # Verificar que NO se creó el médico
        self.assertFalse(Medico.objects.filter(usuario=self.user).exists())

        # Verificar que el usuario sigue siendo paciente
        self.user.refresh_from_db()
        self.assertEqual(self.user.tipo_usuario, 'paciente')

        # Verificar que la solicitud está rechazada
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, 'RECHAZADO')
        self.assertEqual(solicitud.comentario_admin, 'Documentación incompleta')

    # --- Edge cases ---
    def test_no_puede_aprobar_solicitud_ya_resuelta(self):
        """No se puede aprobar una solicitud ya resuelta."""
        solicitud, _ = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )
        solicitud.aprobar()

        # Intentar aprobar de nuevo
        exito, errors = solicitud.aprobar()
        self.assertFalse(exito)
        self.assertTrue(len(errors) > 0)

    def test_no_puede_rechazar_solicitud_ya_aprobada(self):
        """No se puede rechazar una solicitud ya aprobada."""
        solicitud, _ = SolicitudMedico.new(
            usuario=self.user,
            matricula='MP-12345',
            especialidad=self.especialidad
        )
        solicitud.aprobar()

        exito, errors = solicitud.rechazar()
        self.assertFalse(exito)
        self.assertTrue(len(errors) > 0)