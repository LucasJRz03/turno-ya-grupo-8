"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from django.utils import timezone

class Medico(models.Model):
    """Representa a un profesional médico disponible para turnos."""

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    class Meta:
        ordering = ["apellido", "nombre"]

    def __str__(self):
        """Retorna una etiqueta legible para listados y admin."""
        return f"Dr/a. {self.apellido}, {self.nombre}"

    def nombre_completo(self):
        """Retorna nombre y apellido concatenados."""
        return f"{self.nombre} {self.apellido}"

    def cantidad_turnos(self):
        """Retorna la cantidad total de turnos asociados a este médico."""
        if not hasattr(self, "turno_set"):
            return 0
        return self.turno_set.count()

    @classmethod
    def validate(cls, nombre, apellido, matricula, especialidad):
        """
        Valida los datos del médico. Retorna una lista de errores.
        Si la lista está vacía, los datos son válidos.
        """
        errors = []

        if not nombre or not nombre.strip():
            errors.append("El nombre es obligatorio.")

        if not apellido or not apellido.strip():
            errors.append("El apellido es obligatorio.")

        if not matricula or not matricula.strip():
            errors.append("La matrícula es obligatoria.")

        if not especialidad or not especialidad.strip():
            errors.append("La especialidad es obligatoria.")

        return errors

    @classmethod
    def new(cls, nombre, apellido, matricula, especialidad):
        """
        Crea y persiste un nuevo médico si los datos son válidos.
        Retorna (instancia, errors). Si hay errores, instancia es None.
        """
        errors = cls.validate(nombre, apellido, matricula, especialidad)
        if errors:
            return None, errors

        medico = cls.objects.create(
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            matricula=matricula.strip(),
            especialidad=especialidad.strip(),
        )
        return medico, []

    def update(self, nombre, apellido, matricula, especialidad):
        """
        Actualiza los datos del médico si los datos son válidos.
        Retorna una lista de errores. Si está vacía, la actualización fue exitosa.
        """
        errors = self.__class__.validate(nombre, apellido, matricula, especialidad)
        if errors:
            return errors

        self.nombre = nombre.strip()
        self.apellido = apellido.strip()
        self.matricula = matricula.strip()
        self.especialidad = especialidad.strip()
        self.save()
        return []

    # TODO: Agregar los siguientes modelos:
    # class Especialidad(models.Model): ...  ← extraer especialidad a FK
    # class Paciente(models.Model): ...
    class Turno(models.Model):
        """Representa un turno asignado a un médico y paciente."""

        ESTADO_CHOICES = [
            ("PENDIENTE", "Pendiente"),
            ("CONFIRMADO", "Confirmado"),
            ("CANCELADO", "Cancelado"),
        ]

        medico = models.ForeignKey("Medico", on_delete=models.CASCADE)
        paciente = models.ForeignKey("Paciente", on_delete=models.CASCADE)
        fecha_hora = models.DateTimeField()
        motivo = models.TextField()
        estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE")

        def __str__(self):
            return f"Turno de {self.paciente} con {self.medico} el {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"
        
        def validate(self):
            """Valida los datos del turno. Retorna una lista de errores."""
            errors = []

            if self.fecha_hora < timezone.now():
                errors.append("La fecha y hora del turno no pueden ser en el pasado.")

            if not self.motivo or not self.motivo.strip():
                errors.append("El motivo del turno es obligatorio.")

            return errors
        @classmethod
        def new(cls, **kwargs):
            """Crea un nuevo turno si los datos son válidos. Retorna (instancia, errors)."""
            turno = cls(**kwargs)
            errors = turno.validate()
            if errors:
                return None, errors
            turno.save()
            return turno, []
        
        def update(self, **kwargs) -> list[str]: 
            """Actualiza los datos del turno si son válidos. Retorna una lista de errores."""
            for attr, value in kwargs.items():
                setattr(self, attr, value)
            errors = self.validate()
            if errors:
                return errors
            self.save()
            return []