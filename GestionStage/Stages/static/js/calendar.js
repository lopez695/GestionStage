// static/js/calendar.js
document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let currentDate = new Date();
    let events = [];
    let currentEventId = null;
    
    // Récupérer les événements depuis le serveur
    function fetchEvents() {
        fetch('/calendrier/events/')
            .then(response => response.json())
            .then(data => {
                events = data;
                loadEvents();
            });
    }
    
    // Sauvegarder un événement
    function saveEvent(eventData) {
        const method = eventData.id ? 'PUT' : 'POST';
        const url = '/calendrier/events/' + (eventData.id ? `${eventData.id}/` : '');
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                fetchEvents(); // Rafraîchir les événements
            }
        });
    }
    
    // Supprimer un événement
    function deleteEvent(eventId) {
        fetch(`/calendrier/events/${eventId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                fetchEvents(); // Rafraîchir les événements
            }
        });
    }
    
    // Fonction utilitaire pour récupérer le cookie CSRF
    function getCookie(name) {
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
    
    // Initialisation
    fetchEvents();
    initCalendar();
    
    // [Le reste de votre code JavaScript existant...]
    // Adaptez simplement les fonctions saveEvent et deleteEvent pour utiliser
    // les nouvelles fonctions fetch que nous avons créées
});