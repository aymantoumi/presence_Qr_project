from django.contrib import admin
from django.urls import path, include

# --- IMPORTATIONS POUR SWAGGER ---
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- AJOUT IMPORTANT : Importez les vues de l'application comptes ---
from comptes import views as comptes_views

# Configuration de la vue Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="API Gestion de Présence",
        default_version='v1',
        description="Documentation des API pour l'application de présence",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@exemple.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Vos URLs existantes (Application presence)
    path('', include('presence.urls')),

    # URLs d'authentification
    path('comptes/', include('django.contrib.auth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Pour Swagger

    # --- AJOUT IMPORTANT : Les routes manquantes ---
    # Inscription
    path('comptes/inscription/', comptes_views.signup_view, name='signup'),
    # Redirection Dashboard (C'est celle qui causait l'erreur)
    path('dashboard/', comptes_views.dashboard_redirect_view, name='dashboard_redirect'),
    # -----------------------------------------------

    # --- URLs SWAGGER ---
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]