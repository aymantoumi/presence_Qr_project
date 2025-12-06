// static/js/session_refresh.js

document.addEventListener("DOMContentLoaded", function() {
    const qrContainer = document.getElementById('qr-code-container');
    if (!qrContainer) return; // Quitte si on n'est pas sur la bonne page

    const refreshUrl = qrContainer.dataset.refreshUrl;
    const qrImage = document.getElementById('qr-code-image');
    const timerDisplay = document.getElementById('qr-timer');
    const spinner = document.getElementById('qr-spinner');

    // Intervalle de 10 minutes (en millisecondes)
    const REFRESH_INTERVAL = 600000;
    let timerDuration = 600; // 10 minutes en secondes pour l'affichage

    // --- 1. Fonction de rafraîchissement du QR Code ---
    async function refreshQRCode() {
        console.log("Rafraîchissement du QR code...");
        if(timerDisplay) timerDisplay.style.display = 'none';
        if(spinner) spinner.style.display = 'inline-block';

        try {
            const response = await fetch(refreshUrl, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });

            if (!response.ok) throw new Error(`Erreur réseau: ${response.statusText}`);

            const data = await response.json();

            if (data.qr_image_base64) {
                qrImage.src = 'data:image/png;base64,' + data.qr_image_base64;
                console.log("QR Code rafraîchi !");
                timerDuration = 600; // Réinitialiser le minuteur
            } else if (data.error) {
                console.error(data.error);
                if(timerDisplay) timerDisplay.textContent = data.error;
                clearInterval(refreshInterval); // Arrête le rafraîchissement
                clearInterval(timerInterval);
            }
        } catch (error) {
            console.error("Erreur lors du rafraîchissement:", error);
            if(timerDisplay) timerDisplay.textContent = "Erreur de connexion.";
        } finally {
            if(spinner) spinner.style.display = 'none';
            if(timerDisplay) timerDisplay.style.display = 'inline';
        }
    }

    // --- 2. Minuteur visuel (Bonus) ---
    function updateTimerDisplay() {
        timerDuration--;
        if (timerDuration < 0) timerDuration = 0;

        let minutes = parseInt(timerDuration / 60, 10);
        let seconds = parseInt(timerDuration % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        if(timerDisplay) timerDisplay.textContent = "Prochain rafraîchissement dans " + minutes + ":" + seconds;
    }

    // --- 3. Lancement ---
    const timerInterval = setInterval(updateTimerDisplay, 1000);
    const refreshInterval = setInterval(refreshQRCode, REFRESH_INTERVAL);
});