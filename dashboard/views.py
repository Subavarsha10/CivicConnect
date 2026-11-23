
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q

from grievances.models import Grievance, Notification
from departments.models import Department


# ROLE CHECKING FUNCTIONS

def is_citizen(user):
    return user.is_authenticated and user.role == 'citizen'


def is_manager(user):
    return user.is_authenticated and user.role == 'manager'


def is_admin(user):
    return user.is_authenticated and (
        user.role == 'admin' or user.is_superuser
    )


# CITIZEN DASHBOARD

@login_required
@user_passes_test(is_citizen)
def citizen_dashboard(request):

    complaints = Grievance.objects.filter(
        citizen=request.user
    ).order_by('-created_at')

    total = complaints.count()

    pending = complaints.filter(
        status__in=[
            'submitted', 'under_review', 'assigned',
            'in_progress', 'on_hold', 'reopened'
        ]
    ).count()

    resolved = complaints.filter(
        status__in=['resolved', 'closed']
    ).count()

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    unread_notifications = notifications.filter(
        is_read=False
    ).count()

    return render(
        request,
        'dashboard/citizen.html',
        {
            'complaints': complaints[:10],
            'total': total,
            'pending': pending,
            'resolved': resolved,
            'notifications': notifications[:10],
            'unread_notifications': unread_notifications,
        }
    )


# DEPARTMENT MANAGER DASHBOARD

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):

    # Get the active department assigned to this manager
    department = request.user.managed_departments.filter(
        is_active=True
    ).first()

    complaints = Grievance.objects.none()

    if department:

        # Display only complaints belonging to this department
        complaints = Grievance.objects.filter(
            department=department
        ).select_related(
            'citizen',
            'department',
            'category'
        ).order_by('-created_at')

    else:
        messages.warning(
            request,
            'No active department is assigned to your account. Please contact the administrator.'
        )

    total = complaints.count()

    pending = complaints.filter(
        status__in=['submitted', 'under_review']
    ).count()

    in_progress = complaints.filter(
        status__in=[
            'assigned', 'in_progress', 'on_hold', 'reopened'
        ]
    ).count()

    resolved = complaints.filter(
        status__in=['resolved', 'closed']
    ).count()

    return render(
        request,
        'dashboard/manager.html',
        {
            'department': department,
            'complaints': complaints,
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'resolved': resolved,
        }
    )


# CENTRAL ADMINISTRATOR DASHBOARD

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    departments = Department.objects.select_related(
        'manager'
    ).annotate(
        total_complaints=Count('grievances'),

        pending_complaints=Count(
            'grievances',
            filter=Q(
                grievances__status__in=[
                    'submitted', 'under_review'
                ]
            )
        ),

        in_progress_complaints=Count(
            'grievances',
            filter=Q(
                grievances__status__in=[
                    'assigned', 'in_progress',
                    'on_hold', 'reopened'
                ]
            )
        ),

        resolved_complaints=Count(
            'grievances',
            filter=Q(
                grievances__status__in=[
                    'resolved', 'closed'
                ]
            )
        )
    ).order_by('name')

    total = Grievance.objects.count()

    pending = Grievance.objects.filter(
        status__in=['submitted', 'under_review']
    ).count()

    in_progress = Grievance.objects.filter(
        status__in=[
            'assigned', 'in_progress', 'on_hold', 'reopened'
        ]
    ).count()

    resolved = Grievance.objects.filter(
        status__in=['resolved', 'closed']
    ).count()

    return render(
        request,
        'dashboard/admin.html',
        {
            'departments': departments,
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'resolved': resolved,
        }
    )


# CENTRAL ADMINISTRATOR - DEPARTMENT DETAILS

@login_required
@user_passes_test(is_admin)
def department_detail(request, department_id):

    department = get_object_or_404(
        Department.objects.select_related('manager'),
        id=department_id
    )

    complaints = Grievance.objects.filter(
        department=department
    ).select_related(
        'citizen',
        'category'
    ).order_by('-created_at')

    return render(
        request,
        'dashboard/department_detail.html',
        {
            'department': department,
            'complaints': complaints,
            'total': complaints.count(),
        }
    )


# DEPARTMENT MANAGEMENT PORTAL

@login_required
@user_passes_test(is_admin)
def department_management(request):

    departments = Department.objects.select_related(
        'manager'
    ).annotate(
        total_complaints=Count('grievances'),

        pending_complaints=Count(
            'grievances',
            filter=Q(
                grievances__status__in=[
                    'submitted', 'under_review'
                ]
            )
        ),

        resolved_complaints=Count(
            'grievances',
            filter=Q(
                grievances__status__in=[
                    'resolved', 'closed'
                ]
            )
        )
    ).order_by('name')

    return render(
        request,
        'dashboard/department_management.html',
        {
            'departments': departments
        }
    )
