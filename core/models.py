"""
Core models for the DRC Asset Lending Management System.
"""

import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ──────────────────────────────────────────────────────────────
# Custom User Manager
# ──────────────────────────────────────────────────────────────
class UserManager(BaseUserManager):
    """Custom manager: users are created only by admin."""

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('email_verified', True)
        return self.create_user(email, name, password, **extra_fields)


# ──────────────────────────────────────────────────────────────
# User
# ──────────────────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('MANAGER', 'Gestionnaire'),
        ('USER', 'Utilisateur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nom complet', max_length=200)
    email = models.EmailField('Adresse email', unique=True)
    email_verified = models.BooleanField('Email vérifié', default=False)
    phone = models.CharField('Téléphone', max_length=30, blank=True, default='')
    role = models.CharField('Rôle', max_length=20, choices=ROLE_CHOICES, default='USER')
    verification_token = models.CharField(max_length=100, blank=True, default='')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'core_user'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.email})"


# ──────────────────────────────────────────────────────────────
# Organization Hierarchy: Direction → Department → SubDepartment
# ──────────────────────────────────────────────────────────────
class Direction(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Nom de la direction', max_length=200, unique=True)
    code = models.CharField('Code', max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_direction'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    direction = models.ForeignKey(
        Direction, on_delete=models.CASCADE, related_name='departments',
        verbose_name='Direction'
    )
    name = models.CharField('Nom du département', max_length=200)
    code = models.CharField('Code', max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_department'
        ordering = ['name']
        unique_together = ['direction', 'name']

    def __str__(self):
        return f"{self.name} ({self.direction.name})"


class SubDepartment(models.Model):
    id = models.AutoField(primary_key=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='sub_departments',
        verbose_name='Département'
    )
    name = models.CharField('Nom du sous-département', max_length=200)
    code = models.CharField('Code', max_length=20, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_subdepartment'
        ordering = ['name']
        unique_together = ['department', 'name']

    def __str__(self):
        return f"{self.name} ({self.department.name})"


# ──────────────────────────────────────────────────────────────
# Equipment
# ──────────────────────────────────────────────────────────────
class Equipment(models.Model):
    CONDITION_CHOICES = [
        ('NEUF', 'Neuf'),
        ('BON', 'Bon état'),
        ('USAGE', 'Usagé'),
        ('DEFECTUEUX', 'Défectueux'),
        ('HORS_SERVICE', 'Hors service'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField('Nom', max_length=200)
    model = models.CharField('Modèle', max_length=200, blank=True, default='')
    internal_id = models.CharField('ID interne', max_length=50, unique=True)
    serial_number = models.CharField('Numéro de série', max_length=100, blank=True, default='')
    condition = models.CharField('État', max_length=20, choices=CONDITION_CHOICES, default='BON')
    description = models.TextField('Description', blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_equipment'
        verbose_name = 'Équipement'
        verbose_name_plural = 'Équipements'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.internal_id}]"

    @property
    def current_stock(self):
        """Compute current stock from all movements."""
        from django.db.models import Sum, Q
        result = Movement.objects.filter(equipment=self).aggregate(
            total_in=Sum('quantity', filter=Q(action_type__in=['ENTREE', 'RETOUR'])),
            total_out=Sum('quantity', filter=Q(action_type__in=['PRET', 'SORTIE'])),
        )
        total_in = result['total_in'] or 0
        total_out = result['total_out'] or 0
        return total_in - total_out


# ──────────────────────────────────────────────────────────────
# Movement (core business entity)
# ──────────────────────────────────────────────────────────────
class Movement(models.Model):
    ACTION_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('PRET', 'Prêt'),
        ('RETOUR', 'Retour'),
        ('SORTIE', 'Sortie'),
    ]

    id = models.AutoField(primary_key=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movements_completed',
        verbose_name='Effectué par'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movements_assigned',
        verbose_name='Assigné à',
        null=True, blank=True,
        help_text='Personne ayant reçu l\'équipement (obligatoire pour PRET/SORTIE)'
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT,
        related_name='movements',
        verbose_name='Équipement'
    )
    quantity = models.PositiveIntegerField('Quantité', default=1)
    action_type = models.CharField('Type d\'action', max_length=10, choices=ACTION_CHOICES)
    date = models.DateTimeField('Date du mouvement', auto_now_add=True)
    notes = models.TextField('Remarques', blank=True, default='')
    direction = models.ForeignKey(
        Direction, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Direction'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Département'
    )

    class Meta:
        db_table = 'core_movement'
        verbose_name = 'Mouvement'
        verbose_name_plural = 'Mouvements'
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.equipment.name} x{self.quantity}"
