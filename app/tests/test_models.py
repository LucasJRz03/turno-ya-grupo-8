"""Pruebas unitarias del modelo Medico."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Medico, Turno, Paciente, Especialidad
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

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
            descripcion="Especialidad infantil")
        
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

    # --- new ---
    def test_new_crea_medico(self):
        nuevo_user = User.objects.create_user(
            username="carlos",email="carlos@gmail.com", password="pass1234", first_name="Carlos", last_name="López"
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
        cardio = Especialidad.objects.create(nombre="Cardiología")
        errors = self.medico.update("MP-9999", cardio)
        self.assertEqual(errors, [])
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.especialidad.nombre, "Cardiología")

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
    # --- __str__ y métodos simples ---

    def test_str_incluye_paciente_medico_fecha(self):
        self.assertIn(str(self.turno.paciente), str(self.turno))
        self.assertIn(str(self.turno.medico), str(self.turno))
        self.assertIn(self.turno.fecha_hora.strftime('%Y-%m-%d %H:%M'), str(self.turno))

    # --- validate ---
    def test_validate_fecha_pasada(self):
        self.turno.fecha_hora = timezone.now() - timedelta(days=1)
        errors = self.turno.validate()
        self.assertTrue(len(errors) > 0)

    def test_validate_fecha_futura(self):
        self.turno.fecha_hora = timezone.now() + timedelta(days=1)
        errors = self.turno.validate()
        self.assertEqual(errors, [])

    def test_validate_estado_invalido(self):
        self.turno.estado = "INVALIDO"
        errors = self.turno.validate()
        self.assertTrue(len(errors) > 0)
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
            fecha_hora=timezone.now() - timedelta(days=1),  # fecha pasada
            motivo="",
            estado="INVALIDO"
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
    
    # --- validate ----
    def test_validate_datos_correctos(self):
        errors = Paciente.validate(
            usuario=self.user,
            dni="987654321",
            telefono="2901-44-11-11"
        )
        self.assertEqual(errors, [])

    def test_validate_dni_vacio(self):
        errors = Paciente.validate(
            usuario=self.user,
            dni="",
            telefono="2901-44-11-11"
        )
        self.assertIn("El DNI es obligatorio.", errors)

    def test_validate_dni_no_numerico(self):
        errors = Paciente.validate(
            usuario=self.user,
            dni="ABC123", 
            telefono=""
        )
        self.assertTrue(any("números" in e for e in errors))

    # --- new ---
    def test_new_crea_paciente(self):
        nuevo_user = User.objects.create_user(username="carlos", email="carlos@gmail.com", password="contra123", first_name="Carlos", last_name="López")
        paciente, errors = Paciente.new(
            usuario=nuevo_user,
            dni="11223344",
            telefono="2901-44-22-22"
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente.nombre, "Carlos")
        # Debería haber 2 pacientes ahora, Juan y Carlos
        self.assertEqual(Paciente.objects.count(), 2)

    def test_new_con_datos_invalidos_no_crea(self):
        datos_user = User.objects.create_user(username="pepe", email="pepe@gmail.com", password="hola")
        paciente, errors = Paciente.new(
            usuario=datos_user,
            dni="",
            telefono=""
        )
        self.assertIsNone(paciente)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Paciente.objects.count(), 1)

    # --- update ---
    def test_update_modifica_datos_correctamente(self): 
        errors = self.paciente.update(
            usuario=self.user,
            dni="123456789",
            telefono="2901-55-11-11"
        )
        self.assertEqual(errors, [])
        # Refrescar desde la base de datos para asegurar que se guardó
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.dni,"123456789" )
        self.assertEqual(self.paciente.telefono, "2901-55-11-11")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.paciente.update(
            usuario=self.user,           
            dni="ACB123456",
            telefono="Telefono celular"
        )
        self.assertTrue(len(errors) > 0)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, "Juan") # sin cambios

class EspecialidadModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""
    
    def test_str_retorna_nombre(self):
        esp = Especialidad.objects.create(nombre="Cardiología")
        self.assertEqual(str(esp), "Cardiología")
        
    # --- validate ----
    def test_validate_nombre_vacio_retorna_error(self):
        errores = Especialidad.validate(nombre="")
        self.assertIn("El nombre de la especialidad es obligatorio.", errores)

    def test_validate_nombre_valido_retorna_lista_vacia(self):
        errores = Especialidad.validate(nombre="Neurología")
        self.assertEqual(errores, [])

    # --- new ---
    def test_new_crea_especialidad(self):
        esp, errores = Especialidad.new(nombre="Neurología")
        self.assertEqual(errores,[])
        self.assertEqual(esp.nombre, "Neurología")
        self.assertTrue(Especialidad.objects.filter(nombre= "Neurologia"))

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