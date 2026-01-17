import json
import io
import base64
import qrcode
from rest_framework import viewsets
from xhtml2pdf import pisa
from psycopg2 import IntegrityError

from django.template.loader import get_template
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt


from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from comptes import models
from comptes.models import Utilisateur, Departement, Formation
from .forms import CoursForm, EtudiantUpdateForm, EtudiantCreationForm, EnseignantCreationForm, EnseignantUpdateForm, \
    FormationForm, DepartementForm
from .models import Cours, SessionCours, Presence, Enseignant, Etudiant
from .utils import generer_jeton_qr, valider_jeton_qr
from rest_framework import viewsets, permissions
from .serializers import (
    DepartementSerializer, FormationSerializer, EnseignantSerializer,
    EtudiantSerializer, CoursSerializer, SessionCoursSerializer, PresenceSerializer
)
from .permissions import IsEnseignant, IsEtudiant, IsAdmin

# --- Helpers de rôle (Deprecated for API, kept for Template Views) ---
def est_enseignant(user):
    return user.is_authenticated and hasattr(user, 'enseignant')


def est_etudiant(user):
    return user.is_authenticated and hasattr(user, 'etudiant')


def est_admin(user):
    return user.is_authenticated and user.role == 'admin'


# --- Vue d'accueil ---
def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    return render(request, 'home.html')


# --- Vues Enseignant ---
@user_passes_test(est_enseignant, login_url='/comptes/login/')
def dashboard_enseignant(request):
    profil_enseignant = request.user.enseignant
    cours_list = Cours.objects.filter(enseignant=profil_enseignant)

    # --- AJOUT : On vérifie s'il y a une session active pour chaque cours ---
    for cours in cours_list:
        # On cherche une session active pour ce cours
        session_active = SessionCours.objects.filter(cours=cours, actif=True).first()
        # On "attache" cette session temporairement à l'objet cours pour l'utiliser dans le HTML
        cours.session_en_cours = session_active

    return render(request, 'presence/dashboard_enseignant.html', {'cours_list': cours_list})


@user_passes_test(est_enseignant)
def lancer_session(request, cours_id):
    profil_enseignant = request.user.enseignant
    cours = get_object_or_404(Cours, id=cours_id, enseignant=profil_enseignant)
    SessionCours.objects.filter(cours=cours, actif=True).update(actif=False)
    session = SessionCours.objects.create(cours=cours, enseignant=profil_enseignant)
    jeton, expiration = generer_jeton_qr(session)
    session.qr_token = jeton
    session.qr_expiration = expiration
    session.save()
    return redirect('session_detail', session_id=session.id)


@user_passes_test(est_enseignant)
def session_detail(request, session_id):
    profil_enseignant = request.user.enseignant
    session = get_object_or_404(SessionCours, id=session_id, enseignant=profil_enseignant)
    qr_img = qrcode.make(session.qr_token)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return render(request, 'presence/session_detail.html', {
        'session': session,
        'qr_image_base64': qr_base64
    })


@swagger_auto_schema(
    method='get',
    operation_description="Rafraîchir le QR code d'une session active",
    responses={200: openapi.Response("QR Code Base64", examples={"application/json": {"qr_image_base64": "..."}})}
)
@api_view(['GET'])
@permission_classes([IsEnseignant])
def rafraichir_qr(request, session_id):
    # Utilisation de la permission IsEnseignant
    profil_enseignant = request.user.enseignant
    session = get_object_or_404(SessionCours, id=session_id, enseignant=profil_enseignant)
    if not session.actif:
        return JsonResponse({'error': 'Session terminée'}, status=400)
    jeton, expiration = generer_jeton_qr(session)
    session.qr_token = jeton
    session.qr_expiration = expiration
    session.save()
    qr_img = qrcode.make(jeton)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return JsonResponse({'qr_image_base64': qr_base64})


