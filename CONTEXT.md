# Contexto del proyecto: TurnoYa

## ¿Qué es este proyecto?

TurnoYa es una aplicación web de gestión de turnos médicos desarrollada con Django 5.1+ y Python 3.12+.
Es un trabajo práctico integrador universitario.
El proyecto está **en construcción**: hay código base ya implementado y partes marcadas con `# TODO` que los estudiantes deben completar.

---

## Stack tecnológico

- Python 3.12+
- Django 5.1+
- SQLite (base de datos de desarrollo)
- Bootstrap 5.3 (frontend, via CDN)
- `django.test.TestCase` (tests unitarios)
- Git + GitHub (control de versiones)

---

## Estructura del proyecto

```
turno-ya/
├── turnoya/
│   ├── settings.py        # Configuración Django. Incluye la app "app" y SQLite como base local
│   ├── urls.py            # include("django.contrib.auth.urls") + include("app.urls", namespace="app")
│   └── wsgi.py
├── app/                   # App principal
│   ├── models.py          # Modelos del dominio
│   ├── views.py           # Vistas (FBV)
│   ├── urls.py            # URLs con app_name = "app"
│   ├── admin.py           # Registro de modelos en el admin
│   ├── apps.py
│   ├── fixtures/
│   │   └── medicos.json   # 4 instancias de Medico para poblar la BD, incluyendo a Juan Pérez
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── templates/
│   │   ├── clinica/
│   │       ├── home.html         # Panel de inicio con cards vacías (TODO)
│   │       └── lista_medicos.html # Tabla de médicos
│   │   └── base.html              # Layout base compartido del proyecto
│   └── tests/
│       └── test_models.py  # Tests del modelo Medico (validate, new, update)
├── manage.py
├── requirements.txt       # django>=5.1,<6.0
└── .gitignore
```

---

## Modelo actual implementado: `Medico`

```python
class Medico(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)  # Por ahora CharField, luego será FK a Especialidad

    def __str__(self): ...
    def nombre_completo(self): ...
    def cantidad_turnos(self): ...

    @classmethod
    def validate(cls, nombre, apellido, matricula, especialidad) -> list[str]: ...
    @classmethod
    def new(cls, nombre, apellido, matricula, especialidad) -> tuple[Medico | None, list[str]]: ...
    def update(self, nombre, apellido, matricula, especialidad) -> list[str]: ...
```

**Patrón de validate/new/update**:
- `validate` retorna lista de strings con errores. Lista vacía = datos válidos.
- `new` llama a `validate`, si hay errores retorna `(None, errors)`, si no crea y retorna `(instancia, [])`.
- `update` llama a `validate`, si hay errores retorna la lista sin modificar, si no guarda con `self.save()` y retorna `[]`.

---

## Modelos pendientes de implementar (TODO de los estudiantes)

Los estudiantes deben agregar estos modelos en `app/models.py`:

### `Especialidad`
- `nombre` (CharField, unique)
- `descripcion` (TextField, blank=True)
- Refactorizar `Medico.especialidad` de CharField a FK → Especialidad (PROTECT)

### `Paciente`
- `nombre`, `apellido` (CharField)
- `dni` (CharField, unique)
- `email` (CharField)
- `telefono` (CharField, optional)
- `usuario` (OneToOneField → User, CASCADE)

### `Turno`
- `medico` (FK → Medico, CASCADE)
- `paciente` (FK → Paciente, CASCADE)
- `fecha_hora` (DateTimeField)
- `motivo` (TextField)
- `estado` (CharField, choices: `pendiente` / `confirmado` / `cancelado`)
- `creado_por` (FK → User, SET_NULL, null=True)
- Métodos: `esta_pendiente()`, `confirmar()`, `cancelar()`
- Classmethod: `validate`, `new`, `update` (mismo patrón que Medico)

---

## Vistas actuales implementadas

```python
def home(request):        # GET /  → clinica/home.html — contexto vacío (TODO: agregar estadísticas)
def lista_medicos(request): # GET /medicos/ → clinica/lista_medicos.html — contexto: {"medicos": queryset ordenado}
```

## Vistas pendientes (TODO)

```python
def detalle_medico(request, pk)        # GET /medicos/<pk>/
def lista_turnos(request)              # GET /turnos/
def nuevo_turno(request)               # GET+POST /turnos/nuevo/
def cancelar_turno(request, pk)        # POST /turnos/<pk>/cancelar/
def lista_pacientes(request)           # GET /pacientes/
```

---

## Autenticación

- `django.contrib.auth.urls` sigue incluido en `turnoya/urls.py`, pero la UI actual no expone login, logout ni registro.
- No hay vista de registro implementada en la app.
- Las vistas actuales (`home`, `lista_medicos`) no usan `@login_required`.
- `settings.py` todavía conserva `LOGIN_URL`, `LOGIN_REDIRECT_URL` y `LOGOUT_REDIRECT_URL` como configuración heredada.

---

## Admin

`app/admin.py` tiene `admin.site.register(Medico)` básico.
Los estudiantes deben reemplazarlo por `@admin.register` con:
- `list_display`
- `list_filter`
- `search_fields`
- `date_hierarchy` (en Turno)

---

## Templates

- `base.html` vive en `app/templates/base.html`. Usa `{% block title %}` y `{% block content %}`.
- La navbar actual muestra solo navegación del dominio (`Inicio` implícito por logo y `Médicos`).
- Los templates de app van en `app/templates/clinica/`.
- No hay templates de auth implementados en la app.
- Bootstrap 5.3 via CDN (no instalado localmente).

---

## Tests actuales (pasan ✅)

En `app/tests/test_models.py`:
- `test_str_incluye_apellido_y_nombre`
- `test_nombre_completo`
- `test_cantidad_turnos_inicial_es_cero`
- `test_validate_datos_correctos_retorna_lista_vacia`
- `test_validate_nombre_vacio_retorna_error`
- `test_validate_matricula_vacia_retorna_error`
- `test_new_crea_medico_con_datos_validos`
- `test_new_con_datos_invalidos_retorna_errores_y_no_crea`
- `test_update_modifica_datos_correctamente`
- `test_update_con_datos_invalidos_no_modifica`

---

## Consultas ORM pendientes (archivo a crear: `consultas.py`)

```python
def medicos_por_especialidad(nombre_especialidad: str) -> QuerySet: ...
def turnos_pendientes_del_dia(fecha) -> QuerySet: ...
def pacientes_con_mas_de_n_turnos(n: int) -> QuerySet: ...
def turnos_por_medico_ordenados(medico_id: int) -> QuerySet: ...
```

---

## Convenciones del proyecto

- Vistas: FBV (Function-Based Views), no CBV
- URLs: siempre con `app_name` y `name`, referenciar con `{% url 'app:nombre' %}`
- Templates: siempre extienden `base.html`
- Modelos: siempre incluir `__str__`, `validate`, `new`, `update`
- Tests: usar `django.test.TestCase`, no `pytest`
- Commits semánticos: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`

---

## Cómo correr el proyecto

```bash
python -m venv .venv && source .venv/bin/activate  # o .\.venv\Scripts\Activate.ps1 en Windows
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata app/fixtures/medicos.json
python manage.py test -v 2
python manage.py runserver
```