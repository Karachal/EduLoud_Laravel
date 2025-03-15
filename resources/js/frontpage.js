jQuery(document).ready(function () {
    var responseChart;   // For SPL vs freq(Hz)
    var impedanceChart;  // For Impedance vs (f/fs)
    var portDiaphragmChart;
    var speakers = [];

    restoreSuggestions();

    // Load speaker presets from Laravel's JSON route
    jQuery.getJSON("/speakers", function (data) {
        speakers = data;
        var dropdown = jQuery("#speakerPreset");
        data.forEach(function (speaker) {
            dropdown.append(new Option(speaker.name, JSON.stringify(speaker)));
        });
    });

    // When the user selects a speaker, populate the form with its values
    jQuery("#speakerPreset").on("change", function () {
        var selectedSpeaker = JSON.parse(jQuery(this).val() || "{}");

        if (!selectedSpeaker.name) return;

        // Fill the form fields with the selected speaker data
        jQuery("#re").val(selectedSpeaker.re);
        jQuery("#le").val(selectedSpeaker.le);
        jQuery("#qes").val(selectedSpeaker.qes);
        jQuery("#qms").val(selectedSpeaker.qms);
        jQuery("#fs").val(selectedSpeaker.fs);
        jQuery("#vas").val(selectedSpeaker.vas);
        jQuery("#cms").val(selectedSpeaker.cms);
        jQuery("#mms").val(selectedSpeaker.mms);
        jQuery("#rms").val(selectedSpeaker.rms);
        jQuery("#bl").val(selectedSpeaker.bl);
        jQuery("#sd").val(selectedSpeaker.sd);
        jQuery("#z").val(selectedSpeaker.z);

        //Trigger Qts Calculation
        calculatePhysicalParameters();
    });
    // Toggle form visibility
    jQuery('#toggleFormBtn').on('click', function () {
        jQuery('#speakerFormContainer').toggle();
        var isVisible = jQuery('#speakerFormContainer').is(':visible');
        jQuery('#toggleFormBtn').text(isVisible ? 'Hide Form' : 'Show Form');
    });

    // Function to clear all form fields
    jQuery("#clearFormBtn").on("click", function () {
        jQuery("#speakerForm")[0].reset(); // Reset all fields to default

        // Also clear manually filled calculated fields
        jQuery("#qts").val("");
        jQuery("#cms").val("");
        jQuery("#mms").val("");
        jQuery("#rms").val("");
        jQuery("#bl").val("");
        // Reset Type of Analysis dropdown
        jQuery("#scenario").val("open_air").trigger("change"); // Ensures the dropdown resets and triggers onchange event

        // Hide additional fields (Sealed & Ported box parameters)
        jQuery("#boxParams").hide();
        jQuery("#portedParams").hide();
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
        jQuery("#qts, #cms, #mms, #rms, #bl, #le, #z").each(function () {
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
            formData.port_section_aeria = parseFloat(jQuery("#port_section_aeria").val()) || null;
            formData.port_diagram_response = jQuery("#port_diagram_response").is(":checked");
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

                    // Update Port & Diaphragm Chart ONLY IF "ported" and checkbox enabled
                    if (scenario === "ported" && formData.port_diagram_response) {
                        if (response.spl_port && response.spl_diaphragm) {
                            updatePortDiaphragmChart(response.frequencies, response, scenario);
                        } else {
                            console.error("Missing port/diaphragm response data.");
                        }
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
                                autoSkip: true,    // Automatically skips overlapping ticks
                                maxTicksLimit: 20, // Limits the number of ticks to 10
                                callback: function(value) {
                                    return Number(value).toFixed(0);
                                }
                            }
                        },
                        y: {
                            title: { display: true, text: "SPL (dB)" },
                            min: 60,
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
                borderWidth: 0.5,
                pointRadius: 0.5,
                fill: false,
                tension: 0.4
            });
        } else {
            responseChart.data.datasets[dsIndex].data = dataPoints;
        }

        responseChart.update();
    }
    // IMPEDANCE vs frequency(Hz)
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
                                autoSkip: true,    // Automatically skips overlapping ticks
                                maxTicksLimit: 20, // Limits the number of ticks to 20
                                callback: function (value) {
                                    return Number(value).toFixed(0);
                                }
                            }
                        },
                        y: {
                            type: "linear",
                            title: { display: true, text: "Impedance (Ω)" }, // UPDATED Y-AXIS LABEL
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
                borderWidth: 0.5,
                pointRadius: 0.5,
                fill: false,
                tension: 0.4
            });
        } else {
            impedanceChart.data.datasets[dsIndex].data = dataPoints;
        }
    
        // Update the chart
        impedanceChart.update();
    }

    // Function to update the new Port & Diaphragm SPL chart
    function updatePortDiaphragmChart(frequencies, response, scenario) {
        console.log("Updating Port & Diaphragm Response Chart:", scenario);

        // Check if the response contains the required data
        if (!Array.isArray(frequencies) || !response.spl_port || !response.spl_diaphragm) {
            console.error("Invalid data for Port & Diaphragm chart update.");
            return;
        }

        var ctx = document.getElementById("portDiaphragmChart").getContext("2d");

        if (!portDiaphragmChart) {
            portDiaphragmChart = new Chart(ctx, {
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
                                autoSkip: true,
                                maxTicksLimit: 20,
                                callback: function (value) {
                                    return Number(value).toFixed(0);
                                }
                            }
                        },
                        y: {
                            title: { display: true, text: "SPL (dB)" },
                            min: 40,
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

        // Define datasets for SPL_port and SPL_diaphragm
        var datasetsToAdd = [];

        if (response.spl_port[scenario]) {
            datasetsToAdd.push({
                label: scenario.replace("_", " ") + " SPL (Port)",
                data: frequencies.map((f, i) => ({ x: f, y: response.spl_port[scenario][i] })),
                borderColor: "blue",
                borderWidth: 1,
                pointRadius: 0.5,
                fill: false,
                tension: 0.4
            });
        }

        if (response.spl_diaphragm[scenario]) {
            datasetsToAdd.push({
                label: scenario.replace("_", " ") + " SPL (Diaphragm)",
                data: frequencies.map((f, i) => ({ x: f, y: response.spl_diaphragm[scenario][i] })),
                borderColor: "green",
                borderWidth: 1,
                pointRadius: 0.5,
                fill: false,
                tension: 0.4
            });
        }

        // Replace datasets and update the chart
        portDiaphragmChart.data.datasets = datasetsToAdd;
        portDiaphragmChart.update();
    }
    
    // Track overridden fields
    let overriddenFields = {};

    // Function to round a number to 3 significant figures
    function roundToSignificantFigures(num, sigFigs = 3) {
        if (num === 0) return 0; // Avoid log issues with zero
        let scale = Math.pow(10, sigFigs - Math.floor(Math.log10(Math.abs(num))) - 1);
        return Math.round(num * scale) / scale;
    }

    // Function to calculate Fb (Tuning Frequency)
    function calculateFb() {
        console.log("calculateFb function triggered!"); // Debugging message

        // Read and convert input values
        let lx = parseFloat(jQuery("#lx").val()) * 0.01; // Convert cm to m
        let ly = parseFloat(jQuery("#ly").val()) * 0.01;
        let lz = parseFloat(jQuery("#lz").val()) * 0.01;
        let portLength = parseFloat(jQuery("#port_length").val()) * 0.01; // Convert cm to m
        let portSection = parseFloat(jQuery("#port_section_aeria").val()) * 0.0001; // Convert cm² to m²

        console.log("Raw input values - lx:", lx, "ly:", ly, "lz:", lz, "portLength:", portLength, "portSection:", portSection);

        // Check for missing values
        if (isNaN(lx) || isNaN(ly) || isNaN(lz) || isNaN(portLength) || isNaN(portSection)) {
            console.log("Missing values, fb calculation skipped.");
            jQuery("#fb").val("");
            return;
        }

        // Box volume (Vb) in cubic meters
        let Vb = lx * ly * lz;

        // ✅ Directly calculate Sp, Vp, and Vab inside this function
        let Sp = portSection; // Port section area in m² (already converted)
        let Vp = Sp * portLength; // Port volume in m³
        let Vab = Vb - Vp; // Effective box volume in m³

        console.log("Port Section Area (Sp) in m²:", Sp);
        console.log("Port Volume (Vp) in m³:", Vp);
        console.log("Effective Box Volume (Vab) in m³:", Vab);

        // Ensure values are valid
        if (Vab <= 0 || Vp <= 0) {
            console.log("Error: Vab or Vp is invalid. Fb calculation stopped.");
            jQuery("#fb").val("");
            return;
        }

        // ✅ Correct Fb formula (NO ROUNDING)
        let fb = (344.8 / (2 * Math.PI * portLength)) * Math.sqrt(Vp / Vab);

        console.log("Raw Fb:", fb); // ✅ Debugging message

        // ✅ Update the fb field with the raw value
        jQuery("#fb").val(fb);
    }

    // Ensure Fb is calculated when inputs change
    jQuery(document).ready(function () {
        console.log("Page loaded - running calculateFb() once");
        calculateFb(); // Run once on page load
    });

    // Trigger recalculation when inputs change
    jQuery("#port_length, #port_section_aeria, #lx, #ly, #lz").off("input").on("input", calculateFb);


   

    // Function to calculate Physical Parameters with correct unit conversions
    function calculatePhysicalParameters() {
        // Constants
        const SOUND_CELERITY = 344.8;  // Speed of sound in air (m/s)
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

        // Calculate Total Q Factor
        let Qts = (Qes * Qms) / (Qes + Qms);

        // Calculate Cms (Compliance of Suspension)
        let Cms = (Vas / (Sd ** 2 * AIR_DENSITY * SOUND_CELERITY ** 2));

        // Calculate Mms (Moving Mass)
        let Mms = (1 / (((2 * PI * fs) ** 2) * Cms));

        // Calculate Rms (Mechanical Resistance)
        let Rms = (1 / Qms) * Math.sqrt(Mms / Cms); 

        // Calculate BL (Force Factor)
        let BL = Math.sqrt(Re / (2 * PI * fs * Qes * Cms));

        Cms = Cms * 1000000; // convert from m/N to μm/N
        Mms = Mms * 1000; //convert from kg to g
        

        // Update form fields with calculated values (only if not overridden by the user)
        if (!overriddenFields.qts) jQuery("#qts").val(roundToSignificantFigures(Qts, 3));
        if (!overriddenFields.cms) jQuery("#cms").val(roundToSignificantFigures(Cms, 3));
        if (!overriddenFields.mms) jQuery("#mms").val(roundToSignificantFigures(Mms, 3));
        if (!overriddenFields.rms) jQuery("#rms").val(roundToSignificantFigures(Rms, 3));
        if (!overriddenFields.bl) jQuery("#bl").val(roundToSignificantFigures(BL, 3));
    }

    // Attach event listeners to Thiele-Small parameters to trigger recalculation
    jQuery("#re, #qes, #qms, #fs, #sd, #vas").on("input", calculatePhysicalParameters);

    // Listen for user input on calculated fields to mark them as overridden
    //DELETED #le
    jQuery("#qts, #cms, #mms, #rms, #bl").on("input", function () {
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