@swagger_auto_schema(
    method='get',
    operation_description="Récupérer la liste des étudiants présents pour une session",
    responses={200: "Liste JSON des présences"}
)
@api_view(['GET'])
@permission_classes([IsEnseignant | IsAdmin])
def get_presences_api(request, session_id):
    session = get_object_or_404(SessionCours, id=session_id)

    # Check ownership if not admin
    if not request.user.role == 'admin':
        if session.enseignant != request.user.enseignant:
             return HttpResponseForbidden("Vous n'êtes pas le propriétaire de cette session.")

    presences = Presence.objects.filter(session=session).order_by('horodatage_scan')
    presences_data = []
    for p in presences:
        presences_data.append({
            'nom': p.etudiant.id.nom,
            'prenom': p.etudiant.id.prenom,
            'heure': p.horodatage_scan.strftime('%H:%M:%S')
        })
    return JsonResponse({'presences': presences_data})


# --- Vues Étudiant ---
@user_passes_test(est_etudiant, login_url='/comptes/login/')
def scanner_etudiant(request):
    profil_etudiant = request.user.etudiant

    # 1. On garde l'historique global pour l'affichage par défaut
    historique_global = Presence.objects.filter(etudiant=profil_etudiant).order_by('-horodatage_scan')[:5]

    # 2. On récupère les cours
    cours_inscrits = profil_etudiant.cours_inscrits.all()

    # 3. On prépare les données détaillées pour chaque cours
    cours_stats = {}

    for cours in cours_inscrits:
        # Récupérer toutes les sessions *terminées* ou *commencées* pour ce cours
        sessions_passees = SessionCours.objects.filter(cours=cours).order_by('-date_debut')
        total_sessions = sessions_passees.count()

        # Récupérer les présences de l'étudiant pour ce cours
        presences = Presence.objects.filter(etudiant=profil_etudiant, session__cours=cours).select_related('session')
        nb_presences = presences.count()

        # Calcul des absences
        nb_absences = total_sessions - nb_presences
        if nb_absences < 0: nb_absences = 0

        # Liste détaillée des dates de présence
        historique_cours = []
        ids_sessions_presentes = []

        for p in presences:
            historique_cours.append({
                'date': p.session.date_debut.strftime("%d/%m/%Y"),
                'heure': p.session.date_debut.strftime("%H:%M"),
                'statut': 'Présent',
                'couleur': 'success'
            })
            ids_sessions_presentes.append(p.session.id)

        for s in sessions_passees:
            if s.id not in ids_sessions_presentes:
                historique_cours.append({
                    'date': s.date_debut.strftime("%d/%m/%Y"),
                    'heure': s.date_debut.strftime("%H:%M"),
                    'statut': 'Absent',
                    'couleur': 'danger'
                })

        historique_cours.sort(key=lambda x: x['date'], reverse=True)

        cours_stats[cours.id] = {
            'nom': cours.nom,
            'code': cours.code,
            'total': total_sessions,
            'present': nb_presences,
            'absent': nb_absences,
            'historique': historique_cours
        }

    cours_stats_json = json.dumps(cours_stats)

    return render(request, 'presence/scanner_etudiant.html', {
        'profil': profil_etudiant,
        'cours_inscrits': cours_inscrits,
        'historique': historique_global,
        'cours_stats_json': cours_stats_json,
    })


# =======================================================
# ==== API VALIDER SCAN (ADAPTÉE POUR SWAGGER) ====
# =======================================================

