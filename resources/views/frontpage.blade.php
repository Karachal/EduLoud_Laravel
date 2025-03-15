<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>EduLoud 2025</title>

    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-logarithmic"></script>

    <style>
        body { padding: 20px; }
        canvas { max-width: 100%; height: 400px; }
        .form-container { display: block; max-width: 50%; margin: auto; }
        .toggle-button { margin-bottom: 20px; }
        #formIcon { width: 100px; margin-top: 20px; }
        .is-invalid { border-color: #dc3545; }
        .form-section { margin-top: 20px; padding: 15px; border-radius: 10px; background: #f8f9fa; flex: 1; }
        .form-control { font-size: 0.85rem; padding: 5px; }
        .form-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; }
        .form-section-divider { border-right: 2px solid #ccc; padding-right: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 class="mb-4 text-center">EduLoud 2025</h2>

        <div class="text-center">
            <img id="formIcon" src="/images/speaker_icon.webp" alt="Speaker Icon">
        </div>

        <!-- <button class="btn btn-secondary toggle-button" id="toggleFormBtn">Hide Form</button>
        <button type="button" id="clearFormBtn" class="btn btn-secondary">Clear Form</button> -->
        <button class="btn btn-secondary toggle-button d-block mb-2" id="toggleFormBtn">Hide Form</button>
        <button type="button" id="clearFormBtn" class="btn d-block"
            style="background-color: #FFA07A; border-color: #E9967A; color: white;"
            onmouseover="this.style.backgroundColor='#FF7F50'; this.style.borderColor='#E67E22';"
            onmouseout="this.style.backgroundColor='#FFA07A'; this.style.borderColor='#E9967A';">
            Clear Form
        </button>




        <div id="errorMessage" class="alert alert-danger d-none"></div>

        <div class="form-container" id="speakerFormContainer">
            <form id="speakerForm">
                <!-- Include a style block to define the math calligraphy font and increased font sizes -->
                <style>
                    .math-font {
                        font-family: 'STIX Two Math', 'Latin Modern Math', Cambria Math, serif;
                        /* Increase the overall font size */
                        font-size: 1.2rem;
                    }
                    .math-calligraphy {
                        font-family: 'Brush Script MT', 'Great Vibes', cursive;
                        /* Optionally, increase the calligraphic letters further */
                        font-size: 1.3rem;
                    }
                </style>
                <div class="form-group">
                    <label for="speakerPreset">Select a Speaker:</label>
                    <select id="speakerPreset" class="form-control">
                        <option value="">-- Speaker Examples --</option>
                    </select>
                </div>
                <div class="form-row">
                    <!-- Thiele-Small Parameters Section -->
                    <div class="form-section form-section-divider">
                        <h5 class="text-center fw-bold math-font">Thiele-Small Parameters</h5>
                        <div class="row">
                            @foreach ([
                                're'  => '<i>R</i><sub><span style="font-style: normal;">E</span></sub>&thinsp;(<span style="font-style: normal;">Ω</span>)',
                                'qes' => '<i>Q</i><sub><span style="font-style: normal;">es</span></sub>',
                                'qms' => '<i>Q</i><sub><span style="font-style: normal;">ms</span></sub>',
                                'fs'  => '<i>f</i><sub><span style="font-style: normal;">s</span></sub>&thinsp;(<span style="font-style: normal;">Hz</span>)',
                                'sd'  => '<i>S</i><sub><span style="font-style: normal;">d</span></sub>&thinsp;(<span style="font-style: normal;">cm²</span>)',
                                'vas' => '<i>V</i><sub><span style="font-style: normal;">as</span></sub>&thinsp;(<span style="font-style: normal;">L</span>)'
                            ] as $id => $label)
                                <div class="col-md-12">
                                    <label for="{{ $id }}" class="form-label math-font">{!! $label !!}</label>
                                    <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                                    <datalist id="{{ $id }}-suggestions"></datalist>
                                </div>
                            @endforeach
                        </div>
                    </div>

                    <!-- Physical Parameters Section (Auto-Calculated) -->
                    <div class="form-section">
                        <h5 class="text-center fw-bold math-font">Calculated Physical Parameters</h5>
                        <div class="row">
                            @foreach ([
                                'qts' => '<i>Q</i><sub><span style="font-style: normal;">ts</span></sub>',
                                'cms' => '<i>C</i><sub><span style="font-style: normal;">ms</span></sub>&thinsp;(<span style="font-style: normal;">µm/N</span>)',
                                'mms' => '<i>M</i><sub><span style="font-style: normal;">ms</span></sub>&thinsp;(<span style="font-style: normal;">g</span>)',
                                'rms' => '<i>R</i><sub><span style="font-style: normal;">ms</span></sub>&thinsp;(<span style="font-style: normal;">Ns/m</span>)',
                                'bl'  => '<i>Bl</i> (<span style="font-style: normal;">Tm</span>)',
                                'le'  => '<i>L</i><sub><span style="font-style: normal;">e</span></sub>&thinsp;( <span style="font-style: normal;">mH</span>)',
                                'z'   => '<i>Z</i>&thinsp;(<span style="font-style: normal;">Ω</span>)'
                            ] as $id => $label)
                                <div class="col-md-12">
                                    <label for="{{ $id }}" class="form-label math-font">{!! $label !!}</label>
                                    <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" required step="any" data-calculated="true">
                                </div>
                            @endforeach
                        </div>
                    </div>
                </div>

                <!-- Scenario Selection -->
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label for="scenario" class="form-label fw-bold math-font">Type of Analysis</label>
                        <select class="form-control math-font" id="scenario" name="scenario" onchange="toggleBoxFields()">
                            <option value="open_air">Infinite Baffle</option>
                            <option value="sealed">Closed Box Baffle</option>
                            <option value="ported">Bass-reflex Baffle</option>
                        </select>
                    </div>
                </div>

                <!-- Box Parameters -->
                <div id="boxParams" class="row mt-3" style="display: none;">
                    <div class="col-12">
                        <label class="form-label fw-bold math-font">Box Dimensions</label>
                    </div>
                    <div class="col-md-4">
                        <label for="lx" class="form-label math-font">
                            <i>l</i><sub><span style="font-style: normal;">x</span></sub>&thinsp;( <span style="font-style: normal;">cm</span> )
                        </label>
                        <input type="number" class="form-control" id="lx" name="lx" step="0.01">
                    </div>
                    <div class="col-md-4">
                        <label for="ly" class="form-label math-font">
                            <i>l</i><sub><span style="font-style: normal;">y</span></sub>&thinsp;( <span style="font-style: normal;">cm</span> )
                        </label>
                        <input type="number" class="form-control" id="ly" name="ly" step="0.01">
                    </div>
                    <div class="col-md-4">
                        <label for="lz" class="form-label math-font">
                            <i>l</i><sub><span style="font-style: normal;">z</span></sub>&thinsp;( <span style="font-style: normal;">cm</span> )
                        </label>
                        <input type="number" class="form-control" id="lz" name="lz" step="0.01">
                    </div>
                </div>

                <!-- Ported Box Parameters -->
                <div id="portedParams" class="row mt-3" style="display: none;">
                    <div class="col-md-6">
                        <label for="port_length" class="form-label math-font">Port length (cm)</label>
                        <input type="number" class="form-control" id="port_length" name="port_length" list="port_length-suggestions" step="0.01">
                        <datalist id="port_length-suggestions"></datalist>
                    </div>
                    <div class="col-md-6">
                        <label for="port_section_aeria" class="form-label math-font">Port Section Aeria (cm²)</label>
                        <input type="number" class="form-control" id="port_section_aeria" name="port_section_aeria" list="port_section_aeria-suggestions" step="0.01">
                        <datalist id="port_section_aeria-suggestions"></datalist>
                    </div>
                    <div class="d-flex align-items-center mt-4">  
                        <!-- Checkbox -->
                        <div class="form-check me-3">
                            <input type="checkbox" id="port_diagram_response" name="port_diagram_response" class="form-check-input">
                            <label class="form-check-label" for="port_diagram_response">Port & Diaphragm response</label>
                        </div>

                        <!-- Fb Field -->
                        <div>
                            <label for="fb" class="form-label math-font mb-0">
                                <i>f</i><sub><span style="font-style: normal;">b</span></sub>&thinsp;(<span style="font-style: normal;">Hz</span>)
                            </label>
                            <input type="text" class="form-control d-inline-block" id="fb" name="fb" style="width: 80px;" readonly>
                        </div>
                    </div>
                </div>

                <div class="mt-4 text-center">
                    <button type="submit" class="btn btn-primary math-font">Calculate Diagrams</button>
                    <button type="button" id="clearChartBtn" class="btn btn-danger math-font">Clear Diagrams</button>
                </div>
            </form>
        </div>


        <!-- Charts -->
        <div class="mt-5">
            <canvas id="responseChart" style="max-width: 800px; margin: auto;"></canvas>
        </div>
        <div class="mt-5">
            <canvas id="impedanceChart" style="max-width: 800px; margin: auto;"></canvas>
        </div>
        <div class="mt-5">
            <canvas id="portDiaphragmChart" style="max-width: 800px; margin: auto;"></canvas>
        </div>
        
    </div>

    <script>
        function toggleBoxFields() {
            var scenario = document.getElementById("scenario").value;
            document.getElementById("boxParams").style.display = (scenario === "sealed" || scenario === "ported") ? "flex" : "none";
            document.getElementById("portedParams").style.display = (scenario === "ported") ? "flex" : "none";
        }
    </script>

    <script src="{{ asset('js/frontpage.js') }}"></script>
</body>
<footer class="text-center mt-5">
  <p>&copy; Εργαστηριο Ηλεκτρακουστικής και Τηλεοπτικών Συστημάτων ΑΠΘ</p>
  <p>&copy; Laboratory of Electroacoustics and Television Systems, Aristotle University of Thessaloniki</p>
</footer>
</html>