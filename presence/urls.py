
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import EtudiantViewSet

from .views import (
    EtudiantViewSet, EnseignantViewSet, DepartementViewSet,
    FormationViewSet, CoursViewSet, SessionCoursViewSet, PresenceViewSet
)
router = DefaultRouter()

router.register(r'api/etudiants', EtudiantViewSet, basename='api-etudiant')
router.register(r'api/enseignants', EnseignantViewSet, basename='api-enseignant')
router.register(r'api/departements', DepartementViewSet, basename='api-departement')
router.register(r'api/formations', FormationViewSet, basename='api-formation')
router.register(r'api/cours', CoursViewSet, basename='api-cours')
router.register(r'api/sessions', SessionCoursViewSet, basename='api-session')
router.register(r'api/presences', PresenceViewSet, basename='api-presence')
urlpatterns = [
    path('', views.home_view, name='home'),
    path('', include(router.urls)),

    # URLs Enseignant
    path('dashboard/enseignant/', views.dashboard_enseignant, name='dashboard_enseignant'),
    path('cours/<int:cours_id>/lancer-session/', views.lancer_session, name='lancer_session'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('cours/<int:cours_id>/stats/', views.cours_statistiques, name='cours_stats'),
    path('session/<int:session_id>/arreter/', views.arreter_session, name='arreter_session'),
    path('session/<int:session_id>/pdf/', views.session_pdf_view, name='session_pdf'),
    # URLs Étudiant
    path('scanner/', views.scanner_etudiant, name='scanner'),

    # URLs API (pour JavaScript/AJAX)
    path('api/valider-scan/', views.valider_scan, name='valider_scan'),
    path('api/session/<int:session_id>/refresh-qr/', views.rafraichir_qr, name='rafraichir_qr'),
    path('api/session/<int:session_id>/get-presences/', views.get_presences_api, name='get_presences_api'),

    # URLs Panneau Admin Personnalisé (Onglets)
    path('admin-custom/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-custom/creer-enseignant/', views.creer_enseignant_view, name='creer_enseignant'),
    path('admin-custom/creer-departement/', views.creer_departement_view, name='creer_departement'),

    # URLs Gestion CRUD Cours
    path('gestion/cours/', views.cours_list_view, name='cours_list'),
    path('gestion/cours/ajouter/', views.cours_create_view, name='cours_create'),
    path('gestion/cours/<int:pk>/modifier/', views.cours_update_view, name='cours_update'),
    path('gestion/cours/<int:pk>/supprimer/', views.cours_delete_view, name='cours_delete'),

    path('api/cours-filter/', views.api_get_cours_par_filtres, name='api_get_cours_filter'),
    # URLs Gestion CRUD Département
    path('gestion/departements/', views.departement_list_view, name='departement_list'),
    path('gestion/departements/ajouter/', views.departement_create_view, name='departement_create'),
    path('gestion/departements/<str:pk>/modifier/', views.departement_update_view, name='departement_update'),
    path('gestion/departements/<str:pk>/supprimer/', views.departement_delete_view, name='departement_delete'),

    # URLs Gestion CRUD Formation
    path('gestion/formations/', views.formation_list_view, name='formation_list'),
    path('gestion/formations/ajouter/', views.formation_create_view, name='formation_create'),
    path('gestion/formations/<int:pk>/modifier/', views.formation_update_view, name='formation_update'),
    path('gestion/formations/<int:pk>/supprimer/', views.formation_delete_view, name='formation_delete'),

    # URLs Gestion CRUD Enseignant
    path('gestion/enseignants/', views.enseignant_list_view, name='enseignant_list'),
    path('gestion/enseignants/ajouter/', views.enseignant_create_view, name='enseignant_create'),
    path('gestion/enseignants/<int:pk>/modifier/', views.enseignant_update_view, name='enseignant_update'),
    path('gestion/enseignants/<int:pk>/supprimer/', views.enseignant_delete_view, name='enseignant_delete'),

    # URLs Gestion CRUD Étudiant
    path('gestion/etudiants/', views.etudiant_list_view, name='etudiant_list'),
    path('gestion/etudiants/ajouter/', views.etudiant_create_view, name='etudiant_create'),
    path('gestion/etudiants/<int:pk>/modifier/', views.etudiant_update_view, name='etudiant_update'),
    path('gestion/etudiants/<int:pk>/supprimer/', views.etudiant_delete_view, name='etudiant_delete'),
    path('api/etudiants-filter/', views.api_get_etudiants_par_formation, name='api_get_etudiants_filter'),

    # Niveaux
    path('api/get-niveaux/', views.api_get_niveaux, name='api_get_niveaux'),

    #Formations
    path('api/get-formations/', views.api_get_formations, name='api_get_formations'),

]