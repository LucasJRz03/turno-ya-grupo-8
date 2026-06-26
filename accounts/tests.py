# accounts/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import CustomUser

User = get_user_model()
class CustomUserModelTest(TestCase):
    """Tests del modelo CustomUser con patrón validate/new/update."""

    def test_new_usuario_valido(self):
        """Prueba que new() crea un usuario correctamente."""
        user, errors = CustomUser.new(
            username='juan123',
            email='juan@gmail.com',
            password='contraseña_segura_123',
            tipo_usuario='paciente',
            first_name='Juan',
            last_name='Pérez'
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('contraseña_segura_123'))
        self.assertEqual(user.email, 'juan@gmail.com')
        self.assertEqual(user.tipo_usuario, 'paciente')

    def test_new_usuario_email_duplicado(self):
        """Prueba que new() falla si el email ya existe."""
        CustomUser.new(
            username='juan1', email='juan@gmail.com',
            password='pass1234', tipo_usuario='paciente'
        )
        user, errors = CustomUser.new(
            username='juan2', email='juan@gmail.com',
            password='pass1234', tipo_usuario='paciente'
        )
        self.assertIsNone(user)
        self.assertTrue(any('email' in e.lower() for e in errors))

    def test_new_usuario_sin_email(self):
        """Prueba que new() falla si no hay email."""
        user, errors = CustomUser.new(
            username='juan3', email='',
            password='pass1234', tipo_usuario='paciente'
        )
        self.assertIsNone(user)
        self.assertTrue(len(errors) > 0)

    def test_validate_username_corto(self):
        """Prueba que validate() detecta usernames cortos."""
        user = CustomUser(username='ab', email='test@test.com')
        errors = user.validate()
        self.assertTrue(any('4 caracteres' in e for e in errors))

    def test_update_usuario_exitoso(self):
        """Prueba que update() modifica datos correctamente."""
        user, _ = CustomUser.new(
            username='juan4', email='juan4@gmail.com',
            password='pass1234', first_name='Juan'
        )
        errors = user.update(first_name='Carlos')
        self.assertEqual(errors, [])
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Carlos')

    def test_update_email_duplicado_falla(self):
        """Prueba que update() falla al poner un email duplicado."""
        CustomUser.new(
            username='user1', email='user1@gmail.com',
            password='pass1234'
        )
        user2, _ = CustomUser.new(
            username='user2', email='user2@gmail.com',
            password='pass1234'
        )
        errors = user2.update(email='user1@gmail.com')
        self.assertTrue(len(errors) > 0)
        user2.refresh_from_db()
        self.assertEqual(user2.email, 'user2@gmail.com')

    def test_propiedades_es_paciente_medico_admin(self):
        """Prueba las propiedades booleanas de rol."""
        user_pac, _ = CustomUser.new(
            username='pac1', email='pac1@gmail.com',
            password='pass1234', tipo_usuario='paciente'
        )
        self.assertTrue(user_pac.es_paciente)
        self.assertFalse(user_pac.es_medico)
        
        user_med, _ = CustomUser.new(
            username='med1', email='med1@gmail.com',
            password='pass1234', tipo_usuario='medico'
        )
        self.assertTrue(user_med.es_medico)
        self.assertFalse(user_med.es_paciente)

    def test_nombre_completo_con_datos(self):
        """Prueba nombre_completo() cuando hay nombre y apellido."""
        user, _ = CustomUser.new(
            username='jperez', email='jp@gmail.com',
            password='pass1234', first_name='Juan', last_name='Pérez'
        )
        self.assertEqual(user.nombre_completo(), 'Juan Pérez')

    def test_nombre_completo_sin_datos(self):
        """Prueba nombre_completo() cuando no hay nombre ni apellido."""
        user, _ = CustomUser.new(
            username='jperez', email='jp@gmail.com',
            password='pass1234'
        )
        self.assertEqual(user.nombre_completo(), 'jperez')
