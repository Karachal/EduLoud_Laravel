jQuery(document).ready(function () {
    var responseChart;   // For SPL vs freq(Hz)
    var impedanceChart;  // For Impedance vs (f/fs)

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

        // Additional fields
        var scenario = formData.scenario;
        if (scenario === "sealed" || scenario === "ported") {
            formData.Vb = parseFloat(jQuery("#Vb").val()) || null;
        }
        if (scenario === "ported") {
            formData.port_length = parseFloat(jQuery("#port_length").val()) || null;
            formData.port_diameter = parseFloat(jQuery("#port_diameter").val()) || null;
        }

        console.log("Form Data:", formData);

        // Save suggestions
        saveSuggestions(formData);

        // Show loading state
        jQuery("#toggleFormBtn").prop("disabled", true).text("Calculating...");

        // AJAX
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

                    // Update SPL chart
                    updateChart(response.frequencies, response.spl, scenario);

                    // If we also have "impedance", update the Impedance chart
                    if (response.impedance && response.f_over_fs && response.Re) {
                        updateImpedanceChart(response, scenario);
                    } else {
                        console.error("Missing impedance or f_over_fs data in response.");
                    }
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

    // SPL vs frequency(Hz)
    function updateChart(frequencies, splData, scenario) {
        console.log("Updating SPL Chart:", scenario);
        if (!Array.isArray(frequencies) || !splData || !splData[scenario]) {
            console.error("Invalid data for SPL chart update.");
            return;
        }
        var ctx = document.getElementById("responseChart").getContext("2d");
        var dataPoints = frequencies.map((f, i) => ({ x: f, y: splData[scenario][i] }));

        if (!responseChart) {
            responseChart = new Chart(ctx, {
                type: "line",
                data: { datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: "logarithmic",
                            position: "bottom",
                            title: { display: true, text: "Frequency (Hz)" },
                            min: 20,
                            max: 20000,
                            ticks: {
                                callback: function(value) {
                                    return Number(value).toFixed(0);
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
                        legend: { display: true }
                    }
                }
            });
        }

        var labelName = scenario.replace("_", " ");
        var dsIndex = responseChart.data.datasets.findIndex(ds => ds.label === labelName);

        if (dsIndex === -1) {
            responseChart.data.datasets.push({
                label: labelName,
                data: dataPoints,
                borderColor: scenario === "open_air" ? "blue"
                          : scenario === "sealed"  ? "green"
                          : "red",
                borderWidth: 1,
                pointRadius: 1,
                fill: false,
                tension: 0.4
            });
        } else {
            responseChart.data.datasets[dsIndex].data = dataPoints;
        }

        responseChart.update();
    }

    // Impedance vs (f/fs)
    function updateImpedanceChart(response, scenario) {
        console.log("Updating Impedance Chart:", scenario);

        // Extract normalized frequency (f/fs) and impedance data
        var scaledFreq = response.f_over_fs;  // array of f/fs
        var impData = response.impedance;     // { scenario: [Z array] }

        // Validate data
        if (!Array.isArray(scaledFreq) || !impData || !impData[scenario]) {
            console.error("Invalid data for Impedance chart update.");
            return;
        }

        // Normalize impedance to driver's DC resistance (Re)
        var normalizedImpedance = impData[scenario].map(z => z / response.Re);

        // Create data points for the chart
        var dataPoints = scaledFreq.map((sf, i) => ({ x: sf, y: normalizedImpedance[i] }));

        // Get chart context
        var ctx = document.getElementById("impedanceChart").getContext("2d");

        // Initialize the chart if it doesn't exist
        if (!impedanceChart) {
            impedanceChart = new Chart(ctx, {
                type: "line",
                data: { datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: "logarithmic",
                            position: "bottom",
                            title: { display: true, text: "f / fs" },
                            min: 0.05,
                            max: 1000,
                            ticks: {
                                callback: function (value) {
                                    return Number(value).toFixed(2);
                                }
                            }
                        },
                        y: {
                            type: "linear",
                            title: { display: true, text: "Impedance (Z/Re)" },
                            ticks: { beginAtZero: false }
                        }
                    },
                    elements: {
                        line: { borderJoinStyle: 'round' }
                    },
                    plugins: {
                        legend: { display: true }
                    }
                }
            });
        }

        // Update or add the dataset for the current scenario
        var labelName = scenario.replace("_", " ");
        var dsIndex = impedanceChart.data.datasets.findIndex(ds => ds.label === labelName);

        if (dsIndex === -1) {
            impedanceChart.data.datasets.push({
                label: labelName,
                data: dataPoints,
                borderColor: scenario === "open_air" ? "orange"
                          : scenario === "sealed"  ? "purple"
                          : scenario === "ported"  ? "green"
                          : "brown",
                borderWidth: 1,
                pointRadius: 1,
                fill: false,
                tension: 0.4
            });
        } else {
            impedanceChart.data.datasets[dsIndex].data = dataPoints;
        }

        // Update the chart
        impedanceChart.update();
    }

    function saveSuggestions(formData) {
        var savedSuggestions = JSON.parse(localStorage.getItem("speakerFormSuggestions")) || {};
        Object.keys(formData).forEach(function(key) {
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
        Object.keys(savedSuggestions).forEach(function(key) {
            var dataList = jQuery(`#${key}-suggestions`);
            if (dataList.length) {
                dataList.empty();
                savedSuggestions[key].forEach(function(value) {
                    dataList.append(`<option value="${value}">`);
                });
            }
        });
        console.log("Restored Suggestions:", savedSuggestions);
    }

    // scenario onChange
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

    // Clear both charts
    jQuery('#clearChartBtn').on('click', function () {
        if (responseChart) {
            responseChart.data.datasets = [];
            responseChart.update();
        }
        if (impedanceChart) {
            impedanceChart.data.datasets = [];
            impedanceChart.update();
        }
    });
});