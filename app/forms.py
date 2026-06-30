from django import forms
from .models import Turno, Ausencia, timezone

class TurnoForm(forms.ModelForm):
    """Formulario para crear un turno nuevo."""
    class Meta:
        model = Turno
        fields = ["medico", "fecha_hora", "motivo"]
        widgets = {
            "medico": forms.Select(attrs={"class": "form-select"}),
            "fecha_hora": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local", "step": "900"}),
            "motivo": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ingrese su consulta"}),
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
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_hora = cleaned_data.get("fecha_hora")
        if fecha_hora and fecha_hora < timezone.now():
            self.add_error("fecha_hora", "La fecha y hora del turno no puede ser en el pasado.")
        return cleaned_data
    
class AusenciaForm(forms.ModelForm):
    """Formulario para registrar la ausencia de un médico."""
    class Meta:
        model = Ausencia
        fields = ["medico", "motivo", "fecha_inicio", "fecha_fin"]
        widgets = {
            "medico": forms.Select(attrs={"class": "form-selec"}),
            "motivo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Vacaciones, Licencia por enfermedad"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "forms-control", "type": "date"})
        }
        labels = {
            "medico": "Médico",
            "motivo": "Mótivo de la ausencia",
            "fecha_inicio": "Fecha de inicio",
            "fecha_fin": "Fecha de fin (incluida)"
        }

    