@swagger_auto_schema(
    method='post',
    operation_description="Valider un scan QR code",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['jeton'],
        properties={
            'jeton': openapi.Schema(type=openapi.TYPE_STRING, description="Le token JWT scanné du QR code"),
        },
    ),
    responses={
        200: openapi.Response("Succès",
                              examples={"application/json": {"success": True, "message": "Présence validée"}}),
        400: "Erreur de requête",
        403: "Non autorisé"
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication]) # Enforce JWT only
@permission_classes([IsEtudiant]) # Enforce Student Role
def valider_scan(request):
    """
    Validation du scan QR code par un étudiant.
    """
    # Avec @api_view, request.data contient les données POST (JSON ou Form)
    # Plus besoin de vérifier request.user.etudiant manuellement grâce à IsEtudiant

    jeton_scanne = request.data.get('jeton')

    if not jeton_scanne:
        return JsonResponse({'success': False, 'message': 'Aucun jeton fourni.'})

    # Valider le jeton JWT
    payload = valider_jeton_qr(jeton_scanne)

    if payload is None:
        return JsonResponse({'success': False, 'message': 'QR Code expiré ou invalide.'})

    # Récupérer la session
    try:
        session = SessionCours.objects.get(id=payload['session_id'], actif=True)
    except SessionCours.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Session de cours introuvable ou terminée.'})

    # Vérifier que le QR code correspond
    if session.qr_token != jeton_scanne:
        return JsonResponse({'success': False, 'message': 'QR Code périmé.'})

    profil_etudiant = request.user.etudiant

    # Utiliser profil_etudiant.id
    if not session.cours.etudiants.filter(id=profil_etudiant.id).exists():
        return JsonResponse({'success': False, 'message': f'Vous n\'êtes pas inscrit au cours {session.cours.nom}.'})

    # Enregistrer la présence
    presence, created = Presence.objects.get_or_create(
        etudiant=profil_etudiant,
        session=session,
        defaults={'qr_token_utilise': jeton_scanne}
    )

    if created:
        return JsonResponse({
            'success': True,
            'message': f'Présence validée pour {session.cours.nom} !',
            'cours_nom': session.cours.nom
        })
    else:
        return JsonResponse({'success': False, 'message': 'Présence déjà enregistrée pour cette session.'})


# --- Vues Admin (Panneau personnalisé) ---
@user_passes_test(est_admin, login_url='/comptes/login/')
def admin_dashboard_view(request):
    enseignants = Enseignant.objects.all().select_related('id')
    departements = Departement.objects.all()
    etudiants = Etudiant.objects.all().select_related('id')
    semestre_choices = Etudiant.SEMESTRE_CHOICES
    context = {
        'enseignants': enseignants,
        'departements': departements,
        'etudiants': etudiants,
        'semestre_choices': semestre_choices,
    }
    return render(request, 'presence/admin_dashboard.html', context)


@user_passes_test(est_admin)
@transaction.atomic
def creer_enseignant_view(request):
    if request.method == 'POST':
        email = request.POST.get('ens_email')
        prenom = request.POST.get('ens_prenom')
        nom = request.POST.get('ens_nom')
        password = request.POST.get('ens_password')
        departement_id = request.POST.get('ens_departement')
        try:
            user = Utilisateur.objects.create_user(
                username=email, email=email, password=password,
                nom=nom, prenom=prenom, role=Utilisateur.Role.ENSEIGNANT
            )
            departement = Departement.objects.get(code=departement_id)
            Enseignant.objects.create(id=user, departement=departement)
            messages.success(request, f"L'enseignant {prenom} {nom} a été créé.")
        except Exception as e:
            messages.error(request, f"Erreur création enseignant: {e}")
    return redirect(reverse('admin_dashboard') + '#enseignant-tab')


@user_passes_test(est_admin)
def creer_departement_view(request):
    if request.method == 'POST':
        code = request.POST.get('dept_code')
        nom = request.POST.get('dept_nom')
        if code and nom:
            try:
                dept, created = Departement.objects.get_or_create(
                    code=code.upper(), defaults={'nom': nom}
                )
                if created:
                    messages.success(request, f"Le département '{nom}' a été créé.")
                else:
                    messages.warning(request, f"Le département avec le code '{code}' existe déjà.")
            except Exception as e:
                messages.error(request, f"Erreur création département: {e}")
    return redirect(reverse('admin_dashboard') + '#departement-tab')


@user_passes_test(est_admin)
def creer_cours_view(request):
    return redirect('cours_list')


