from django import forms
from .models import Turno, Medico, Paciente, timezone

class TurnoForm(forms.ModelForm):
    """Formulario para crear un turno nuevo."""
    class Meta:
        model = Turno
        fields = {"medico", "fecha_hora", "motivo"}
        widgets = {
            "medico": forms.Select(attrs={"class": "form-select"}),
            "fecha_hora": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local", "datetime_picker": "true"}),
            "motivo": forms.Textarea(attrs={"readonly": True, "class": "form-control-plaintext", "rows": 3, "placeholder": "Ingrese su consulta"}),
            }
        labels = {
            "medico": "Seleccione un médico",
            "fecha_hora": "Fecha y hora del turno",
            "motivo": "Motivo del turno"
        }
        error_messages = {
            "medico": {"required": "Debe seleccionar un médico."},
            "fecha_hora": {"required": "Debe ingresar la fecha y hora del turno."}
        }
    
    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get("fecha_hora")
        if fecha_hora and fecha_hora < timezone.now():
            raise forms.ValidationError("La fecha y hora del turno no puede ser en el pasado.")
        return fecha_hora
    
    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get("motivo")
        medico = cleaned_data.get("medico", None)
        if not motivo or not motivo.strip():
            self.add_error("motivo", "El motivo del turno es obligatorio.")
        if not medico:
            self.add_error("medico", "Debe seleccionar un médico.")
        return cleaned_data

    