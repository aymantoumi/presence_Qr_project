# presence/serializers.py
from rest_framework import serializers
from comptes.models import Utilisateur, Departement, Formation, Enseignant, Etudiant
from presence.models import Cours, SessionCours, Presence




class DepartementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departement
        fields = '__all__'


class FormationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = '__all__'


class EnseignantSerializer(serializers.ModelSerializer):

    nom_complet = serializers.SerializerMethodField()

    class Meta:
        model = Enseignant
        fields = '__all__'

    def get_nom_complet(self, obj):
        return f"{obj.id.nom} {obj.id.prenom}"


class EtudiantSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField()

    class Meta:
        model = Etudiant
        fields = '__all__'

    def get_nom_complet(self, obj):
        return f"{obj.id.nom} {obj.id.prenom}"




class CoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cours
        fields = '__all__'


class SessionCoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionCours
        fields = '__all__'


class PresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = '__all__'