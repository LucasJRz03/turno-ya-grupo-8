# TurnoYa 🏥

Sistema web de gestión de turnos médicos desarrollado con Django 5.1+.  
Permite registrar médicos, pacientes y turnos, con autenticación de usuarios y panel de administración.

---

## 🛠️ Stack

| Tecnología | Versión |
|------------|---------|
| Python | 3.13+ |
| Django | 5.1+ |
| Base de datos | SQLite (desarrollo) |
| Frontend | Bootstrap 5 |
| Tests | `django.test.TestCase` |
| Control de versiones | Git + GitHub |

---

## ✨ Funcionalidades

- 🔐 Registro, login y logout de usuarios
- 👨‍⚕️ Gestión de médicos y especialidades
- 🧑 Gestión de pacientes
- 📅 Solicitud, confirmación y cancelación de turnos
- 📊 Panel de inicio con estadísticas del día
- 🛠️ Panel de administración Django configurado
- 📱 Interfaz responsiva con Bootstrap 5

---

## 👥 Integrantes

| Nombre | Usuario GitHub |
|--------|---------------|
| Lucas Rodríguez | https://github.com/LucasJRz03 |
| ... | [@usuario](https://github.com/usuario) |
| ... | [@usuario](https://github.com/usuario) |

---

## 🚀 Instalación y uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/usuario/turnoya.git
cd turnoya
```

### 2. Crear y activar el entorno virtual

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario (para el panel admin)

```bash
python manage.py createsuperuser
```

### 6. Correr el servidor de desarrollo

```bash
python manage.py runserver
```

Accedé a [http://localhost:8000](http://localhost:8000)  
Panel admin: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🧪 Correr los tests

```bash
# Todos los tests con detalle
python manage.py test -v 2

# Solo tests de modelos
python manage.py test app.tests.test_models -v 2

# Solo tests de vistas
python manage.py test app.tests.test_views -v 2
```

---

## 🔑 Credenciales de prueba

> ⚠️ Solo para uso del corrector en entorno de desarrollo local.

| Rol | Usuario | Contraseña |
|-----|---------|-----------|
| Superusuario / Admin | `admin` | `admin1234` |
| Usuario de prueba | `usuario_prueba` | `prueba1234` |

---

## 📁 Estructura del proyecto

```
turnoya/
├── turnoya/            # Configuración del proyecto Django
│   ├── settings.py
│   └── urls.py
├── app/                # App principal
│   ├── models.py       # Especialidad, Medico, Paciente, Turno
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── consultas.py    # Consultas ORM
│   └── tests/
│       ├── test_models.py
│       └── test_views.py
├── templates/
│   ├── base.html
│   └── registration/
├── static/
├── manage.py
├── requirements.txt
└── .gitignore
```

---

## 🖼️ Capturas

### Inicio
![Pantalla de inicio](docs/screenshots/inicio.png)

### Lista de turnos
![Lista de turnos](docs/screenshots/turnos.png)

### Panel de administración
![Admin](docs/screenshots/admin.png)

### Login
![Login](docs/screenshots/login.png)

---

## 🧩 Decisiones de diseño

> *(Mínimo 200 palabras — completar antes de la entrega final)*

Describir aquí:
- Por qué eligieron este dominio
- Cómo organizaron las responsabilidades entre modelos y vistas
- Qué validaciones decidieron poner en el modelo vs. en el formulario
- Cómo dividieron el trabajo entre los integrantes
- Cualquier decisión de diseño no obvia (ej: por qué usaron FBV en lugar de CBV, cómo manejaron la relación User ↔ Paciente, etc.)

---

## ⭐ Funcionalidades opcionales implementadas

- [ ] Vista "Mis turnos" para el paciente autenticado
- [ ] Mensajes flash con `django.contrib.messages`
- [ ] Paginación en lista de turnos
- [ ] Permisos diferenciados por grupo
- [ ] Tests de integración (flujo completo)

---

## 🐛 Problemas comunes

| Problema | Solución |
|----------|----------|
| `OperationalError: no such table` | Corré `python manage.py migrate` |
| `No module named django` | Activá el entorno virtual |
| Página en blanco o error 500 | Revisá la consola donde corre `runserver` |
| Login no redirige bien | Verificá `LOGIN_REDIRECT_URL` en `settings.py` |