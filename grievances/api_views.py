
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from departments.models import Department, ComplaintCategory

from .models import (
    Grievance,
    ComplaintAssignment,
    StatusHistory,
    ComplaintFeedback,
    Notification,
    ResolutionEvidence,
)

from .serializers import (
    DepartmentSerializer,
    ComplaintCategorySerializer,
    GrievanceSerializer,
    ComplaintAssignmentSerializer,
    StatusHistorySerializer,
    ComplaintFeedbackSerializer,
    NotificationSerializer,
    ResolutionEvidenceSerializer,
)


def is_admin(user):
    return user.role == 'admin' or user.is_superuser


def can_manage_department(user, department):
    if is_admin(user):
        return True

    return (
        user.role == 'manager'
        and department.manager_id == user.id
    )


def notify_user(user, title, message):
    if user:
        Notification.objects.create(
            user=user,
            title=title,
            message=message
        )


# -----------------------------------------
# DEPARTMENT API
# -----------------------------------------

@api_view(['GET'])
def department_list(request):
    departments = Department.objects.filter(is_active=True)

    serializer = DepartmentSerializer(
        departments,
        many=True
    )

    return Response(serializer.data)


# -----------------------------------------
# COMPLAINT CATEGORY API
# -----------------------------------------

@api_view(['GET'])
def category_list(request):
    department_id = request.query_params.get('department')

    categories = ComplaintCategory.objects.filter(
        is_active=True,
        department__is_active=True
    )

    if department_id:
        categories = categories.filter(
            department_id=department_id
        )

    serializer = ComplaintCategorySerializer(
        categories,
        many=True
    )

    return Response(serializer.data)


