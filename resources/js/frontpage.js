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
    
        // Include calculated fields in form data
        jQuery("#cms, #mms, #rms, #bl, #le").each(function () {
            formData[this.id] = parseFloat(jQuery(this).val()) || null;
        });
    
        // Additional fields
        var scenario = formData.scenario;
        if (scenario === "sealed" || scenario === "ported") {
            formData.lx = parseFloat(jQuery("#lx").val()) || null;
            formData.ly = parseFloat(jQuery("#ly").val()) || null;
            formData.lz = parseFloat(jQuery("#lz").val()) || null;
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
        
                    // If impedance data is present, update the Impedance chart
                    if (response.impedance && response.frequencies) {
                        updateImpedanceChart(response, scenario);
                    } else {
                        console.error("Missing impedance or frequency data in response.");
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

    function updateImpedanceChart(response, scenario) {
        console.log("Updating Impedance Chart:", scenario);
    
        // Extract frequency (Hz) and impedance data
        var frequencies = response.frequencies;
        var impData = response.impedance;  // { scenario: [Z array] }
    
        // Validate data
        if (!Array.isArray(frequencies) || !impData || !impData[scenario]) {
            console.error("Invalid data for Impedance chart update.");
            return;
        }
    
        // Create data points for the chart (No normalization needed)
        var dataPoints = frequencies.map((freq, i) => ({ x: freq, y: impData[scenario][i] }));
    
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
                            title: { display: true, text: "Frequency (Hz)" },
                            min: 20,
                            max: 20000,
                            ticks: {
                                callback: function (value) {
                                    return Number(value).toFixed(0);
                                }
                            }
                        },
                        y: {
                            type: "linear",
                            title: { display: true, text: "Impedance (Ohms)" }, // UPDATED Y-AXIS LABEL
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
    
    // Track overridden fields
    let overriddenFields = {};

    // Function to calculate Physical Parameters with correct unit conversions
    function calculatePhysicalParameters() {
        // Constants
        const SOUND_CELERITY = 343;  // Speed of sound in air (m/s)
        const AIR_DENSITY = 1.18;  // Air density (kg/m³)
        const PI = Math.PI;

        // Get input values from form
        let Re = parseFloat(jQuery("#re").val());
        let Qes = parseFloat(jQuery("#qes").val());
        let Qms = parseFloat(jQuery("#qms").val());
        let fs = parseFloat(jQuery("#fs").val());
        let Sd = parseFloat(jQuery("#sd").val()) / 10000; // Convert cm² to m²
        let Vas = parseFloat(jQuery("#vas").val()) / 1000; // Convert L to m³

        // Check if all required values are present
        if (isNaN(Re) || isNaN(Qes) || isNaN(Qms) || isNaN(fs) || isNaN(Sd) || isNaN(Vas)) {
            console.log("Waiting for all Thiele-Small parameters to be entered...");
            return;
        }

        // Calculate Cms (Compliance of Suspension)
        let Cms = (Vas / (Sd ** 2 * AIR_DENSITY * SOUND_CELERITY ** 2)) * 1000000; // Convert from m/N to µm/N

        // Calculate Mms (Moving Mass)
        let Mms = (1 / (((2 * PI * fs) ** 2) * (Cms / 1000))) * 1000; // Convert from kg to grams

        // Calculate Rms (Mechanical Resistance)
        let Rms = (1 / Qms) * Math.sqrt((Mms / 1000) / (Cms / 1000)); // Convert Mms and Cms to SI for calculation

        // Calculate BL (Force Factor)
        let BL = Math.sqrt(Re / (2 * PI * fs * Qes * Qms * (Cms / 1000))); // Convert Cms to SI for calculation

        // Estimate Le (Voice Coil Inductance)
        let Le = (Re / (2 * PI * fs)) * 1000; // Convert H to mH

        // Update form fields with calculated values (only if not overridden by the user)
        if (!overriddenFields.cms) jQuery("#cms").val(Cms.toFixed(6));
        if (!overriddenFields.mms) jQuery("#mms").val(Mms.toFixed(6));
        if (!overriddenFields.rms) jQuery("#rms").val(Rms.toFixed(6));
        if (!overriddenFields.bl) jQuery("#bl").val(BL.toFixed(6));
        if (!overriddenFields.le) jQuery("#le").val(Le.toFixed(6));
    }

    // Attach event listeners to Thiele-Small parameters to trigger recalculation
    jQuery("#re, #qes, #qms, #fs, #sd, #vas").on("input", calculatePhysicalParameters);

    // Listen for user input on calculated fields to mark them as overridden
    jQuery("#cms, #mms, #rms, #bl, #le").on("input", function () {
        overriddenFields[this.id] = true;
    });

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