from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import calculate_rotation

urlpatterns = [
    path("calculate/", calculate_rotation, name="calculate"),
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)