# --- Vues de Gestion (CRUD) ---
@user_passes_test(est_admin)
def cours_list_view(request):
    cours_list = Cours.objects.all().select_related('enseignant__id')
    return render(request, 'presence/cours/cours_list.html', {'cours_list': cours_list})


@user_passes_test(est_admin)
def cours_create_view(request):
    if request.method == 'POST':
        form = CoursForm(request.POST)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.cree_par = request.user.administrateur
            cours.save()
            form.save_m2m()
            messages.success(request, f"Le cours '{cours.nom}' a été créé.")
            return redirect('cours_list')
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger.")
    else:
        form = CoursForm()
    return render(request, 'presence/cours/cours_form.html', {'form': form})


@user_passes_test(est_admin)
def cours_update_view(request, pk):
    cours = get_object_or_404(Cours, pk=pk)
    if request.method == 'POST':
        form = CoursForm(request.POST, instance=cours)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le cours '{cours.nom}' a été mis à jour.")
            return redirect('cours_list')
    else:
        form = CoursForm(instance=cours)
    return render(request, 'presence/cours/cours_form.html', {'form': form})


@user_passes_test(est_admin)
def cours_delete_view(request, pk):
    cours = get_object_or_404(Cours, pk=pk)
    if request.method == 'POST':
        nom_cours = cours.nom
        cours.delete()
        messages.success(request, f"Le cours '{nom_cours}' a été supprimé.")
        return redirect('cours_list')
    return render(request, 'presence/cours/cours_confirm_delete.html', {'cours': cours})


# --- CRUD Département ---
@user_passes_test(est_admin)
def departement_list_view(request):
    departements = Departement.objects.all()
    return render(request, 'presence/departement/departement_list.html', {'departements': departements})


@user_passes_test(est_admin)
def departement_create_view(request):
    if request.method == 'POST':
        form = DepartementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le département '{form.cleaned_data['nom']}' a été créé.")
            return redirect('departement_list')
    else:
        form = DepartementForm()
    return render(request, 'presence/departement/departement_form.html',
                  {'form': form, 'form_title': 'Créer un département'})


