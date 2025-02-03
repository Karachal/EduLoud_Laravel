jQuery(document).ready(function () {
    var responseChart; // Declare chart globally

    restoreSuggestions();

    // Toggle form visibility
    jQuery('#toggleFormBtn').on('click', function () {
        jQuery('#speakerFormContainer').toggle();
        var isVisible = jQuery('#speakerFormContainer').is(':visible');
        jQuery('#toggleFormBtn').text(isVisible ? 'Hide Form' : 'Show Form');
    });

    // Handle form submission
    jQuery('#speakerForm').on('submit', function (event) {
        event.preventDefault();
        console.log("Submitting form...");

        var formData = {};
        jQuery("#speakerForm").serializeArray().forEach(function (item) {
            formData[item.name] = isNaN(item.value) ? item.value : parseFloat(item.value);
        });

        console.log("Form Data:", formData);

        // Save user inputs to localStorage
        saveSuggestions(formData);

        var csrfToken = jQuery('meta[name="csrf-token"]').attr('content');

        jQuery.ajax({
            url: "/calculate-speaker-response",
            type: "POST",
            data: JSON.stringify(formData),
            contentType: "application/json",
            headers: { "X-CSRF-TOKEN": csrfToken },
            success: function (response) {
                if (response.error) {
                    console.log("Server Response:", response);
                    jQuery("#errorMessage").removeClass("d-none").text(response.error);
                } else {
                    console.log("Server Response:", response);
                    updateChart(response.frequencies, response.spl);
                }
            },
            error: function (xhr) {
                jQuery("#errorMessage").removeClass("d-none").text("Error: " + xhr.responseText);
            }
        });
    });

    // Function to update or create the chart
    function updateChart(frequencies, splValues) {
        console.log("Updating Chart with Data:", frequencies, splValues);

        if (!Array.isArray(frequencies) || !Array.isArray(splValues) || frequencies.length === 0) {
            console.error("Invalid data received for chart update.");
            return;
        }

        var ctx = document.getElementById("responseChart").getContext("2d");

        // Destroy previous chart if exists
        if (responseChart) {
            responseChart.destroy();
        }

        responseChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: frequencies,
                datasets: [{
                    label: "SPL Response",
                    data: splValues,
                    borderColor: "blue",
                    borderWidth: 2,
                    pointRadius: 2,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: "logarithmic",
                        position: "bottom",
                        title: { display: true, text: "Frequency (Hz)" }
                    },
                    y: {
                        title: { display: true, text: "SPL (dB)" },
                        ticks: { beginAtZero: false }
                    }
                },
                elements: {
                    line: { borderJoinStyle: 'round' }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    function saveSuggestions(formData) {
        var savedSuggestions = JSON.parse(localStorage.getItem("speakerFormSuggestions")) || {};
        
        Object.keys(formData).forEach(function (key) {
            if (!savedSuggestions[key]) {
                savedSuggestions[key] = [];
            }
            if (!savedSuggestions[key].includes(formData[key])) {
                savedSuggestions[key].push(formData[key]);
            }
        });

        localStorage.setItem("speakerFormSuggestions", JSON.stringify(savedSuggestions));
    }

    function restoreSuggestions() {
        var savedSuggestions = JSON.parse(localStorage.getItem("speakerFormSuggestions")) || {};

        Object.keys(savedSuggestions).forEach(function (key) {
            var dataList = jQuery(`#${key}-suggestions`);
            if (dataList.length) {
                dataList.empty();
                savedSuggestions[key].forEach(function (value) {
                    dataList.append(`<option value="${value}">`);
                });
            }
        });

        console.log("Restored Suggestions:", savedSuggestions);
    }
});
