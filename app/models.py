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

    def update(self, **kwargs):
        """Actualiza los datos de la especialidad si son válidos."""
        datos_futuros = {"nombre": self.nombre, "descripcion": self.descripcion}
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
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
        return self.turno_set.count()

    @classmethod
    def validate(cls, usuario, matricula, especialidad, exclude_pk=None):
        """Valida los datos del médico. Retorna una lista de errores.
        Si la lista está vacía, los datos son válidos."""

        errors = []

        if not usuario:
            errors.append("El usuario asociado es obligatorio")

        if not matricula or not matricula.strip():
            errors.append("La matrícula es obligatoria.")
        else:
            matricula_limpia = str(matricula).strip()
            qs = cls.objects.filter(matricula=matricula_limpia)
        
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            
            if qs.exists():
                errors.append("Ya existe un médico con esa matrícula.")

        # `especialidad` puede ser una instancia de Especialidad o un nombre (string)
        if isinstance(especialidad, Especialidad):
            pass
        else:
            if not especialidad or not str(especialidad).strip():
                errors.append("La especialidad es obligatoria.")

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

    def update(self, **kwargs):
        """Actualiza los datos del médico si son válidos."""
        datos_futuros = {
            "usuario": self.usuario, 
            "matricula": self.matricula, 
            "especialidad": self.especialidad,
            "exclude_pk": self.pk
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            # Si la especialidad viene como string, la resolvemos a instancia
            if attr == 'especialidad' and isinstance(value, str):
                esp, _ = Especialidad.objects.get_or_create(
                    nombre=value.strip(), defaults={"descripcion": ""}
                )
                setattr(self, attr, esp)
            else:
                setattr(self, attr, value)
                
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

    def update(self, **kwargs):
        """Actualiza los datos del paciente si son válidos."""
        datos_futuros = {"usuario": self.usuario, "dni": self.dni, "telefono": self.telefono}
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
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


    @classmethod
    def validate(cls, medico, paciente, fecha_hora, motivo="", estado="PENDIENTE", exclude_pk=None):
        """Valida los datos del turno. Retorna una lista de errores."""
        errors = []

        if fecha_hora and fecha_hora < timezone.now():
            errors.append("La fecha y hora del turno no pueden ser en el pasado.")

        if motivo and len(motivo) > 200:
            errors.append("El motivo del turno no puede exceder los 200 caracteres.")

        if estado not in dict(cls.ESTADO_CHOICES):
            errors.append(f"El estado del turno debe ser uno de: {', '.join(dict(cls.ESTADO_CHOICES).keys())}.")

        if medico and fecha_hora:
            turnos_superpuestos = Turno.objects.filter(
                medico=medico,
                fecha_hora=fecha_hora,
                estado__in=["PENDIENTE", "CONFIRMADO"]
            )
            if exclude_pk:
                turnos_superpuestos = turnos_superpuestos.exclude(pk=exclude_pk)
            if turnos_superpuestos.exists():
                errors.append("El médico ya tiene un turno en esa fecha y hora.")

        if not medico or not paciente:
            errors.append("El médico y el paciente son obligatorios.")

        return errors
    
    @classmethod
    def new(cls, medico, paciente, fecha_hora, motivo="", estado="PENDIENTE"):
        """Crea un nuevo turno si los datos son válidos. Retorna (instancia, errors)."""
        errors = cls.validate(medico, paciente, fecha_hora, motivo, estado)
        if errors:
            return None, errors
        
        turno = cls.objects.create(
            medico=medico,
            paciente=paciente,
            fecha_hora=fecha_hora,
            motivo=motivo,
            estado=estado
        )
        return turno, []
        
    def update(self, **kwargs) -> list[str]: 
        """Actualiza los datos del turno si son válidos. Retorna una lista de errores."""

        datos_futuros = {
            "medico": self.medico,
            "paciente": self.paciente,
            "fecha_hora": self.fecha_hora,
            "motivo": self.motivo,
            "estado": self.estado,
            "exclude_pk": self.pk
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
        for attr, value in kwargs.items():
            setattr(self, attr, value)
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
class Ausencia(models.Model): 
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE, related_name='ausencias')
    motivo = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def __str__(self):
        return f"Ausencia de Dr/a {self.medico}, fecha:{self.fecha_inicio.strftime('%Y-%m-%d')}"

    @classmethod
    def validate(cls, medico, motivo, fecha_inicio, fecha_fin):
        errors = []
        if not medico: 
            errors.append("El médico es obligatorio.")
        if not motivo or not motivo.strip(): 
            errors.append("El motivo no puede estar vacío.")
        if not fecha_inicio: 
            errors.append("La fecha de inicio es obligatoria.")
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            errors.append("La fecha fin no puede ser mayor a la fecha de inicio.")  
        return errors

    @classmethod
    def new(cls, medico, motivo, fecha_inicio, fecha_fin):
        """LLama a validate, si hay errores retorna none, sino crea la ausencia"""
        errors = cls.validate(medico, motivo, fecha_inicio, fecha_fin)
        if errors:
            return None, errors
        
        ausencia = cls(
            medico = medico,
            motivo = motivo,
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin
        )
        
        ausencia.save()
        return ausencia, []

    def update(self, **kwargs):
        """Actualiza los datos de la ausencia si son válidos."""
        datos_futuros = {
            "medico": self.medico, "motivo": self.motivo,
            "fecha_inicio": self.fecha_inicio, "fecha_fin": self.fecha_fin
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save()
        return []
class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100)
    sitio_web = models.URLField(blank=True, null=True)
    requiere_token = models.BooleanField(default=False)
    medicos_disponibles = models.ManyToManyField('Medico', related_name='obra_sociales', blank=True)

    @classmethod
    def validate(cls, nombre, sitio_web='', requiere_token=False):
        """Solo valida, nunca toca la BD, retorna list[str]."""
        errors = []
        if not nombre or not str(nombre).strip():
            errors.append("El nombre de la obra social no puede estar vacío.")
        return errors

    @classmethod
    def new(cls, nombre, sitio_web='', requiere_token=False, medicos=None):
        """Llama a validate, si hay errores retorna None; si no, crea y retorna  (instancia, [])."""
        
        errors = cls.validate(nombre, sitio_web, requiere_token)
        if errors:
            return None, errors

        obra_social = cls(
            nombre = nombre,
            sitio_web = sitio_web,
            requiere_token = requiere_token
        )

        obra_social.save()
        if medicos is not None:
            obra_social.medicos_disponibles.set(medicos)
        return obra_social, []

    def update(self, **kwargs):
        """Actualiza los datos de la obra social. Extrae 'medicos' para el M2M."""
        # Extraemos el campo ManyToMany para que no se pase a validate ni a setattr
        medicos = kwargs.pop('medicos', None)
        
        datos_futuros = {
            "nombre": self.nombre, "sitio_web": self.sitio_web, 
            "requiere_token": self.requiere_token
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save()
        
        # Actualizamos la relación ManyToMany si se proporcionó
        if medicos is not None:
            self.medicos_disponibles.set(medicos)
            
        return []
        
    def __str__(self):
        return self.nombre
class SolicitudMedico(models.Model):
    """Representa una solicitud de un paciente para convertirse en médico.
    El administrador debe aprobarla o rechazarla."""
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    usuario = models.OneToOneField(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        related_name='solicitud_medico'
    )
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.ForeignKey(
        'Especialidad',
        on_delete=models.PROTECT,
        related_name='solicitudes'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    comentario_admin = models.TextField(
        blank=True,
        help_text="Motivo del rechazo o aprobación (opcional)"
    )
    
    class Meta:
        verbose_name = "Solicitud de Médico"
        verbose_name_plural = "Solicitudes de Médicos"
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud de {self.usuario.username} - {self.estado}"
    
    @classmethod
    def validate(cls, usuario, matricula, especialidad, exclude_pk=None):
        """Valida los datos de la solicitud."""
        errors = []
        
        if not usuario:
            errors.append("El usuario es obligatorio.")
        
        if not matricula or not str(matricula).strip():
            errors.append("La matrícula es obligatoria.")
        else:
            # Verifica que la matrícula no exista ya en otro médico
            if Medico.objects.filter(matricula=str(matricula).strip()).exists():
                errors.append("Ya existe un médico con esa matrícula.")
            
            # Verifica que no exista otra solicitud pendiente con la misma matrícula
            qs = SolicitudMedico.objects.filter(
                matricula=str(matricula).strip(),
                estado='PENDIENTE'
            )
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                errors.append("Ya existe una solicitud pendiente con esa matrícula.")
        
        if not especialidad:
            errors.append("La especialidad es obligatoria.")
        
        # Valida que el usuario sea paciente
        if usuario and usuario.tipo_usuario != 'paciente':
            errors.append("Solo los pacientes pueden solicitar ser médicos.")
        
        # Valida que el usuario no tenga otra solicitud pendiente
        if usuario:
            qs = SolicitudMedico.objects.filter(
                usuario=usuario,
                estado='PENDIENTE'
            )
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                errors.append("Ya tienes una solicitud pendiente en revisión.")
        
        return errors
    
    @classmethod
    def new(cls, usuario, matricula, especialidad):
        """Crea una nueva solicitud si los datos son válidos."""

        errors = cls.validate(usuario, matricula, especialidad)
        if errors:
            return None, errors

        solicitud = cls(
            usuario=usuario,
            matricula=matricula,
            especialidad=especialidad
        )
        
        solicitud.save()
        return solicitud, []
    
    def update(self, **kwargs):
        """Actualiza el estado o datos de la solicitud."""
        datos_futuros = {
            "usuario": self.usuario, "matricula": self.matricula, 
            "especialidad": self.especialidad, "exclude_pk": self.pk
        }
        datos_futuros.update(kwargs)
        
        errors = self.__class__.validate(**datos_futuros)
        if errors:
            return errors
            
        for attr, value in kwargs.items():
            setattr(self, attr, value)
            
        # Si se cambió el estado, actualizamos la fecha de resolución automáticamente
        if 'estado' in kwargs and kwargs['estado'] != self.estado:
            self.fecha_resolucion = timezone.now()
            
        self.save()
        return []
    
    def aprobar(self, comentario=""):
        """Aprueba la solicitud: crea el médico y cambia el rol del usuario.
        Retorna (exito, errores)."""

        if self.estado != 'PENDIENTE':
            return False, ["Esta solicitud ya fue resuelta."]
        
        medico, errors = Medico.new(
            usuario=self.usuario,
            matricula=self.matricula,
            especialidad=self.especialidad
        )
        
        if errors:
            return False, errors
        
        # Cambiar el rol del usuario
        self.usuario.tipo_usuario = 'medico'
        self.usuario.save()
        
        # Actualizar estado de la solicitud
        self.estado = 'APROBADO'
        self.comentario_admin = comentario
        self.fecha_resolucion = timezone.now()
        self.save()
        
        return True, []
    
    def rechazar(self, comentario=""):
        """Rechaza la solicitud sin crear el médico."""
        if self.estado != 'PENDIENTE':
            return False, ["Esta solicitud ya fue resuelta."]
        
        self.estado = 'RECHAZADO'
        self.comentario_admin = comentario
        self.fecha_resolucion = timezone.now()
        self.save()
        
        return True, []