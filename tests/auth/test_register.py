from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Profile


User = get_user_model()


class RegisterApiTests(APITestCase):
    url = reverse("register")

    def valid_payload(self, **overrides):
        payload = {
            "email": "new-user@example.com",
            "password": "strong-password-123",
            "full_name": "New User",
        }
        payload.update(overrides)
        return payload

    def test_register_creates_user_profile_and_tokens(self):
        response = self.client.post(self.url, self.valid_payload(), format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("access_token", response.data["data"])
        self.assertIn("refresh_token", response.data["data"])

        user = User.objects.get(email="new-user@example.com")
        self.assertTrue(user.check_password("strong-password-123"))
        self.assertFalse(user.password == "strong-password-123")
        self.assertEqual(Profile.objects.get(user=user).full_name, "New User")

    def test_register_rejects_duplicate_email(self):
        self.client.post(self.url, self.valid_payload(), format="multipart")

        response = self.client.post(self.url, self.valid_payload(), format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("Email already exists.", response.data["error"]["message"])

    def test_register_rejects_short_password(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password="12345"),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Password must be at least 6 characters", response.data["error"]["message"])
        self.assertEqual(User.objects.count(), 0)

    def test_register_rejects_today_as_date_of_birth(self):
        response = self.client.post(
            self.url,
            self.valid_payload(date_of_birth=date.today().isoformat()),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Date of birth must be in the past", response.data["error"]["message"])
        self.assertEqual(User.objects.count(), 0)

    def test_register_accepts_multipart_form_data(self):
        response = self.client.post(
            self.url,
            self.valid_payload(
                email="multipart@example.com",
                date_of_birth=(date.today() - timedelta(days=365 * 20)).isoformat(),
            ),
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="multipart@example.com").exists())
