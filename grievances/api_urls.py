
from django.urls import path
from . import api_views

urlpatterns = [
    path('departments/', api_views.department_list, name='api_departments'),

    path('categories/', api_views.category_list, name='api_category_list'),

    path(
        'complaints/',
        api_views.grievance_list_create,
        name='api_complaints'
    ),

    path(
        'complaints/<int:pk>/',
        api_views.grievance_detail,
        name='api_complaint_detail'
    ),

    path(
        'complaints/<int:pk>/assign/',
        api_views.assign_complaint,
        name='api_assign_complaint'
    ),

    path(
        'complaints/<int:pk>/status/',
        api_views.update_complaint_status,
        name='api_update_status'
    ),

    path(
        'complaints/<int:pk>/history/',
        api_views.complaint_history,
        name='api_complaint_history'
    ),

    path(
        'complaints/<int:pk>/feedback/',
        api_views.submit_feedback,
        name='api_submit_feedback'
    ),

    path(
        'complaints/<int:pk>/evidence/',
        api_views.upload_evidence,
        name='api_upload_evidence'
    ),

    path(
        'notifications/',
        api_views.notification_list,
        name='api_notifications'
    ),

    path(
        'notifications/<int:pk>/read/',
        api_views.mark_notification_read,
        name='api_mark_notification_read'
    ),
]
