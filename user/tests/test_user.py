from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

MANAGE_USER_URL = reverse("user:manage")


class UserModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email, password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(password))

    def test_create_user_without_email_raises_error(self):
        with self.assertRaisesMessage(
                ValueError, "The given email must be set"
        ):
            get_user_model().objects.create_user(
                email=None, password="testpass123"
            )

    def test_create_superuser_successful(self):
        email = "superuser@example.com"
        password = "testpass123"
        superuser = get_user_model().objects.create_superuser(
            email=email, password=password
        )

        self.assertEqual(superuser.email, email)
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.check_password(password))

    def test_create_duplicate_user_email_raises_error(self):
        email = "duplicate@example.com"
        get_user_model().objects.create_user(email=email, password="testpass1")
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create_user(
                email=email, password="testpass2"
            )


class UserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )

    def test_retrieve_authenticated_user_profile(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_manage_user_unauthenticated(self):
        res = self.client.get(MANAGE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
