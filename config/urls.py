from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),

    path('api/', include('grievances.api_urls')),

    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    path('grievances/', include('grievances.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
