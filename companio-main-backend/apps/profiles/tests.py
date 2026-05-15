from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class ProfileApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='profile@example.com',
            username='profileuser',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_is_created_for_new_user(self):
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_user_can_update_profile(self):
        response = self.client.patch(reverse('profile-me'), {
            'display_name': 'Kavinda',
            'preferred_language': 'en',
            'timezone': 'Asia/Colombo',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['profile_completed'])