@user_passes_test(est_admin)
def departement_update_view(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    if request.method == 'POST':
        form = DepartementForm(request.POST, instance=departement)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le département '{departement.nom}' a été mis à jour.")
            return redirect('departement_list')
    else:
        form = DepartementForm(instance=departement)
    return render(request, 'presence/departement/departement_form.html',
                  {'form': form, 'form_title': f"Modifier le département : {departement.nom}"})


@user_passes_test(est_admin)
def departement_delete_view(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    if request.method == 'POST':
        nom_dept = departement.nom
        try:
            departement.delete()
            messages.success(request, f"Le département '{nom_dept}' a été supprimé.")
        except models.ProtectedError as e:
            messages.error(request,
                           f"Impossible de supprimer '{nom_dept}' car il est utilisé par des enseignants ou formations.")
        return redirect('departement_list')
    return render(request, 'presence/departement/departement_confirm_delete.html', {'departement': departement})


# --- CRUD Formation ---
@user_passes_test(est_admin)
def formation_list_view(request):
    formations = Formation.objects.all().select_related('departement')
    return render(request, 'presence/formation/formation_list.html', {'formations': formations})


@user_passes_test(est_admin)
def formation_create_view(request):
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"La formation '{form.cleaned_data['nom']}' a été créé.")
            return redirect('formation_list')
    else:
        form = FormationForm()
    context = {
        'form': form,
        'form_title': 'Créer une formation',
        'niveaux_licence': Formation.NIVEAU_CHOICES_LICENCE,
        'niveaux_master': Formation.NIVEAU_CHOICES_MASTER,
    }
    return render(request, 'presence/formation/formation_form.html', context)


@user_passes_test(est_admin)
def formation_update_view(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(request, f"La formation '{formation.nom}' a été mise à jour.")
            return redirect('formation_list')
    else:
        form = FormationForm(instance=formation)
    context = {
        'form': form,
        'form_title': f"Modifier la formation : {formation.nom}",
        'niveaux_licence': Formation.NIVEAU_CHOICES_LICENCE,
        'niveaux_master': Formation.NIVEAU_CHOICES_MASTER,
    }
    return render(request, 'presence/formation/formation_form.html', context)


@user_passes_test(est_admin)
def formation_delete_view(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if request.method == 'POST':
        nom_formation = formation.nom
        formation.delete()
        messages.success(request, f"La formation '{nom_formation}' a été supprimée.")
        return redirect('formation_list')
    return render(request, 'presence/formation/formation_confirm_delete.html', {'formation': formation})


# --- CRUD Enseignant ---
@user_passes_test(est_admin)
def enseignant_list_view(request):
    enseignants = Enseignant.objects.all().select_related('id', 'departement')
    return render(request, 'presence/Enseignant/Enseignant_list.html', {'enseignants': enseignants})


@user_passes_test(est_admin)
@transaction.atomic
def enseignant_create_view(request):
    if request.method == 'POST':
        form = EnseignantCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = Utilisateur.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password'],
                    nom=data['nom'],
                    prenom=data['prenom'],
                    role=Utilisateur.Role.ENSEIGNANT
                )
                Enseignant.objects.create(
                    id=user,
                    sexe=data.get('sexe'),
                    departement=data['departement']
                )
                messages.success(request, f"L'enseignant {data['prenom']} {data['nom']} a été créé.")
                return redirect('enseignant_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {e}")
    else:
        form = EnseignantCreationForm()
    return render(request, 'presence/Enseignant/Enseignant_form.html',
                  {'form': form, 'form_title': 'Créer un enseignant'})


@user_passes_test(est_admin)
@transaction.atomic
def enseignant_update_view(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ENSEIGNANT)
    enseignant = get_object_or_404(Enseignant, id=user)

    if request.method == 'POST':
        form = EnseignantUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user.nom = data['nom']
                user.prenom = data['prenom']
                user.email = data['email']
                user.username = data['email']
                user.save()
                enseignant.sexe = data.get('sexe')
                enseignant.departement = data['departement']
                enseignant.save()
                messages.success(request, f"Le profil de {user.prenom} {user.nom} a été mis à jour.")
                return redirect('enseignant_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la mise à jour : {e}")
    else:
        initial_data = {
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'sexe': enseignant.sexe,
            'departement': enseignant.departement
        }
        form = EnseignantUpdateForm(initial=initial_data)

    return render(request, 'presence/Enseignant/Enseignant_form.html',
                  {'form': form, 'form_title': f"Modifier l'enseignant : {user.prenom} {user.nom}"})


@user_passes_test(est_admin)
def enseignant_delete_view(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ENSEIGNANT)
    if request.method == 'POST':
        nom_complet = f"{user.prenom} {user.nom}"
        user.delete()
        messages.success(request, f"L'enseignant '{nom_complet}' a été supprimé.")
        return redirect('enseignant_list')
    return render(request, 'presence/Enseignant/Enseignant_confirm_delete.html', {'enseignant': user})


# --- CRUD Étudiant ---
@user_passes_test(est_admin)
def etudiant_list_view(request):
    etudiants = Etudiant.objects.all().select_related('id', 'formation')
    return render(request, 'presence/Etudiant/etudiant_list.html', {'etudiants': etudiants})


@user_passes_test(est_admin)
@transaction.atomic
def etudiant_create_view(request):
    if request.method == 'POST':
        form = EtudiantCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user = Utilisateur.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password'],
                    nom=data['nom'],
                    prenom=data['prenom'],
                    role=Utilisateur.Role.ETUDIANT
                )
                etudiant = Etudiant.objects.create(
                    id=user,
                    formation=data.get('formation')
                )
                cours_selectionnes = data.get('cours')
                if cours_selectionnes:
                    etudiant.cours_inscrits.set(cours_selectionnes)

                messages.success(request, f"L'étudiant {data['prenom']} {data['nom']} a été créé.")
                return redirect('etudiant_list')

            except IntegrityError as e:
                error_message = str(e).lower()
                if 'email' in error_message or 'unique' in error_message:
                    form.add_error('email', 'Cette adresse email est déjà utilisée.')
                else:
                    form.add_error(None, f"Erreur de base de données : {e}")

            except Exception as e:
                form.add_error(None, f"Erreur lors de la création : {e}")
        else:
            messages.error(request, "Le formulaire contient des erreurs.")

    else:
        form = EtudiantCreationForm()

    context = {
        'form': form,
        'form_title': 'Créer un étudiant',
        'niveaux_licence': Formation.NIVEAU_CHOICES_LICENCE,
        'niveaux_master': Formation.NIVEAU_CHOICES_MASTER,
    }

    return render(request, 'presence/Etudiant/etudiant_form.html', context)


@user_passes_test(est_admin)
@transaction.atomic
def etudiant_update_view(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ETUDIANT)
    etudiant = get_object_or_404(Etudiant, id=user)

    if request.method == 'POST':
        form = EtudiantUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                user.nom = data['nom']
                user.prenom = data['prenom']
                user.email = data['email']
                user.username = data['email']
                user.save()

                etudiant.formation = data.get('formation')
                etudiant.save()

                cours_selectionnes = data.get('cours')
                if cours_selectionnes is not None:
                    etudiant.cours_inscrits.set(cours_selectionnes)

                messages.success(request, f"Le profil de {user.prenom} {user.nom} a été mis à jour.")
                return redirect('etudiant_list')
            except Exception as e:
                messages.error(request, f"Erreur : {e}")

    else:
        initial_data = {
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'formation': etudiant.formation,
            'cours': etudiant.cours_inscrits.all()
        }

        if etudiant.formation:
            initial_data['type_formation'] = etudiant.formation.type_formation
            initial_data['niveau'] = etudiant.formation.niveau
            initial_data['departement'] = etudiant.formation.departement

        form = EtudiantUpdateForm(initial=initial_data)

    context = {
        'form': form,
        'form_title': f"Modifier l'étudiant : {user.prenom} {user.nom}",
        'niveaux_licence': Formation.NIVEAU_CHOICES_LICENCE,
        'niveaux_master': Formation.NIVEAU_CHOICES_MASTER,
    }
    return render(request, 'presence/Etudiant/etudiant_form.html', context)


@user_passes_test(est_admin)
def etudiant_delete_view(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk, role=Utilisateur.Role.ETUDIANT)
    if request.method == 'POST':
        nom_complet = f"{user.prenom} {user.nom}"
        user.delete()
        messages.success(request, f"L'étudiant '{nom_complet}' a été supprimé.")
        return redirect('etudiant_list')
    return render(request, 'presence/Etudiant/etudiant_confirm_delete.html', {'etudiant': user})


# =======================================================
# ==== VUES API (ADAPTÉES POUR SWAGGER) ====
# =======================================================

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('type_formation', openapi.IN_QUERY, description="Type (licence/master)",
                          type=openapi.TYPE_STRING),
    ],
    responses={200: "Liste des niveaux"}
)
@api_view(['GET'])
def api_get_niveaux(request):
    """
    Renvoie la liste des niveaux (S1, S2...) en fonction d'un type (licence/master).
    """
    # DRF utilise request.query_params mais request.GET fonctionne toujours
    type_form = request.GET.get('type_formation')
    niveaux = []
    if type_form == 'licence':
        niveaux = Formation.NIVEAU_CHOICES_LICENCE
    elif type_form == 'master':
        niveaux = Formation.NIVEAU_CHOICES_MASTER

    data = [{'id': k, 'name': v} for k, v in niveaux]
    return JsonResponse({'niveaux': data})


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('type_formation', openapi.IN_QUERY, description="Filtre par type", type=openapi.TYPE_STRING),
        openapi.Parameter('niveau', openapi.IN_QUERY, description="Filtre par niveau", type=openapi.TYPE_STRING),
        openapi.Parameter('departement', openapi.IN_QUERY, description="ID du département", type=openapi.TYPE_STRING),
    ],
    responses={200: "Liste des formations filtrées"}
)
@api_view(['GET'])
def api_get_formations(request):
    """
    Renvoie une liste de formations filtrée selon le type, niveau et département.
    """
    formations = Formation.objects.all()

    type_form = request.GET.get('type_formation')
    niveau = request.GET.get('niveau')
    dept_id = request.GET.get('departement')

    if type_form:
        formations = formations.filter(type_formation=type_form)
    if niveau:
        formations = formations.filter(niveau=niveau)
    if dept_id:
        formations = formations.filter(departement_id=dept_id)

    data = [{
        'id': f.id,
        'name': str(f)
    } for f in formations]

    return JsonResponse({'formations': data})


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('type_formation', openapi.IN_QUERY, description="Filtre par type", type=openapi.TYPE_STRING),
        openapi.Parameter('niveau', openapi.IN_QUERY, description="Filtre par niveau", type=openapi.TYPE_STRING),
        openapi.Parameter('departement', openapi.IN_QUERY, description="ID du département", type=openapi.TYPE_STRING),
    ],
    responses={200: "Liste des étudiants filtrés"}
)
@api_view(['GET'])
@permission_classes([IsAdmin | IsEnseignant]) # Security: Students must not see other students list
def api_get_etudiants_par_formation(request):
    """
    Renvoie les étudiants filtrés par Type, Niveau et Département.
    Restricted to Admins and Teachers.
    """
    type_form = request.GET.get('type_formation')
    niveau = request.GET.get('niveau')
    dept_id = request.GET.get('departement')

    etudiants = Etudiant.objects.all()

    if type_form:
        etudiants = etudiants.filter(formation__type_formation=type_form)
    if niveau:
        etudiants = etudiants.filter(formation__niveau=niveau)
    if dept_id:
        etudiants = etudiants.filter(formation__departement_id=dept_id)

    data = [{
        'id': e.id.id,
        'nom': f"{e.id.nom} {e.id.prenom} ({e.formation.nom if e.formation else 'Sans formation'})"
    } for e in etudiants]

    return JsonResponse({'etudiants': data})


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('niveau', openapi.IN_QUERY, description="Filtre par niveau (S1, M1...)",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('departement', openapi.IN_QUERY, description="ID du département", type=openapi.TYPE_STRING),
    ],
    responses={200: "Liste des cours filtrés"}
)
@api_view(['GET'])
def api_get_cours_par_filtres(request):
    """
    Renvoie la liste des cours selon le Niveau et le Département.
    """
    niveau = request.GET.get('niveau')
    dept_id = request.GET.get('departement')

    cours_qs = Cours.objects.all()

    if niveau:
        cours_qs = cours_qs.filter(semestre_cible=niveau)
    if dept_id:
        cours_qs = cours_qs.filter(enseignant__departement_id=dept_id)

    data = [{
        'id': c.id,
        'nom': f"{c.code} - {c.nom} ({c.enseignant.id.nom})"
    } for c in cours_qs]

    return JsonResponse({'cours': data})


