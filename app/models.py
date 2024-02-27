from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db import models

class Account(AbstractUser):
    def __str__(self):
        return self.username

    class Meta:
        indexes = [models.Index(fields=['username']),]
        verbose_name = _("Usuario")
        verbose_name_plural = _("Usuarios")