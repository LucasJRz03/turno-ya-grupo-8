"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from django.utils import timezone

class Especialidad(models.Model):
    """Representa un área de espcialización médica."""
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
    @classmethod
    def validate(cls, nombre, descripcion=""):
        errors = []
        if not nombre or not str(nombre).strip(): 
            errors.append("El nombre de la especialidad es obligatorio.")
        return errors

    @classmethod
    def new(cls, nombre, descripcion=""):    
        errors = cls.validate(nombre, descripcion)
        if errors:
            return None, errors
        especialidad = cls.objects.create(
            nombre=str(nombre).strip(), 
            descripcion=str(descripcion).strip()
        )
        return especialidad, [] 

    def update(self, nombre, descripcion=""):
        errors = self.__class__.validate(nombre, descripcion)
        if errors:
            return errors
        self.nombre = str(nombre).strip()
        self.descripcion = str(descripcion).strip()
        self.save()
        return []
  
class Medico(models.Model):
    """Representa a un profesional médico disponible para turnos."""

    usuario = models.OneToOneField('accounts.CustomUser', on_delete=models.PROTECT, null=True, blank=True, related_name= 'medico')
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.ForeignKey('Especialidad', on_delete=models.PROTECT, related_name='medicos')
    class Meta:
        ordering = ["usuario__last_name", "usuario__first_name"]

    def __str__(self):
        """Retorna una etiqueta legible para listados y admin."""
        if self.usuario:
            return f"Dr/a. {self.usuario.last_name}, {self.usuario.first_name}"
        return f"Dr/a. (sin usuario asociado) - Mat. {self.matricula}"

    def nombre_completo(self):
        """(Delegado al CustomUser) Retorna nombre y apellido concatenados."""
        if self.usuario:
            return self.usuario.nombre_completo()
        return "Sin nombre"

    def cantidad_turnos(self):
        """Retorna la cantidad total de turnos asociados a este médico."""
        if not hasattr(self, "turno_set"):
            return 0
        return self.turno_set.count()

    @classmethod
    def validate(cls, usuario, matricula, especialidad):
        """Valida los datos del médico. Retorna una lista de errores.
        Si la lista está vacía, los datos son válidos."""

        errors = []

        if not usuario:
            errors.append("El usuario asociado es obligatorio")

        if not matricula or not matricula.strip():
            errors.append("La matrícula es obligatoria.")

        # `especialidad` puede ser una instancia de Especialidad o un nombre (string)
        if isinstance(especialidad, Especialidad):
            pass
        else:
            if not especialidad or not str(especialidad).strip():
                errors.append("La especialidad es obligatoria.")

        if matricula:
            qs = cls.objects.filter(matricula=str(matricula).strip())
            if qs.exists():
                errors.append("Ya existe un médico con esa matrícula.")

        return errors

    @classmethod
    def new(cls, usuario, matricula, especialidad):
        """Crea y persiste un nuevo médico si los datos son válidos.
        Retorna (instancia, errors). Si hay errores, instancia es None."""

        errors = cls.validate(usuario, matricula, especialidad)
        if errors:
            return None, errors

        # Resolver `especialidad`: si viene como string, buscar o crear la Especialidad
        if isinstance(especialidad, Especialidad):
            esp = especialidad
        else:
            esp, _ = Especialidad.objects.get_or_create(
                nombre=str(especialidad).strip(), defaults={"descripcion": ""}
            )

        medico = cls.objects.create(
            usuario=usuario,
            matricula=matricula.strip(),
            especialidad=esp,
        )
        return medico, []

    def update(self, matricula, especialidad):
        """Actualiza los datos del médico si los datos son válidos.
        Retorna una lista de errores. Si está vacía, la actualización fue exitosa."""
        errors = self.__class__.validate(self.usuario, matricula, especialidad)
        if errors:
            return errors
        
        self.matricula = matricula.strip()
        # Resolver especialidad a instancia si se pasa como nombre
        if isinstance(especialidad, Especialidad):
            esp = especialidad
        else:
            esp, _ = Especialidad.objects.get_or_create(nombre=str(especialidad).strip(), defaults={"descripcion": ""})

        self.especialidad = esp
        self.save()
        return []
    
