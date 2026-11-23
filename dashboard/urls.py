
from django.urls import path
from . import views

urlpatterns = [
    path('citizen/', views.citizen_dashboard, name='citizen_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    # Department details
    path(
        'department/<int:department_id>/',
        views.department_detail,
        name='department_detail'
    ),

    # Central Department Management Portal
    path(
        'departments/',
        views.department_management,
        name='department_management'
    ),
]
