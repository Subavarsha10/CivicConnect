
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction

from .models import (
    Grievance,
    StatusHistory,
    Notification,
    ComplaintFeedback,
)

from .forms import GrievanceForm


def is_citizen(user):
    return user.is_authenticated and user.role == 'citizen'


def is_manager(user):
    return user.is_authenticated and user.role == 'manager'


# CITIZEN: SUBMIT COMPLAINT
@login_required
@user_passes_test(is_citizen)
def submit_complaint(request):
    if request.method == 'POST':
        form = GrievanceForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                grievance = form.save(commit=False)
                grievance.citizen = request.user
                grievance.save()

                StatusHistory.objects.create(
                    grievance=grievance,
                    previous_status='',
                    new_status='submitted',
                    remarks='Complaint submitted by citizen.',
                    changed_by=request.user
                )

                manager = grievance.department.manager

                if manager:
                    Notification.objects.create(
                        user=manager,
                        title='New Complaint Received',
                        message=(
                            f'New complaint {grievance.complaint_id} '
                            f'has been submitted.'
                        )
                    )

            messages.success(
                request,
                f'Complaint submitted successfully! Your ID is {grievance.complaint_id}'
            )

            return redirect('complaint_detail', pk=grievance.pk)

    else:
        form = GrievanceForm()

    return render(
        request,
        'grievances/submit_complaint.html',
        {'form': form}
    )


# CITIZEN: VIEW COMPLAINT DETAILS
@login_required
@user_passes_test(is_citizen)
def complaint_detail(request, pk):
    grievance = get_object_or_404(
        Grievance,
        pk=pk,
        citizen=request.user
    )

    history = grievance.status_history.all()

    feedback = ComplaintFeedback.objects.filter(
        grievance=grievance
    ).first()

    return render(
        request,
        'grievances/complaint_detail.html',
        {
            'grievance': grievance,
            'history': history,
            'feedback': feedback,
        }
    )


# CITIZEN: SUBMIT FEEDBACK
@login_required
@user_passes_test(is_citizen)
def submit_feedback(request, pk):
    grievance = get_object_or_404(
        Grievance,
        pk=pk,
        citizen=request.user
    )

    if grievance.status not in ['resolved', 'closed']:
        messages.error(
            request,
            'Feedback is available only after resolution.'
        )
        return redirect('complaint_detail', pk=pk)

    if ComplaintFeedback.objects.filter(grievance=grievance).exists():
        messages.warning(
            request,
            'Feedback has already been submitted.'
        )
        return redirect('complaint_detail', pk=pk)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
        except (TypeError, ValueError):
            rating = 0

        comments = request.POST.get('comments', '').strip()

        if rating not in range(1, 6):
            messages.error(
                request,
                'Please select a valid rating between 1 and 5.'
            )
        else:
            ComplaintFeedback.objects.create(
                grievance=grievance,
                citizen=request.user,
                rating=rating,
                comments=comments
            )

            messages.success(
                request,
                'Thank you for your feedback!'
            )

    return redirect('complaint_detail', pk=pk)


# MANAGER: UPDATE COMPLAINT STATUS
@login_required
@user_passes_test(is_manager)
def update_complaint_status(request, pk):
    if request.method != 'POST':
        return redirect('manager_dashboard')

    grievance = get_object_or_404(
        Grievance,
        pk=pk,
        department__manager=request.user
    )

    new_status = request.POST.get('status', '').strip()
    remarks = request.POST.get('resolution_remarks', '').strip()

    valid_statuses = dict(Grievance.STATUS_CHOICES)

    if new_status not in valid_statuses:
        messages.error(request, 'Please select a valid complaint status.')
        return redirect('manager_dashboard')

    if new_status in ['resolved', 'rejected'] and not remarks:
        messages.error(
            request,
            'Please provide remarks before resolving or rejecting a complaint.'
        )
        return redirect('manager_dashboard')

    previous_status = grievance.status

    with transaction.atomic():
        grievance.status = new_status
        grievance.resolution_remarks = remarks
        grievance.save()

        if previous_status != new_status:
            StatusHistory.objects.create(
                grievance=grievance,
                previous_status=previous_status,
                new_status=new_status,
                remarks=remarks,
                changed_by=request.user
            )

            Notification.objects.create(
                user=grievance.citizen,
                title='Complaint Status Updated',
                message=(
                    f'Your complaint {grievance.complaint_id} '
                    f'has been updated to {valid_statuses[new_status]}. '
                    f'Remarks: {remarks or "No additional remarks."}'
                )
            )

    messages.success(
        request,
        f'Complaint {grievance.complaint_id} updated successfully.'
    )

    return redirect('manager_dashboard')


# CITIZEN: MARK NOTIFICATION AS READ
@login_required
@user_passes_test(is_citizen)
def mark_notification_read(request, pk):
    if request.method == 'POST':
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user
        )

        notification.is_read = True
        notification.save(update_fields=['is_read'])

        messages.success(
            request,
            'Notification marked as read.'
        )

    return redirect('citizen_dashboard')
