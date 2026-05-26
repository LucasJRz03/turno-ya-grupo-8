"""Pruebas unitarias del modelo Medico."""

from django.test import TestCase
from app.models import Medico, Turno
from django.utils import timezone
from datetime import timedelta


class MedicoModelTest(TestCase):
    """Verifica comportamiento básico y validaciones del modelo."""

    def setUp(self):
        self.medico = Medico.objects.create(
            nombre="Laura",
            apellido="Romero",
            matricula="MP-9999",
            especialidad="Pediatría",
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
        errors = Medico.validate("Ana", "García", "MP-0001", "Cardiología")
        self.assertEqual(errors, [])

    def test_validate_nombre_vacio_retorna_error(self):
        errors = Medico.validate("", "García", "MP-0001", "Cardiología")
        self.assertTrue(len(errors) > 0)

    def test_validate_matricula_vacia_retorna_error(self):
        errors = Medico.validate("Ana", "García", "", "Cardiología")
        self.assertTrue(len(errors) > 0)

    # --- new ---

    def test_new_crea_medico_con_datos_validos(self):
        medico, errors = Medico.new("Carlos", "López", "MP-1234", "Clínica Médica")
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
        self.assertEqual(self.medico.especialidad, "Cardiología")

    def test_update_con_datos_invalidos_no_modifica(self):
        errors = self.medico.update("", "", "", "")
        self.assertTrue(len(errors) > 0)
        self.medico.refresh_from_db()
        self.assertEqual(self.medico.nombre, "Laura")  # sin cambios

    # TODO: agregar tests para Paciente y Turno cuando los implementen

class TurnoModelTest(TestCase):
    """Pruebas para el modelo Turno (pendiente implementación)."""

    def setUp(self):
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
        self.turno.fecha_hora = timezone.now() - timedelta(days=1)
        errors = self.turno.validate()
        self.assertTrue(len(errors) > 0)

    def test_validate_fecha_futura_retorna_lista_vacia(self):
        self.turno.fecha_hora = timezone.now() + timedelta(days=1)
        errors = self.turno.validate()
        self.assertEqual(errors, [])

    def test_validate_estado_invalido_retorna_error(self):
        self.turno.estado = "INVALIDO"
        errors = self.turno.validate()
        self.assertTrue(len(errors) > 0)

    def test_validate_estado_valido_retorna_lista_vacia(self):
        self.turno.estado = "CONFIRMADO"
        errors = self.turno.validate()
        self.assertEqual(errors, [])

    def test_validate_motivo_vacio_retorna_error(self):
        self.turno.motivo = ""
        errors = self.turno.validate()
        self.assertTrue(len(errors) > 0)

    def test_validate_motivo_no_vacio_retorna_lista_vacia(self):
        self.turno.motivo = "Consulta general"
        errors = self.turno.validate()
        self.assertEqual(errors, [])

    def test_validate_todos_datos_validos_retorna_lista_vacia(self):
        self.turno.fecha_hora = timezone.now() + timedelta(days=1)
        self.turno.estado = "PENDIENTE"
        self.turno.motivo = "Consulta general"
        errors = self.turno.validate()
        self.assertEqual(errors, [])

    # --- new ---

    def new_crea_turno_con_datos_validos(self):
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

    def new_con_datos_invalidos_retorna_errores_y_no_crea(self):
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

    def update_modifica_datos_correctamente(self):
        errors = self.turno.update(
            medico=self.medico,
            paciente=self.paciente,
            fecha_hora=timezone.now() + timedelta(days=2),
            motivo="Consulta de seguimiento",
            estado="CONFIRMADO"
        )
        self.assertEqual(errors, [])
        self.turno.refresh_from_db()
        self.assertEqual(self.turno.motivo, "Consulta de seguimiento")
        self.assertEqual(self.turno.estado, "CONFIRMADO")

    def update_con_datos_invalidos_no_modifica(self):
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

    

    

    

        

    