@user_passes_test(est_enseignant)
def arreter_session(request, session_id):
    profil_enseignant = request.user.enseignant
    session = get_object_or_404(SessionCours, id=session_id, enseignant=profil_enseignant)

    if session.actif:
        session.actif = False
        session.date_fin = timezone.now()
        session.save()
        messages.success(request, "La session a été clôturée avec succès.")

    return redirect('dashboard_enseignant')


@user_passes_test(est_enseignant)
def cours_statistiques(request, cours_id):
    profil_enseignant = request.user.enseignant
    cours = get_object_or_404(Cours, id=cours_id, enseignant=profil_enseignant)

    sessions = SessionCours.objects.filter(cours=cours).order_by('-date_debut')
    total_sessions = sessions.count()
    etudiants = cours.etudiants.all()

    data_etudiants = []
    for etudiant in etudiants:
        presences_count = Presence.objects.filter(
            etudiant=etudiant,
            session__cours=cours
        ).count()

        taux = 0
        if total_sessions > 0:
            taux = round((presences_count / total_sessions) * 100, 1)

        data_etudiants.append({
            'etudiant': etudiant,
            'presences': presences_count,
            'taux': taux
        })

    graph_dates = []
    graph_counts = []

    for sess in sessions.reverse():
        count = Presence.objects.filter(session=sess).count()
        graph_dates.append(sess.date_debut.strftime("%d/%m"))
        graph_counts.append(count)

    context = {
        'cours': cours,
        'sessions': sessions,
        'etudiants_stats': data_etudiants,
        'total_sessions': total_sessions,
        'graph_dates': graph_dates,
        'graph_counts': graph_counts,
    }
    return render(request, 'presence/cours_statistiques.html', context)


