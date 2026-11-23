from django.contrib import admin
from .models import Grievance

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = (
        'complaint_id',
        'citizen',
        'department',
        'category',
        'status',
        'created_at',
    )

    list_filter = ('status', 'department', 'priority')
    search_fields = ('complaint_id', 'title', 'citizen__username')