"""
Serializers for the DRC Asset Lending Management System.
"""

from rest_framework import serializers
from .models import User, Direction, Department, SubDepartment, Equipment, Movement


# ──────────────────────────────────────────────
# User
# ──────────────────────────────────────────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'email_verified', 'phone', 'role',
                  'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'role', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for dropdowns."""
    class Meta:
        model = User
        fields = ['id', 'name', 'email']


# ──────────────────────────────────────────────
# Organization
# ──────────────────────────────────────────────
class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    direction_name = serializers.CharField(source='direction.name', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'direction', 'direction_name', 'name', 'code', 'created_at']


class SubDepartmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = SubDepartment
        fields = ['id', 'department', 'department_name', 'name', 'code', 'created_at']


# ──────────────────────────────────────────────
# Equipment
# ──────────────────────────────────────────────
class EquipmentSerializer(serializers.ModelSerializer):
    current_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Equipment
        fields = ['id', 'name', 'model', 'internal_id', 'serial_number',
                  'condition', 'description', 'current_stock', 'created_at']


class EquipmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight equipment serializer for dropdowns."""
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'internal_id']


# ──────────────────────────────────────────────
# Movement
# ──────────────────────────────────────────────
class MovementSerializer(serializers.ModelSerializer):
    completed_by_name = serializers.CharField(source='completed_by.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True,
                                              default=None)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_internal_id = serializers.CharField(source='equipment.internal_id', read_only=True)
    direction_name = serializers.CharField(source='direction.name', read_only=True, default=None)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)

    class Meta:
        model = Movement
        fields = ['id', 'completed_by', 'completed_by_name', 'assigned_to',
                  'assigned_to_name', 'equipment', 'equipment_name',
                  'equipment_internal_id', 'quantity', 'action_type',
                  'date', 'notes', 'direction', 'direction_name',
                  'department', 'department_name']
        read_only_fields = ['id', 'date', 'completed_by']


class MovementCreateSerializer(serializers.Serializer):
    """Custom serializer with stock validation."""
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.IntegerField(min_value=1)
    action_type = serializers.ChoiceField(choices=Movement.ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    direction = serializers.PrimaryKeyRelatedField(
        queryset=Direction.objects.all(), required=False, allow_null=True
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True
    )

    def validate(self, data):
        action = data['action_type']
        equipment = data['equipment']
        quantity = data['quantity']

        # assigned_to is required for PRET and SORTIE
        if action in ['PRET', 'SORTIE'] and not data.get('assigned_to'):
            raise serializers.ValidationError(
                {'assigned_to': "Le bénéficiaire est obligatoire pour un prêt ou une sortie."}
            )

        # Prevent negative stock
        if action in ['PRET', 'SORTIE']:
            current = equipment.current_stock
            if quantity > current:
                raise serializers.ValidationError(
                    {'quantity': f"Stock insuffisant. Disponible: {current}, demandé: {quantity}."}
                )

        return data

    def create(self, validated_data):
        validated_data['completed_by'] = self.context['request'].user
        return Movement.objects.create(**validated_data)


# ──────────────────────────────────────────────
# Stock (read-only, computed)
# ──────────────────────────────────────────────
class StockSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField()
    equipment_name = serializers.CharField()
    internal_id = serializers.CharField()
    model = serializers.CharField()
    condition = serializers.CharField()
    current_stock = serializers.IntegerField()


# ──────────────────────────────────────────────
# Active Loans
# ──────────────────────────────────────────────
class ActiveLoanSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField()
    equipment_name = serializers.CharField()
    internal_id = serializers.CharField()
    assigned_to_name = serializers.CharField()
    assigned_to_id = serializers.UUIDField()
    quantity_loaned = serializers.IntegerField()
    loan_date = serializers.DateTimeField()
    direction_name = serializers.CharField(allow_null=True)