@user_passes_test(est_enseignant)
def session_pdf_view(request, session_id):
    profil_enseignant = request.user.enseignant
    session = get_object_or_404(SessionCours, id=session_id, enseignant=profil_enseignant)

    etudiants_inscrits = session.cours.etudiants.all().select_related('id').order_by('id__nom')
    ids_presents = Presence.objects.filter(session=session).values_list('etudiant_id', flat=True)

    liste_etudiants = []
    present_count = 0

    for etu in etudiants_inscrits:
        est_present = etu.id.id in ids_presents
        if est_present:
            present_count += 1

        liste_etudiants.append({
            'nom': etu.id.nom,
            'prenom': etu.id.prenom,
            'statut': 'PRÉSENT' if est_present else 'ABSENT',
            'color': '#198754' if est_present else '#dc3545'
        })

    context = {
        'session': session,
        'liste_etudiants': liste_etudiants,
        'total_inscrits': etudiants_inscrits.count(),
        'total_presents': present_count,
        'enseignant': profil_enseignant
    }

    template_path = 'presence/pdf/session_report.html'
    response = HttpResponse(content_type='application/pdf')
    filename = f"Presence_{session.cours.nom}_{session.date_debut.strftime('%d-%m-%Y')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF <pre>' + html + '</pre>')

    return response

