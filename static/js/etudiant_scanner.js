// static/js/etudiant_scanner.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("Chargement du script de statistiques étudiant...");

    // 1. Récupération des éléments DOM
    const statsTitle = document.getElementById('stats-title');
    const statsContent = document.getElementById('stats-content');
    const courseSelect = document.getElementById('courseSelect');
    const btnReset = document.getElementById('btn-reset');

    // Sauvegarde du contenu par défaut (Historique global)
    let defaultContent = '';
    if (statsContent) {
        defaultContent = statsContent.innerHTML;
    }

    // Récupération des données passées par Django (via window.DJANGO_DATA)
    const coursData = window.DJANGO_DATA ? window.DJANGO_DATA.coursStats : {};

    /**
     * Fonction appelée quand on clique sur un cours
     * Attachée à 'window' pour être accessible via les onclick="" du HTML
     */
    window.selectCours = function(coursId) {
        // Conversion en string pour éviter les problèmes de type
        if (!coursId || coursId === "") {
            resetView();
            return;
        }

        const data = coursData[coursId];
        if (!data) {
            console.warn("Aucune donnée trouvée pour le cours ID:", coursId);
            return;
        }

        // Mettre à jour le selecteur (si clic depuis la liste de gauche)
        if (courseSelect) courseSelect.value = coursId;

        // Mettre à jour le titre et afficher le bouton reset
        if (statsTitle) statsTitle.innerHTML = `<span class="text-primary">${data.nom}</span>`;
        if (btnReset) btnReset.style.display = 'inline-block';

        // Calculer le pourcentage de présence
        let taux = 0;
        if (data.total > 0) {
            taux = Math.round((data.present / data.total) * 100);
        }

        let badgeClass = taux >= 50 ? 'bg-success' : 'bg-danger';

        // Générer le HTML des statistiques
        let html = `
            <div class="row text-center mb-3">
                <div class="col-4 border-end">
                    <div class="h4 mb-0 text-primary">${data.total}</div>
                    <small class="text-muted">Séances</small>
                </div>
                <div class="col-4 border-end">
                    <div class="h4 mb-0 text-success">${data.present}</div>
                    <small class="text-muted">Présences</small>
                </div>
                <div class="col-4">
                    <div class="h4 mb-0 text-danger">${data.absent}</div>
                    <small class="text-muted">Absences</small>
                </div>
            </div>
            
            <div class="progress mb-3" style="height: 10px;">
                <div class="progress-bar ${badgeClass}" role="progressbar" style="width: ${taux}%"></div>
            </div>
            <p class="text-center small text-muted">Taux de présence : <strong>${taux}%</strong></p>

            <h6 class="border-bottom pb-2 mt-3 mb-2">Historique du cours</h6>
            <div style="max-height: 200px; overflow-y: auto;">
                <ul class="list-group list-group-flush">
        `;

        if (data.historique.length === 0) {
            html += `<li class="list-group-item text-center small text-muted">Aucune séance passée.</li>`;
        } else {
            data.historique.forEach(seance => {
                html += `
                    <li class="list-group-item d-flex justify-content-between px-0 py-2">
                        <span>${seance.date} <small class="text-muted">(${seance.heure})</small></span>
                        <span class="badge bg-${seance.couleur}">${seance.statut}</span>
                    </li>
                `;
            });
        }

        html += `</ul></div>`;

        if (statsContent) statsContent.innerHTML = html;

        // Mettre en surbrillance l'élément de la liste à gauche
        document.querySelectorAll('.cours-item').forEach(el => el.classList.remove('active'));
        const activeItem = document.querySelector(`.cours-item[data-cours-id="${coursId}"]`);
        if(activeItem) activeItem.classList.add('active');
    };

    /**
     * Fonction pour remettre l'affichage par défaut
     */
    window.resetView = function() {
        if (statsTitle) statsTitle.innerHTML = '<i class="bi bi-bar-chart-fill me-2"></i>Historique Global';
        if (statsContent) statsContent.innerHTML = defaultContent;
        if (courseSelect) courseSelect.value = "";
        if (btnReset) btnReset.style.display = 'none';
        document.querySelectorAll('.cours-item').forEach(el => el.classList.remove('active'));
    };
});