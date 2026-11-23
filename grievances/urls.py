
from django.urls import path
from . import views

urlpatterns = [
    # Citizen routes
    path(
        'submit/',
        views.submit_complaint,
        name='submit_complaint'
    ),

    path(
        '<int:pk>/',
        views.complaint_detail,
        name='complaint_detail'
    ),

    path(
        '<int:pk>/feedback/',
        views.submit_feedback,
        name='submit_feedback'
    ),

    # Manager route
    path(
        '<int:pk>/update-status/',
        views.update_complaint_status,
        name='update_complaint_status'
    ),

    # Notification route
    path(
        'notifications/<int:pk>/read/',
        views.mark_notification_read,
        name='mark_notification_read'
    ),
]
