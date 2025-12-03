from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username='testuser', password='password123', role='FARMER')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'FARMER')
        self.assertTrue(user.check_password('password123'))
        # Check profile creation signal
        self.assertIsNotNone(user.profile)

class UserViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/dashboard_base.html')

class UserAPITest(TestCase):
    def test_user_serializer(self):
        # Basic test for serializer logic if needed, or integration test with APIClient
        pass
