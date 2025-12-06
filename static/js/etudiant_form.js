

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Script etudiant_form.js chargé');

    // Récupération des éléments du DOM
    const typeFormationSelect = document.getElementById('id_type_formation');
    const niveauSelect = document.getElementById('id_niveau');
    const departementSelect = document.getElementById('id_departement');
    const formationSelect = document.getElementById('id_formation');

    // Vérifier que tous les éléments existent
    if (!typeFormationSelect || !niveauSelect || !departementSelect || !formationSelect) {
        console.error('❌ Certains éléments du formulaire sont manquants');
        return;
    }

    console.log('✅ Tous les éléments du formulaire trouvés');

    /**
     * Met à jour la liste des niveaux en fonction du type de formation
     */
    function updateNiveaux() {
        const typeFormation = typeFormationSelect.value;
        console.log('📝 Mise à jour des niveaux pour type:', typeFormation);

        if (!typeFormation) {
            niveauSelect.innerHTML = '<option value="">----</option>';
            niveauSelect.disabled = true;
            updateFormations();
            return;
        }

        // Appel AJAX pour récupérer les niveaux
        fetch(`${window.DJANGO_DATA.urlNiveaux}?type_formation=${typeFormation}`)
            .then(response => response.json())
            .then(data => {
                console.log('✅ Niveaux reçus:', data.niveaux);

                // Vider et remplir la liste des niveaux
                niveauSelect.innerHTML = '<option value="">----</option>';

                data.niveaux.forEach(niveau => {
                    const option = document.createElement('option');
                    option.value = niveau.id;
                    option.textContent = niveau.name;
                    niveauSelect.appendChild(option);
                });

                niveauSelect.disabled = false;

                // Restaurer la valeur initiale si elle existe
                if (window.DJANGO_DATA.initialNiveau) {
                    niveauSelect.value = window.DJANGO_DATA.initialNiveau;
                }

                updateFormations();
            })
            .catch(error => {
                console.error('❌ Erreur lors du chargement des niveaux:', error);
                niveauSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                niveauSelect.disabled = true;
            });
    }

    /**
     * Met à jour la liste des formations en fonction des filtres
     */
    function updateFormations() {
        const typeFormation = typeFormationSelect.value;
        const niveau = niveauSelect.value;
        const departement = departementSelect.value;

        console.log('📝 Mise à jour des formations avec filtres:', {
            typeFormation,
            niveau,
            departement
        });

        // Construire l'URL avec les paramètres
        const params = new URLSearchParams();
        if (typeFormation) params.append('type_formation', typeFormation);
        if (niveau) params.append('niveau', niveau);
        if (departement) params.append('departement', departement);

        const url = `${window.DJANGO_DATA.urlFormations}?${params.toString()}`;

        // Appel AJAX pour récupérer les formations
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('✅ Formations reçues:', data.formations);

                // Vider et remplir la liste des formations
                formationSelect.innerHTML = '<option value="">-- Sélectionnez une formation --</option>';

                if (data.formations.length === 0) {
                    formationSelect.innerHTML = '<option value="">Aucune formation disponible</option>';
                    formationSelect.disabled = true;
                } else {
                    data.formations.forEach(formation => {
                        const option = document.createElement('option');
                        option.value = formation.id;
                        option.textContent = formation.name;
                        formationSelect.appendChild(option);
                    });

                    formationSelect.disabled = false;

                    // Restaurer la valeur initiale si elle existe
                    if (window.DJANGO_DATA.initialFormationId) {
                        formationSelect.value = window.DJANGO_DATA.initialFormationId;
                    }
                }
            })
            .catch(error => {
                console.error('❌ Erreur lors du chargement des formations:', error);
                formationSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                formationSelect.disabled = true;
            });
    }

    /**
     * Validation avant soumission du formulaire
     */
    function validateForm(event) {
        const email = document.getElementById('id_email').value;
        const password = document.getElementById('id_password');

        // Vérification de l'email
        if (!email || !email.includes('@')) {
            alert('Veuillez entrer une adresse email valide.');
            event.preventDefault();
            return false;
        }

        // Vérification du mot de passe (uniquement pour la création)
        if (password && password.value.length < 8) {
            alert('Le mot de passe doit contenir au moins 8 caractères.');
            event.preventDefault();
            return false;
        }

        console.log('✅ Validation du formulaire réussie');
        return true;
    }

    // Attacher les événements
    typeFormationSelect.addEventListener('change', updateNiveaux);
    niveauSelect.addEventListener('change', updateFormations);
    departementSelect.addEventListener('change', updateFormations);

    // Attacher la validation au formulaire
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', validateForm);
    }

    // Initialiser les listes au chargement de la page
    if (typeFormationSelect.value) {
        updateNiveaux();
    } else {
        // Charger toutes les formations si aucun filtre n'est actif
        updateFormations();
    }

    console.log('✅ Script initialisé avec succès');
});