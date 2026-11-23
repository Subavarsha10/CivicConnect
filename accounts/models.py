
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = [
        ('citizen', 'Citizen'),
        ('manager', 'Department Manager'),
        ('admin', 'Administrator'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citizen'
    )

    phone_number = models.CharField(
        max_length=15,
        blank=True
    )

    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
