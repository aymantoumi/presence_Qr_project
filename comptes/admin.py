# comptes/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Departement, Administrateur, Enseignant, Etudiant, Formation
from django.utils.translation import gettext_lazy as _  # Nécessaire pour les traductions


class CustomUserAdmin(UserAdmin):
    model = Utilisateur

    # --- MODIFICATION ICI ---
    # On redéfinit les champs à afficher lors de la MODIFICATION
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        # On remplace 'first_name' et 'last_name' par 'nom' et 'prenom'
        (_("Personal info"), {"fields": ("nom", "prenom", "email")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        # On ajoute notre champ 'role'
        (_("Rôle"), {"fields": ("role",)}),
    )

    # On redéfinit aussi les champs pour la CRÉATION
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "nom", "prenom", "role", "password", "password2"),
        }),
    )
    # --- FIN DE LA MODIFICATION ---

    list_display = ('email', 'username', 'nom', 'prenom', 'role', 'is_staff')
    search_fields = ('email', 'nom', 'prenom')
    ordering = ('email',)


# Enregistrement des autres modèles
admin.site.register(Utilisateur, CustomUserAdmin)
admin.site.register(Departement)
admin.site.register(Administrateur)
admin.site.register(Enseignant)
admin.site.register(Etudiant)
admin.site.register(Formation)