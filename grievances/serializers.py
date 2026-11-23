
from rest_framework import serializers
from django.contrib.auth import get_user_model

from departments.models import Department, ComplaintCategory
from .models import (
    Grievance,
    ComplaintAssignment,
    StatusHistory,
    ComplaintFeedback,
    Notification,
    ResolutionEvidence,
)

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active']


class ComplaintCategorySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )

    class Meta:
        model = ComplaintCategory
        fields = [
            'id',
            'department',
            'department_name',
            'name',
            'description',
            'is_active',
        ]


class GrievanceSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(
        source='citizen.username',
        read_only=True
    )

    department_name = serializers.CharField(
        source='department.name',
        read_only=True
    )

    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Grievance
        fields = [
            'id',
            'complaint_id',
            'citizen',
            'citizen_name',
            'department',
            'department_name',
            'category',
            'category_name',
            'title',
            'description',
            'address',
            'photograph',
            'priority',
            'status',
            'resolution_remarks',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'complaint_id',
            'citizen',
            'status',
            'resolution_remarks',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        department = attrs.get(
            'department',
            getattr(self.instance, 'department', None)
        )

        category = attrs.get(
            'category',
            getattr(self.instance, 'category', None)
        )

        if department and category:
            if category.department_id != department.id:
                raise serializers.ValidationError({
                    'category': 'This category does not belong to the selected department.'
                })

            if not department.is_active:
                raise serializers.ValidationError({
                    'department': 'This department is inactive.'
                })

            if not category.is_active:
                raise serializers.ValidationError({
                    'category': 'This category is inactive.'
                })

        return attrs


class ComplaintAssignmentSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source='assigned_to.username',
        read_only=True
    )

    class Meta:
        model = ComplaintAssignment
        fields = [
            'id',
            'grievance',
            'assigned_to',
            'assigned_to_name',
            'remarks',
            'is_active',
            'assigned_at',
        ]

        read_only_fields = [
            'id',
            'grievance',
            'assigned_to_name',
            'is_active',
            'assigned_at',
        ]


class StatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        source='changed_by.username',
        read_only=True,
        default=None
    )

    class Meta:
        model = StatusHistory
        fields = [
            'id',
            'previous_status',
            'new_status',
            'remarks',
            'changed_by_name',
            'changed_at',
        ]


class ComplaintFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintFeedback
        fields = [
            'id',
            'grievance',
            'rating',
            'comments',
            'created_at',
        ]

        read_only_fields = ['id', 'grievance', 'created_at']

    def validate(self, attrs):
        grievance = self.context.get('grievance')

        if grievance and grievance.status not in ['resolved', 'closed']:
            raise serializers.ValidationError(
                'Feedback can only be submitted after resolution.'
            )

        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'is_read',
            'created_at',
        ]


class ResolutionEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResolutionEvidence
        fields = [
            'id',
            'grievance',
            'photograph',
            'remarks',
            'uploaded_at',
        ]

        read_only_fields = [
            'id',
            'grievance',
            'uploaded_at',
        ]