class DepartementViewSet(viewsets.ModelViewSet):
    """ API Admin : Gérer les départements """
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer
    permission_classes = [IsAdmin] # Security: Only Admins can modify departments

class FormationViewSet(viewsets.ModelViewSet):
    """ API Admin : Gérer les formations """
    queryset = Formation.objects.all()
    serializer_class = FormationSerializer
    permission_classes = [IsAdmin] # Security: Only Admins can modify formations

class EnseignantViewSet(viewsets.ModelViewSet):
    """ API Admin : Gérer les enseignants """
    queryset = Enseignant.objects.all()
    serializer_class = EnseignantSerializer
    permission_classes = [IsAdmin] # Security: Only Admins can manage teachers

class EtudiantViewSet(viewsets.ModelViewSet):
    """ API Admin : Gérer les étudiants """
    queryset = Etudiant.objects.all()
    serializer_class = EtudiantSerializer
    permission_classes = [IsAdmin] # Security: Only Admins can manage students

class CoursViewSet(viewsets.ModelViewSet):
    """ API Admin/Enseignant : Gérer les cours """
    queryset = Cours.objects.all()
    serializer_class = CoursSerializer
    permission_classes = [IsAdmin] # Security: Admins manage course structure

class SessionCoursViewSet(viewsets.ModelViewSet):
    """ API Enseignant : Gérer les sessions """
    queryset = SessionCours.objects.all()
    serializer_class = SessionCoursSerializer
    permission_classes = [IsAdmin] # Security: Legacy API, Admins only. Teachers use custom endpoints.

class PresenceViewSet(viewsets.ModelViewSet):
    """ API : Voir les présences """
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializer
    permission_classes = [IsAdmin] # Security: Admins only. Real-time presence is handled via custom endpoints.