class Paciente(models.Model):
    """Representa a un paciente registrado en el sistema."""

    usuario = models.OneToOneField('accounts.CustomUser', on_delete=models.PROTECT, related_name='paciente')
    dni = models.CharField(max_length=25, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
     
    def __str__(self):
        if self.usuario:
            return f"{self.usuario.last_name}, {self.usuario.first_name} (DNI: {self.dni})"
        return f"Paciente DNI: {self.dni}"

    def nombre_completo(self):
        """Retorna nombre y apellido concatenados."""
        if self.usuario:
            return self.usuario.nombre_completo()
        return "Sin nombre"
    
    @classmethod
    def validate(cls, usuario, dni, telefono=None):
        """Valida los datos del paciente."""

        errors = []

        if not usuario:
            errors.append("El usuario asociado es obligatorio.")
        
        if not dni or not str(dni).strip():
            errors.append("El DNI es obligatorio.")
        else:
            # Valida que el DNI solo contenga números
            dni_limpio = str(dni).strip()
            if not dni_limpio.isdigit():
                errors.append("El DNI solo debe contener números.")

        if telefono:
            telefono_limpio = str(telefono).replace(' ', '').replace('-', '').replace('+', '')
            if not telefono_limpio.isdigit():
                errors.append("El teléfono solo debe contener números, espacios, guiones y +.")

        return errors

    @classmethod
    def new(cls, usuario, dni, telefono=None):
        """Crea un nuevo paciente."""

        errors = cls.validate(usuario, dni, telefono)
        if errors:
            return None, errors
        
        paciente = cls.objects.create(
            usuario=usuario,
            dni=str(dni).strip(),
            telefono=str(telefono).strip() if telefono else ""
        )
        return paciente, []

    def update(self, dni, telefono=None):
        """Actualiza los datos del paciente."""
        errors = self.__class__.validate(self.usuario, dni, telefono)
        if errors:
            return errors
        
        self.dni = str(dni).strip()
        self.telefono = str(telefono).strip() if telefono else ""
        self.save()
        return []
class Turno(models.Model): 
    """Representa un turno asignado a un médico y paciente."""

    ESTADO_CHOICES = [
            ("PENDIENTE", "Pendiente"),
            ("CONFIRMADO", "Confirmado"),
            ("CANCELADO", "Cancelado"),
    ]

    medico = models.ForeignKey("Medico", on_delete=models.PROTECT, related_name="turnos")
    paciente = models.ForeignKey("Paciente", on_delete=models.PROTECT, related_name="turnos")
    fecha_hora = models.DateTimeField()
    motivo = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE")

    def __str__(self):
        return f"Turno de {self.paciente} con {self.medico} el {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

    def validate(self):
        """Valida los datos del turno. Retorna una lista de errores."""
        errors = []

        if self.fecha_hora and self.fecha_hora < timezone.now():
            errors.append("La fecha y hora del turno no pueden ser en el pasado.")

        if self.motivo and len(self.motivo) > 200:
            errors.append("El motivo del turno no puede exceder los 200 caracteres.")

        if self.estado not in dict(self.ESTADO_CHOICES):
            errors.append(f"El estado del turno debe ser uno de: {', '.join(dict(self.ESTADO_CHOICES).keys())}.")

        if self.medico and self.fecha_hora:
            turnos_superpuestos = Turno.objects.filter(
                medico=self.medico,
                fecha_hora=self.fecha_hora,
                estado__in=["PENDIENTE", "CONFIRMADO"]
            )
            if self.pk:
                turnos_superpuestos = turnos_superpuestos.exclude(pk=self.pk)
            if turnos_superpuestos.exists():
                errors.append("El médico ya tiene un turno en esa fecha y hora.")

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
    
    def cancelar(self):
        """Cancela el turno si está pendiente."""
        if self.estado == "PENDIENTE":
            self.estado = "CANCELADO"
            self.save()
            return True, []
        return False, ["Solo se pueden cancelar turnos pendientes."]

    def confirmar(self):
        """Confirma el turno si está pendiente."""
        if self.estado == "PENDIENTE":
            self.estado = "CONFIRMADO"
            self.save()
            return True, []
        return False, ["Solo se pueden confirmar turnos pendientes."]
