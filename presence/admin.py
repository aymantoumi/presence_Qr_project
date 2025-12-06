from django.contrib import admin
from .models import Cours, SessionCours, Presence


class CoursAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'enseignant', 'semestre_cible', 'cree_par')
    list_filter = ('semestre_cible', 'enseignant')
    search_fields = ('nom', 'code')

    # Interface pour lier les étudiants au cours (votre demande)
    filter_horizontal = ('etudiants',)

    # Pour que le champ 'cree_par' se remplisse automatiquement
    def save_model(self, request, obj, form, change):
        # Assumons que l'admin connecté est lié à un objet Administrateur
        if not obj.cree_par_id:  # Si non défini
            try:
                obj.cree_par = request.user.administrateur
            except:
                # Gérer le cas où l'utilisateur n'est pas un admin
                pass
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        # Pour que l'admin ne voie que les enseignants
        form = super(CoursAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['enseignant'].queryset = form.base_fields['enseignant'].queryset.select_related('id')
        return form


class PresenceAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'session', 'horodatage_scan', 'valide')
    list_filter = ('session__cours', 'valide')


admin.site.register(Cours, CoursAdmin)
admin.site.register(SessionCours)
admin.site.register(Presence, PresenceAdmin)