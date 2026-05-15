from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_register_without_password_exposure(self):
        response = self.client.post(reverse('auth-register'), {
            'email': 'user@example.com',
            'username': 'kavinda',
            'full_name': 'Kavinda Supun',
            'password': 'StrongPassword123',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('tokens', response.json())
        self.assertNotIn('password', response.json()['user'])

    def test_authenticated_user_can_view_me(self):
        user = get_user_model().objects.create_user(
            email='me@example.com',
            username='meuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('auth-me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'me@example.com')
