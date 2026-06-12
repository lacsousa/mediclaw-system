from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="MedicLaw API",
      default_version='v1',
      description="MedicLaw API",
      terms_of_service="https://www.mediclaw.com/policies/terms/",
      contact=openapi.Contact(email="contact@mediclaw.com"),
      license=openapi.License(name="Apache License 2.0"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/patients/", include("apps.patients.urls")),
    path("api/v1/health/", include("apps.health_logs.urls")),
    path("api/v1/conversations/", include("apps.conversations.urls")),
    path("api/v1/admin/knowledge/", include("apps.rag.urls")),
    path("api/v1/admin/", include("apps.audit.urls")),
    path("health/", include("apps.common.health_urls")),
]