# -----------------------------------------
# GRIEVANCE LIST AND CREATE API
# -----------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def grievance_list_create(request):

    if request.method == 'GET':

        if is_admin(request.user):
            grievances = Grievance.objects.all()

        elif request.user.role == 'manager':
            grievances = Grievance.objects.filter(
                department__manager=request.user
            )

        elif request.user.role == 'citizen':
            grievances = Grievance.objects.filter(
                citizen=request.user
            )

        else:
            return Response(
                {'error': 'Unauthorized role.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = GrievanceSerializer(
            grievances.order_by('-created_at'),
            many=True
        )

        return Response(serializer.data)

    if request.user.role != 'citizen':
        return Response(
            {'error': 'Only citizens can submit complaints.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = GrievanceSerializer(data=request.data)

    if serializer.is_valid():
        with transaction.atomic():

            grievance = serializer.save(
                citizen=request.user
            )

            StatusHistory.objects.create(
                grievance=grievance,
                previous_status='',
                new_status='submitted',
                remarks='Complaint submitted.',
                changed_by=request.user
            )

            if grievance.department.manager:
                notify_user(
                    grievance.department.manager,
                    'New Complaint Received',
                    f'Complaint {grievance.complaint_id} has been submitted.'
                )

        return Response(
            GrievanceSerializer(grievance).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# -----------------------------------------
# GRIEVANCE DETAIL API
# -----------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def grievance_detail(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk
    )

    allowed = (
        is_admin(request.user)
        or grievance.citizen_id == request.user.id
        or (
            request.user.role == 'manager'
            and grievance.department.manager_id == request.user.id
        )
    )

    if not allowed:
        return Response(
            {'error': 'You cannot access this complaint.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = GrievanceSerializer(grievance)

    return Response(serializer.data)


# -----------------------------------------
# COMPLAINT ASSIGNMENT API
# -----------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_complaint(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk
    )

    if not can_manage_department(
        request.user,
        grievance.department
    ):
        return Response(
            {'error': 'You cannot assign this complaint.'},
            status=status.HTTP_403_FORBIDDEN
        )

    assigned_to_id = request.data.get('assigned_to')

    if not assigned_to_id:
        return Response(
            {'error': 'assigned_to is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    assigned_to = get_object_or_404(
    User,
    pk=assigned_to_id
)

    if assigned_to.role != 'manager':
        return Response(
            {'error': 'The selected user must be a department manager.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if assigned_to.id != grievance.department.manager_id:
        return Response(
            {'error': 'The selected manager does not manage this department.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():

        ComplaintAssignment.objects.filter(
            grievance=grievance,
            is_active=True
        ).update(is_active=False)

        assignment = ComplaintAssignment.objects.create(
            grievance=grievance,
            assigned_to=assigned_to,
            assigned_by=request.user,
            remarks=request.data.get('remarks', ''),
            is_active=True
        )

        old_status = grievance.status

        if old_status != 'assigned':
            grievance.status = 'assigned'
            grievance.save(update_fields=['status', 'updated_at'])

            StatusHistory.objects.create(
                grievance=grievance,
                previous_status=old_status,
                new_status='assigned',
                remarks='Complaint assigned to department manager.',
                changed_by=request.user
            )

        notify_user(
            assigned_to,
            'Complaint Assigned',
            f'Complaint {grievance.complaint_id} has been assigned to you.'
        )

    return Response(
        ComplaintAssignmentSerializer(assignment).data,
        status=status.HTTP_201_CREATED
    )


# -----------------------------------------
# COMPLAINT STATUS UPDATE API
# -----------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_complaint_status(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk
    )

    if not can_manage_department(
        request.user,
        grievance.department
    ):
        return Response(
            {'error': 'You cannot update this complaint.'},
            status=status.HTTP_403_FORBIDDEN
        )

    new_status = request.data.get('status')

    valid_statuses = dict(Grievance.STATUS_CHOICES)

    allowed_transitions = {
        'submitted': ['under_review', 'rejected', 'on_hold'],
        'under_review': ['assigned', 'rejected', 'on_hold'],
        'assigned': ['in_progress', 'on_hold', 'rejected'],
        'in_progress': ['resolved', 'on_hold'],
        'resolved': ['closed', 'reopened'],
        'closed': ['reopened'],
        'rejected': ['reopened'],
        'on_hold': ['under_review', 'in_progress', 'rejected'],
        'reopened': ['under_review', 'assigned'],
    }

    if new_status not in valid_statuses:
        return Response(
            {'error': 'Invalid complaint status.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if new_status not in allowed_transitions.get(
        grievance.status, []
    ):
        return Response(
            {
                'error': (
                    f'Cannot change status from '
                    f'{grievance.status} to {new_status}.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    remarks = request.data.get('remarks', '')
    old_status = grievance.status

    if new_status == 'resolved' and not remarks.strip():
        return Response(
            {'error': 'Resolution remarks are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():

        grievance.status = new_status

        if new_status == 'resolved':
            grievance.resolution_remarks = remarks

        elif new_status == 'reopened':
            grievance.resolution_remarks = ''

        grievance.save()

        StatusHistory.objects.create(
            grievance=grievance,
            previous_status=old_status,
            new_status=new_status,
            remarks=remarks,
            changed_by=request.user
        )

        notify_user(
            grievance.citizen,
            'Complaint Status Updated',
            f'Your complaint {grievance.complaint_id} is now {new_status.replace("_", " ")}.'
        )

    return Response(
        GrievanceSerializer(grievance).data
    )


# -----------------------------------------
# COMPLAINT STATUS HISTORY API
# -----------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def complaint_history(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk
    )

    allowed = (
        is_admin(request.user)
        or grievance.citizen_id == request.user.id
        or (
            request.user.role == 'manager'
            and grievance.department.manager_id == request.user.id
        )
    )

    if not allowed:
        return Response(
            {'error': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )

    history = grievance.status_history.all()

    serializer = StatusHistorySerializer(
        history,
        many=True
    )

    return Response(serializer.data)


# -----------------------------------------
# CITIZEN FEEDBACK API
# -----------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk,
        citizen=request.user
    )

    if grievance.status not in ['resolved', 'closed']:
        return Response(
            {'error': 'Feedback is available after resolution.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if ComplaintFeedback.objects.filter(
        grievance=grievance
    ).exists():
        return Response(
            {'error': 'Feedback has already been submitted.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ComplaintFeedbackSerializer(
        data=request.data,
        context={'grievance': grievance}
    )

    if serializer.is_valid():
        feedback = serializer.save(
            grievance=grievance,
            citizen=request.user
        )

        return Response(
            ComplaintFeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# -----------------------------------------
# RESOLUTION EVIDENCE API
# -----------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_evidence(request, pk):

    grievance = get_object_or_404(
        Grievance,
        pk=pk
    )

    if not can_manage_department(
        request.user,
        grievance.department
    ):
        return Response(
            {'error': 'You cannot upload evidence for this complaint.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if 'photograph' not in request.FILES:
        return Response(
            {'error': 'A photograph is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ResolutionEvidenceSerializer(
        data=request.data
    )

    if serializer.is_valid():
        evidence = serializer.save(
            grievance=grievance,
            uploaded_by=request.user
        )

        return Response(
            ResolutionEvidenceSerializer(evidence).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# -----------------------------------------
# USER NOTIFICATIONS API
# -----------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):

    notifications = Notification.objects.filter(
        user=request.user
    )

    serializer = NotificationSerializer(
        notifications,
        many=True
    )

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):

    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    return Response({
        'message': 'Notification marked as read.'
    })
