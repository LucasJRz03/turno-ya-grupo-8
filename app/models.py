"""Modelos de dominio de TurnoYa."""

from __future__ import annotations
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

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

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.ForeignKey('Especialidad', on_delete=models.PROTECT, related_name='medicos')
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

        # `especialidad` puede ser una instancia de Especialidad o un nombre (string)
        if isinstance(especialidad, Especialidad):
            pass
        else:
            if not especialidad or not str(especialidad).strip():
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

        # Resolver `especialidad`: si viene como string, buscar o crear la Especialidad
        if isinstance(especialidad, Especialidad):
            esp = especialidad
        else:
            esp, _ = Especialidad.objects.get_or_create(
                nombre=str(especialidad).strip(), defaults={"descripcion": ""}
            )

        medico = cls.objects.create(
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            matricula=matricula.strip(),
            especialidad=esp,
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
        # Resolver especialidad a instancia si se pasa como nombre
        if isinstance(especialidad, Especialidad):
            esp = especialidad
        else:
            esp, _ = Especialidad.objects.get_or_create(
                nombre=str(especialidad).strip(), defaults={"descripcion": ""}
            )
        self.especialidad = esp
        self.save()
        return []

class Paciente(models.Model):
    """Representa a un paciente registrado en el sistema."""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=25, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=50, blank=True, null=True)
     
    def __str__(self):
        return f"{self.apellido}, {self.nombre} (Dni: {self.dni})"

    def nombre_completo(self):
        """Retorna nombre y apellido concatenados."""
        return f"{self.nombre} {self.apellido}"
    
    @classmethod
    def validate(cls, usuario, nombre, apellido, dni, email, telefono=None):
        errors = []
        if not usuario:
            errors.append("El usuario asociado es obligatorio.")
        if not nombre or not str(nombre).strip():
            errors.append("El nombre es obligatorio.")
        if not apellido or not str(apellido).strip():
            errors.append("El apellido es obligatorio.")
        if not dni or not str(dni).strip():
            errors.append("El DNI es obligatorio.")
        if not email or not str(email).strip():
            errors.append("El email es obligatorio.")
        return errors

    @classmethod
    def new(cls, usuario, nombre, apellido, dni, email, telefono=None):
        errors = cls.validate(usuario, nombre,apellido,dni,email,telefono)
        if errors:
            return None, errors
        
        paciente = cls.objects.create(
            usuario=usuario,
            nombre=str(nombre).strip(),
            apellido=str(apellido).strip(),
            dni=str(dni).strip(),
            email=str(email).strip(),
            telefono=str(telefono).strip() if telefono else ""
        )
        return paciente, []

    def update(self, usuario, nombre, apellido, dni, email, telefono=None):
        errors = self.__class__.validate(usuario, nombre, apellido, dni, email, telefono)
        if errors:
            return errors

        self.usuario = usuario
        self.nombre = str(nombre).strip()
        self.apellido = str(apellido).strip()
        self.dni = str(dni).strip()
        self.email = str(email).strip()
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

    medico = models.ForeignKey("Medico", on_delete=models.CASCADE)
    paciente = models.ForeignKey("Paciente", on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    motivo = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="PENDIENTE")

    def __str__(self):
        return f"Turno de {self.paciente} con {self.medico} el {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

    def validate(self):
        """Valida los datos del turno. Retorna una lista de errores."""
        errors = []

        if self.fecha_hora < timezone.now():
            errors.append("La fecha y hora del turno no pueden ser en el pasado.")

        if self.motivo and len(self.motivo) > 200:
            errors.append("El motivo del turno no puede exceder los 200 caracteres.")

        if self.estado not in dict(self.ESTADO_CHOICES):
            errors.append(f"El estado del turno debe ser uno de: {', '.join(dict(self.ESTADO_CHOICES).keys())}.")

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


class Ausencia(models.Model): 
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE, related_name='ausencias')
    motivo = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return f"Ausencia de Dr/a {self.medico}, fecha:{self.fecha_inicio.strftime('%Y-%m-%d')}"

    def validate(self):
        """solo valida, nunca toca la BD, retorna un list[str]"""
        errors = []
        if not self.motivo:
            errors.append("El motivo no puede estar vacío.")

        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                errors.append("La fecha fin no puede ser mayor a la fecha de inicio.")

        return errors

    @classmethod
    def new(cls, medico, motivo, fecha_inicio, fecha_fin):
        """LLama a validate, si hay errores retorna none, sino crea la ausencia"""
        ausencia = cls(
            medico = medico,
            motivo = motivo,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )
        errors = ausencia.validate()

        if errors:
            return None, errors
        
        ausencia.save()
        return ausencia, []

    def update(self, **kwargs): 
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        
        errors = self.validate()
    
        if errors:
            return errors

        self.save()
        return []

class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100)
    sitio_web = models.URLField(blank=True, null=True)
    requiere_token = models.BooleanField(default=False)
    medicos_disponibles = models.ManyToManyField('Medico', related_name='obra_sociales', blank=True)

    def validate(self):
        """Solo valida, nunca toca la BD, retorna list[str]."""
        errors = []
        if not self.nombre:
            errors.append("El nombre de la obra social no puede estar vacío.")

        return errors

    @classmethod
    def new(cls, nombre, sitio_web='', requiere_token=False, medicos=None):
        """Llama a validate, si hay errores retorna None; si no, crea y retorna  (instancia, [])."""
        obra_social = cls(
            nombre = nombre,
            sitio_web = sitio_web,
            requiere_token = requiere_token
        )
        errors = obra_social.validate()

        if errors:
            return None, errors

        obra_social.save()

        if medicos is not None:
            obra_social.medicos_disponibles.set(medicos)
        
        return obra_social, []

    def update(self, medicos=None, **kwargs):
        """Llama a validate, si hay errores retorna la lista sin guardar, si no, llama self.save() y retorna []."""
        for key, value in kwargs.items():
            setattr(self, key, value)

        errors = self.validate()

        if errors:
            return errors

        self.save()

        if medicos is not None:
            self.medicos_disponibles.set(medicos)

        return []
        
    def __str__(self):
        return self.nombre



