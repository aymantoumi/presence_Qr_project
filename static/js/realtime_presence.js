// static/js/realtime_presence.js

document.addEventListener("DOMContentLoaded", function() {
    const presenceCard = document.querySelector('[data-presences-url]');
    if (!presenceCard) return; // Quitte si on n'est pas sur la bonne page

    const presencesUrl = presenceCard.dataset.presencesUrl;
    const listePresences = document.getElementById('liste-presences');
    const presenceCount = document.getElementById('presence-count');
    const noPresenceLi = document.getElementById('aucune-presence');

    // Intervalle de polling (toutes les 5 secondes)
    const POLLING_INTERVAL = 5000;

    async function updatePresenceList() {
        try {
            const response = await fetch(presencesUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) throw new Error('Erreur réseau');

            const data = await response.json();

            // Met à jour la liste
            renderList(data.presences);

        } catch (error) {
            console.error("Erreur lors de la mise à jour des présences:", error);
            if (noPresenceLi) {
                noPresenceLi.textContent = "Erreur de connexion...";
            }
        }
    }

    function renderList(presences) {
        // Vide la liste
        listePresences.innerHTML = '';

        // Met à jour le compteur
        presenceCount.textContent = presences.length;

        if (presences.length === 0) {
            // Remet le message "Aucun étudiant"
            if (noPresenceLi) {
                listePresences.appendChild(noPresenceLi);
            }
        } else {
            // Remplit la liste avec les nouveaux présents
            presences.forEach(p => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `${p.prenom} ${p.nom}
                              <span class="text-muted float-end">${p.heure}</span>`;
                listePresences.appendChild(li);
            });
        }
    }

    // Lancement du polling
    setInterval(updatePresenceList, POLLING_INTERVAL);
    // Lancement immédiat au chargement de la page
    updatePresenceList();
});

