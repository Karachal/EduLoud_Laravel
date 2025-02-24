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

        // Clear previous error messages
        jQuery("#errorMessage").addClass("d-none");
        jQuery("#speakerForm input").removeClass("is-invalid");

        // Validate required fields
        var isValid = true;
        jQuery('#speakerForm input[required]').each(function () {
            if (!jQuery(this).val()) {
                isValid = false;
                jQuery(this).addClass('is-invalid');
            }
        });

        if (!isValid) {
            jQuery("#errorMessage").removeClass("d-none").text("Please fill all required fields.");
            return;
        }

        // Prepare form data
        var formData = {};
        jQuery("#speakerForm").serializeArray().forEach(function (item) {
            formData[item.name] = isNaN(item.value) ? item.value : parseFloat(item.value);
        });

        // Include additional fields based on the scenario selection
        var scenario = formData.scenario;
        if (scenario === "sealed" || scenario === "ported") {
            formData.Vb = parseFloat(jQuery("#Vb").val()) || null;
        }
        if (scenario === "ported") {
            formData.port_length = parseFloat(jQuery("#port_length").val()) || null;
            formData.port_diameter = parseFloat(jQuery("#port_diameter").val()) || null;
        }

        console.log("Form Data:", formData);

        // Save user inputs to localStorage
        saveSuggestions(formData);

        // Show loading state
        jQuery("#toggleFormBtn").prop("disabled", true).text("Calculating...");

        // Send AJAX request
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
                    updateChart(response.frequencies, response.spl, scenario); // Update chart with the selected scenario
                }
            },
            error: function (xhr) {
                var errorMessage = "An error occurred. Please try again.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                }
                jQuery("#errorMessage").removeClass("d-none").text(errorMessage);
            },
            complete: function () {
                jQuery("#toggleFormBtn").prop("disabled", false).text("Hide Form");
            }
        });
    });

    // Function to update or create the chart
    function updateChart(frequencies, splData, scenario) {
        console.log("Updating Chart with Data:", frequencies, splData, scenario);

        // Deep copy the splData to avoid shared references
        splData = JSON.parse(JSON.stringify(splData));

        // Check if the data is valid
        if (!Array.isArray(frequencies) || !splData || !splData[scenario]) {
            console.error("Invalid data received for chart update.");
            return;
        }

        var ctx = document.getElementById("responseChart").getContext("2d");

        // Convert frequencies and SPL into paired data points
        var dataPoints = frequencies.map((f, i) => ({ x: f, y: splData[scenario][i] }));

        // If the chart doesn't exist, create it
        if (!responseChart) {
            responseChart = new Chart(ctx, {
                type: "line",
                data: {
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: "logarithmic",
                            position: "bottom",
                            title: { display: true, text: "Frequency (Hz)" },
                            min: 20, // Start at 20 Hz
                            max: 20000, // End at 20000 Hz
                            ticks: {
                                callback: function (value) {
                                    return Number(value).toFixed(0); // Show values in integer format
                                }
                            }
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
                        legend: { display: true } // Show legend to differentiate datasets
                    }
                }
            });
        }

        // Check if the dataset for the current scenario already exists
        var datasetIndex = responseChart.data.datasets.findIndex(dataset => dataset.label === scenario.replace("_", " "));

        if (datasetIndex === -1) {
            // Add a new dataset for the scenario
            responseChart.data.datasets.push({
                label: scenario.replace("_", " "), // Format scenario name
                data: dataPoints, // Use paired data points
                borderColor: scenario === "open_air" ? "blue" : scenario === "sealed" ? "green" : "red",
                borderWidth: 1,
                pointRadius: 1,
                fill: false,
                tension: 0.4
            });
        } else {
            // Update the existing dataset
            responseChart.data.datasets[datasetIndex].data = dataPoints;
        }

        // Update the chart
        responseChart.update();
    }

    // Save user inputs to localStorage
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

    // Restore suggestions from localStorage
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

    // Show or hide extra fields based on scenario
    jQuery("#scenario").on("change", function () {
        var scenario = jQuery(this).val();
        if (scenario === "sealed") {
            jQuery("#Vb-container").show();
            jQuery("#port-length-container, #port-diameter-container").hide();
        } else if (scenario === "ported") {
            jQuery("#Vb-container, #port-length-container, #port-diameter-container").show();
        } else {
            jQuery("#Vb-container, #port-length-container, #port-diameter-container").hide();
        }
    }).trigger("change");

    // Clear all datasets from the chart
    jQuery('#clearChartBtn').on('click', function () {
        if (responseChart) {
            responseChart.data.datasets = []; // Clear all datasets
            responseChart.update(); // Update the chart
        }
    });
});