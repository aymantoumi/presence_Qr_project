📱 Système de Gestion de Présence par QR Code

Application Django permettant la gestion des présences étudiantes via des QR Codes dynamiques générés par les enseignants.

📋 Prérequis

Python 3.10+

Git

🚀 Installation (Premier lancement)

Si vous venez de cloner le projet, suivez ces étapes pour configurer votre environnement.

1. Cloner le projet et installer les dépendances
# Cloner le projet
git clone <votre-lien-github>
cd presence_projet

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Windows :
.venv\Scripts\activate
# Linux/Mac :
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt


💡 Si le fichier requirements.txt n’existe pas :
pip freeze > requirements.txt

2. Initialiser la Base de Données

La base n’est pas incluse dans le dépôt Git, il faut créer les tables :

python manage.py migrate

3. Créer le Super Administrateur (IMPORTANT)

C’est le premier utilisateur, celui qui aura tous les droits.

python manage.py createsuperuser


Entrez un email (ex : admin@gmail.com
)

Entrez un mot de passe

Validez

4. Lancer le serveur
python manage.py runserver

🛠️ Guide d’Utilisation

Voici le workflow complet pour configurer et utiliser l’application.

🔑 Étape 1 : Connexion Super Admin

Ouvrez → http://127.0.0.1:8000/comptes/login/

Connectez-vous avec les identifiants du super administrateur

Vous serez redirigé vers le tableau de bord d’administration

🧱 Étape 2 : Créer la structure (ordre obligatoire)

Dans le menu Gestion (barre jaune), créez les éléments suivants dans cet ordre :

Départements
Exemple : Informatique

Formations
Liées à un département
Exemple : Licence S1

Enseignants
Comptes reliés à un département

Étudiants
Assignez-les à une formation

Cours

Choisir un enseignant

Ajouter les étudiants concernés

👨‍🏫 Étape 3 : Utilisation par les Enseignants

Déconnectez-vous du Super Admin

Connectez-vous avec un compte enseignant

Le tableau de bord affiche ses cours

Cliquez sur un cours → Lancer une session (génération du QR Code)

🎓 Étape 4 : Utilisation par les Étudiants

Connectez-vous avec un compte étudiant

Cliquez sur Scanner

Scannez le QR Code affiché par l’enseignant
(ou test via l’API Swagger)

📚 Documentation API (Swagger)

Une API REST est disponible et entièrement documentée.

➡️ http://127.0.0.1:8000/swagger/

Vous pouvez y tester :

CRUD Étudiants

CRUD Enseignants

CRUD Cours

Sessions / QR Codes

etc.

⚠️ Dépannage (FAQ)
❌ Erreur : “Table 'presence_...' doesn't exist”

Vous avez oublié :

python manage.py migrate

🔐 Je ne peux plus me connecter après un git pull

La base de données est locale.
Si vous changez de PC ou supprimez la base → recréez un superuser :

python manage.py createsuperuser

🖼️ Les images ou CSS ne se chargent pas (404)

Vérifiez que le dossier static/ existe à la racine.