
import uuid

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


def generate_complaint_id():
    return f"CC-{uuid.uuid4().hex[:10].upper()}"


def complaint_upload_path(instance, filename):
    return f"complaints/{instance.complaint_id}/{filename}"


def evidence_upload_path(instance, filename):
    return f"evidence/{instance.grievance.complaint_id}/{filename}"


class Grievance(models.Model):

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
        ('reopened', 'Reopened'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    complaint_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_complaint_id,
        editable=False
    )

    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grievances'
    )

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='grievances'
    )

    category = models.ForeignKey(
        'departments.ComplaintCategory',
        on_delete=models.PROTECT,
        related_name='grievances'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    address = models.TextField()

    photograph = models.ImageField(
        upload_to=complaint_upload_path,
        blank=True,
        null=True
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    resolution_remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.complaint_id


class ComplaintAssignment(models.Model):

    grievance = models.ForeignKey(
        Grievance,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_assignments'
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assignments'
    )

    remarks = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.grievance.complaint_id} - {self.assigned_to}"


class StatusHistory(models.Model):

    grievance = models.ForeignKey(
        Grievance,
        on_delete=models.CASCADE,
        related_name='status_history'
    )

    previous_status = models.CharField(max_length=20, blank=True)

    new_status = models.CharField(max_length=20)

    remarks = models.TextField(blank=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.grievance.complaint_id} - {self.new_status}"


class ComplaintFeedback(models.Model):

    grievance = models.OneToOneField(
        Grievance,
        on_delete=models.CASCADE,
        related_name='feedback'
    )

    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.grievance.complaint_id} - {self.rating}/5"


class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ResolutionEvidence(models.Model):

    grievance = models.ForeignKey(
        Grievance,
        on_delete=models.CASCADE,
        related_name='evidence'
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    photograph = models.ImageField(
        upload_to=evidence_upload_path
    )

    remarks = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence - {self.grievance.complaint_id}"


class AuditLog(models.Model):

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=100)

    object_type = models.CharField(max_length=100)

    object_id = models.CharField(max_length=100)

    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.object_type}"
