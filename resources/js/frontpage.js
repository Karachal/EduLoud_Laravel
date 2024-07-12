// resources/js/frontpage.js

document.addEventListener('DOMContentLoaded', function () {
    // Example data (simulated local data)
    const speakersData = [
        { name: 'Speaker 1', bio: 'Bio for Speaker 1.' },
        { name: 'Speaker 2', bio: 'Bio for Speaker 2.' },
        { name: 'Speaker 3', bio: 'Bio for Speaker 3.' }
    ];

    // Example of handling a click event to load speakers
    document.getElementById('loadSpeakers').addEventListener('click', function (event) {
        event.preventDefault();
        
        // Example of fetching data asynchronously
        fetchSpeakers();
    });

    function fetchSpeakers() {
        // Simulate fetching data (in this case, it's already available locally)
        displaySpeakers(speakersData);
    }

    function displaySpeakers(data) {
        let speakersHTML = '';

        data.forEach(speaker => {
            speakersHTML += `<div>
                                <h2>${speaker.name}</h2>
                                <p>${speaker.bio}</p>
                             </div>`;
        });

        document.getElementById('content').innerHTML = speakersHTML;
    }
});
