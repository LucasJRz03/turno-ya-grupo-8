"""Pruebas unitarias del modelo Medico."""

from django.test import TestCase
from app.models import Medico, Turno, Paciente, Especialidad, Ausencia, ObraSocial
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
User = get_user_model()



class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):

        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría",
            descripcion="Especialidad que se encarga de la salud de los niños")
        
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
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

    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = Medico.validate("Ana", "García", "MP-0001", "Pediatría")
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        errors = Medico.validate("", "García", "MP-0001", "Pediatría")
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_vacia_retorna_error(self):
        errors = Medico.validate("Ana", "García", "", "Pediatría")
        self.assertTrue(len(errors) > 0)

    # --- new ---

    def test_new_crea_medico_con_datos_validos(self):
        medico, errors = Medico.new("Carlos", "López", "MP-1234", "Cardiología")
        self.assertEqual(errors, [])
        self.assertIsNotNone(medico)
        self.assertEqual(medico.apellido, "López")
        self.assertTrue(Medico.objects.filter(matricula="MP-1234").exists())

    def test_new_con_datos_invalidos_retorna_errores_y_no_crea(self):
        count_antes = Medico.objects.count()
        medico, errors = Medico.new("", "", "", "")
        self.assertIsNone(medico)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Medico.objects.count(), count_antes)

    # --- update ---

    def test_update_modifica_datos_correctamente(self):
        errors = self.medico.update("Laura", "Romero", "MP-9999", "Cardiología")
        self.assertEqual(errors, [])
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.especialidad.nombre, "Cardiología")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.medico.update("", "", "", "")
        self.assertTrue(len(errors) > 0)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.nombre, "Laura") 

class TurnoModelTest(TestCase):
    """Pruebas para el modelo Turno."""
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="juanperez", 
            password="testpass")
        
        self.especialidad = Especialidad.objects.create(
            nombre="Pediatría",
            descripcion="Especialidad que se encarga de la salud de los niños")
        
        self.paciente = Paciente.objects.create(
            usuario=self.usuario,
            nombre="Juan",
            apellido="Pérez",
            dni="12345678"
        )
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad=self.especialidad
        )
        self.turno = Turno.objects.create(
            medico = self.medico,
            paciente = self.paciente,
            fecha_hora = timezone.now() + timedelta(days=1),
            motivo = "Consulta general",
            estado = "PENDIENTE",
        )
    # --- __str__ y métodos simples ---

    def test_str_incluye_paciente_medico_fecha(self):
        self.assertIn(str(self.turno.paciente), str(self.turno))
        self.assertIn(str(self.turno.medico), str(self.turno))
        self.assertIn(self.turno.fecha_hora.strftime('%Y-%m-%d %H:%M'), str(self.turno))

    # --- validate ---
    def test_validate_fecha_pasada_retorna_error(self):
        fecha_pasada = timezone.now() - timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_pasada, "Consulta", "PENDIENTE")
        self.assertTrue(len(errors) > 0)

    def test_validate_fecha_futura_retorna_lista_vacia(self):
        fecha_futura = timezone.now() + timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_futura, "Consulta", "PENDIENTE")
        self.assertEqual(errors, [])
 
    def test_validate_estado_invalido_retorna_error(self):
        fecha_futura = timezone.now() + timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_futura, "Consulta", "INVALIDO")
        self.assertTrue(len(errors) > 0)

    def test_validate_estado_valido_retorna_lista_vacia(self):
        fecha_futura = timezone.now() + timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_futura, "Consulta", "CONFIRMADO")
        self.assertEqual(errors, [])

    def test_validate_motivo_no_vacio_retorna_lista_vacia(self):
        fecha_futura = timezone.now() + timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_futura, "Consulta", "PENDIENTE")
        self.assertEqual(errors, [])

    def test_validate_todos_datos_validos_retorna_lista_vacia(self):
        fecha_futura = timezone.now() + timedelta(days=1)
        errors = Turno.validate(self.medico, self.paciente, fecha_futura, "Consulta general", "PENDIENTE")
        self.assertEqual(errors, [])

    # --- new ---

    def test_new_crea_turno_con_datos_validos(self):
        turno, errors = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=1),
            motivo="Consulta general",
            estado="PENDIENTE"
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(turno)
        self.assertTrue(Turno.objects.filter(id=turno.id).exists())

    def test_new_con_datos_invalidos_retorna_errores_y_no_crea(self):
        count_antes = Turno.objects.count()
        turno, errors = Turno.new(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() - timedelta(days=1),  # fecha pasada
            motivo="",
            estado="INVALIDO"
        )
        self.assertIsNone(turno)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Turno.objects.count(), count_antes)

    # --- update ---

    def test_update_modifica_datos_correctamente(self):
        errors = self.turno.update(
            motivo="Consulta de seguimiento",
            estado="CONFIRMADO"
        )
        self.assertEqual(errors, [])
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta de seguimiento")
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    def test_cancelar_turno(self):
        """Verifica que el método cancelar cambie el estado correctamente."""
        self.turno.cancelar()
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CANCELADO")

    def test_confirmar_turno(self):
        """Verifica que el método confirmar cambie el estado correctamente."""
        self.turno.confirmar()
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.turno.update(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() - timedelta(days=1),  # fecha pasada
            motivo="",
            estado="INVALIDO"
        )
        self.assertTrue(len(errors) > 0)
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta general")  # sin cambios
        self.assertEqual(self.turno.estado, "PENDIENTE")  # sin cambios

class PacienteModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):
        self.user = User.objects.create_user(username="jaundias", password="12345")
        self.paciente = Paciente.objects.create(
            usuario = self.user,
            nombre = "Juan",
            apellido="Díaz",
            dni = "123456789",
            email = "juanDiaz@gmail.com",
            telefono = "2901-55-11-11"
        )

    def test_str_incluye_apellido_y_nombre(self):
        self.assertIn("Díaz", str(self.paciente))
        self.assertIn("Juan", str(self.paciente))

    def test_nombre_completo(self):
        self.assertEqual(self.paciente.nombre_completo(), "Juan Díaz")

  
    def test_dni(self):
        self.assertEqual(self.paciente.dni, "123456789")
    
    def test_email(self):
        self.assertEqual(self.paciente.email, "juanDiaz@gmail.com")
    
    def test_telefono(self):
        self.assertEqual(self.paciente.telefono, "2901-55-11-11")
    
    # --- validate ----
    def test_validate_datos_correctos_retorna_lista_vacia(self):
        errors = Paciente.validate(
            usuario=self.user,
            nombre="Ana",
            apellido="Pacheco",
            dni="987654321",
            email="ana@gmail.com",
            telefono="2901-44-11-11"
        )
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        errors = Paciente.validate(
            usuario=self.user,
            nombre="",
            apellido="Pacheco",
            dni="987654321",
            email="ana@gmail.com",
            telefono="2901-44-11-11"
        )
        self.assertIn("El nombre es obligatorio.", errors)

    def test_validate_dni_vacio_retorna_error(self):
        errors = Paciente.validate(
            usuario=self.user,
            nombre="Ana",
            apellido="Pacheco",
            dni="",
            email="ana@gmail.com",
            telefono="2901-44-11-11"
        )
        self.assertIn("El DNI es obligatorio.", errors)

    # --- new ---
    def test_new_crea_paciente_con_datos_validos(self):
        nuevo_user = User.objects.create_user(username="carloslopes", email="carloslopes@test.com",  password="contra123")
        paciente, errors = Paciente.new(
            usuario=nuevo_user,
            nombre="Carlos",
            apellido="López",
            dni="11223344",
            email="carlos@gmail.com",
            telefono="2901-44-22-22"
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente.nombre, "Carlos")
        # Debería haber 2 pacientes ahora, Juan y Carlos
        self.assertEqual(Paciente.objects.count(), 2)

    def test_new_con_datos_invalidos_retorna_errores_y_no_crea(self):
        datos_user = User.objects.create_user(username="pepe", email="pepe@test.com", password="hola")
        paciente, errors = Paciente.new(
            usuario=datos_user,
            nombre="",
            apellido="Gómez",
            dni="112233445",
            email="carlos@gmail.com", 
            telefono=""
        )
        self.assertIsNone(paciente)
        self.assertTrue(len(errors) > 0)
        self.assertEqual(Paciente.objects.count(), 1) # Solo Juan

    # --- update ---
    def test_update_modifica_datos_correctamente(self): 
        errors = self.paciente.update(
            usuario=self.user,
            nombre="Juan Cruz",
            apellido="Díaz",
            dni="123456789",
            email="juanCruz@gmail.com",
            telefono="2901-55-11-11"
        )
        self.assertEqual(errors, [])

        # Refrescar desde la base de datos para asegurar que se guardó
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nombre, "Juan Cruz")
        self.assertEqual(self.paciente.email, "juanCruz@gmail.com")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.paciente.update(
            usuario=self.user,           
            nombre="",
            apellido="Díaz",
            dni="123456789",
            email="juanCruz@gmail.com",
            telefono="2901-55-11-11"
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

    def test_new_crea_especialidad(self):
        esp, errores = Especialidad.new(nombre="Neurología")
        self.assertEqual(errores,[])
        self.assertEqual(esp.nombre, "Neurología")

class AusenciaModelTest(TestCase):
    """Pruebas unitarias para el modelo Ausencia."""

    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="Pediatría")
        self.medico = Medico.objects.create(
            nombre="Laura", apellido="Romero", matricula="MP-9999", especialidad=self.especialidad
        )

    def test_validate_fechas_invalidas(self):
        """La fecha de inicio no puede ser posterior a la de fin."""
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio - timedelta(days=2)
        
        ausencia = Ausencia(medico=self.medico, motivo="Vacaciones", fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        errores = ausencia.validate()
        self.assertIn("La fecha fin no puede ser mayor a la fecha de inicio.", errores)

    def test_new_crea_ausencia_correcta(self):
        fecha_inicio = timezone.now().date()
        fecha_fin = fecha_inicio + timedelta(days=5)
        ausencia, errores = Ausencia.new(self.medico, "Congreso", fecha_inicio, fecha_fin)
        self.assertEqual(errores, [])
        self.assertIsNotNone(ausencia)
        self.assertEqual(ausencia.motivo, "Congreso")

class ObraSocialModelTest(TestCase):
    """Pruebas unitarias para el modelo ObraSocial."""

    def test_validate_nombre_vacio(self):
        os = ObraSocial(nombre="")
        errores = os.validate()
        self.assertIn("El nombre de la obra social no puede estar vacío.", errores)

    def test_new_crea_obra_social(self):
        os, errores = ObraSocial.new(nombre="OSDE", requiere_token=True)
        self.assertEqual(errores, [])
        self.assertEqual(os.nombre, "OSDE")
        self.assertTrue(os.requiere_token)