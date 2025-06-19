document.addEventListener('DOMContentLoaded', function() {
    const calendarApiUrl = '/calendrier/evenements/';
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Initialisation du calendrier
    function initCalendar() {
        // Ici vous intégrerez le code JavaScript du calendrier
        // en utilisant les endpoints API que nous avons créés
        
        // Exemple de requête pour charger les événements
        fetch(calendarApiUrl, {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(events => {
            // Traitez les événements reçus du serveur
            console.log('Événements chargés:', events);
        });
    }
    
    // Gestion des formulaires
    document.getElementById('saveEvent').addEventListener('click', function() {
        const formData = {
            title: document.getElementById('eventTitle').value,
            start: document.getElementById('eventStart').value,
            end: document.getElementById('eventEnd').value,
            type: document.getElementById('eventType').value,
            description: document.getElementById('eventDescription').value
        };
        
        fetch(calendarApiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Recharger le calendrier
                initCalendar();
            }
        });
    });
    
    // Initialisation
    initCalendar();
});