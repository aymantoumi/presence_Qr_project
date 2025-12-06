// static/js/scanner.js

document.addEventListener("DOMContentLoaded", function() {
    const readerElement = document.getElementById("reader");
    if (!readerElement) {
        console.error("❌ Élément #reader introuvable");
        return;
    }

    // ===== CORRECTION PRINCIPALE =====
    // Récupération de l'URL depuis l'input caché au lieu de dataset
    const validateUrlInput = document.getElementById("validate-url");
    if (!validateUrlInput) {
        console.error("❌ Élément #validate-url introuvable");
        alert("ERREUR: Configuration manquante. L'élément #validate-url est introuvable.");
        return;
    }

    const validateUrl = validateUrlInput.value;
    console.log("✅ URL de validation chargée:", validateUrl);

    // Vérification que l'URL n'est pas vide ou undefined
    if (!validateUrl || validateUrl === 'undefined' || validateUrl.trim() === '') {
        console.error("❌ URL de validation invalide:", validateUrl);
        alert("ERREUR: URL de validation invalide. Vérifiez votre configuration Django.");
        return;
    }

    const resultContainer = document.getElementById("scan-result");
    let isScanning = true;
    let html5QrcodeScanner;

    // Fonction pour récupérer le jeton CSRF depuis le cookie
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    async function onScanSuccess(decodedText, decodedResult) {
        if (!isScanning) {
            console.log("⏸️ Scan ignoré (déjà en cours)");
            return;
        }

        isScanning = false;
        console.log("📷 QR Code scanné:", decodedText);

        // Pause de la caméra
        html5QrcodeScanner.pause();

        const userConfirmed = window.confirm("QR Code détecté. Voulez-vous valider cette présence ?");

        if (!userConfirmed) {
            console.log("❌ Validation annulée par l'utilisateur");
            resultContainer.innerHTML = `<div class="alert alert-warning">Validation annulée.</div>`;
            isScanning = true;
            html5QrcodeScanner.resume();
            return;
        }

        resultContainer.innerHTML = `<div class="alert alert-info">Validation en cours...</div>`;

        const formData = new FormData();
        formData.append('jeton', decodedText);

        try {
            const csrfToken = getCsrfToken();

            if (!csrfToken) {
                throw new Error('Jeton CSRF introuvable dans les cookies');
            }

            console.log("📤 Envoi de la requête vers:", validateUrl);
            console.log("🔑 CSRF Token:", csrfToken.substring(0, 10) + "...");

            const response = await fetch(validateUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
                credentials: 'same-origin'
            });

            console.log("📥 Statut de la réponse:", response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error("❌ Erreur serveur:", errorText);
                throw new Error(`Réponse du serveur non OK: ${response.status}`);
            }

            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const responseText = await response.text();
                console.error("❌ Réponse non-JSON reçue:", responseText.substring(0, 200));
                throw new Error("Le serveur n'a pas renvoyé du JSON");
            }

            const data = await response.json();
            console.log("✅ Données reçues:", data);

            if (data.success) {
                alert(`✅ Vous avez marqué la présence pour le cours: ${data.cours_nom}`);
                resultContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;

                // Arrêt définitif du scanner
                html5QrcodeScanner.clear().catch(err => console.error("Erreur à l'arrêt du scanner:", err));
                document.getElementById('reader').style.display = 'none';

                // Recharger la page après 2 secondes pour voir l'historique mis à jour
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                console.warn("⚠️ Échec de validation:", data.message);
                resultContainer.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                isScanning = true;
                html5QrcodeScanner.resume();
            }

        } catch (error) {
            console.error("❌ ERREUR lors de la validation:", error);
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Erreur de connexion avec le serveur.</strong><br>
                    ${error.message}<br>
                    <small>Consultez la console pour plus de détails (F12)</small>
                </div>
            `;
            isScanning = true;
            html5QrcodeScanner.resume();
        }
    }

    function onScanFailure(error) {
        // Silencieux - ne pas polluer la console avec les échecs de scan
    }

    console.log("🎥 Initialisation du scanner QR...");

    html5QrcodeScanner = new Html5QrcodeScanner(
        "reader",
        { fps: 10, qrbox: { width: 250, height: 250 } },
        false
    );

    html5QrcodeScanner.render(onScanSuccess, onScanFailure);

    console.log("✅ Scanner QR initialisé et prêt");
});