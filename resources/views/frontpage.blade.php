<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>Speaker Response Calculator</title>

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
        <h2 class="mb-4 text-center">Speaker Response Calculator</h2>

        <div class="text-center">
            <img id="formIcon" src="/images/speaker_icon.webp" alt="Speaker Icon">
        </div>

        <button class="btn btn-secondary toggle-button" id="toggleFormBtn">Hide Form</button>

        <div id="errorMessage" class="alert alert-danger d-none"></div>

        <div class="form-container" id="speakerFormContainer">
            <form id="speakerForm">
                <div class="form-row">
                    <!-- Thiele-Small Parameters Section -->
                    <div class="form-section form-section-divider">
                        <h5 class="text-center">Thiele-Small Parameters</h5>
                        <div class="row">
                            @foreach ([
                                're' => 'R<sub>E</sub> (Ω)',
                                'qes' => 'Q<sub>es</sub>',
                                'qms' => 'Q<sub>ms</sub>',
                                'fs' => 'f<sub>s</sub> (Hz)',
                                'sd' => 'S<sub>d</sub> (cm²)',  
                                'vas' => 'V<sub>as</sub> (L)'   
                            ] as $id => $label)
                                <div class="col-md-12">
                                    <label for="{{ $id }}" class="form-label">{!! $label !!}</label>  <!-- Allow raw HTML rendering -->
                                    <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                                    <datalist id="{{ $id }}-suggestions"></datalist>
                                </div>
                            @endforeach
                        </div>
                    </div>


                    <!-- Physical Parameters Section (Auto-Calculated) -->
                    <div class="form-section">
                        <h5 class="text-center">Calculated Physical Parameters</h5>
                        <div class="row">
                            @foreach ([
                                'cms' => 'C<sub>ms</sub> (µm/N)',
                                'mms' => 'M<sub>ms</sub> (g)',
                                'rms' => 'R<sub>ms</sub> (Ns/m)',
                                'bl' => 'B<sub>L</sub> (Tm)',
                                'le' => 'L<sub>e</sub> (mH)'
                            ] as $id => $label)
                                <div class="col-md-12">
                                    <label for="{{ $id }}" class="form-label">{!! $label !!}</label>  <!-- Render subscripts correctly -->
                                    <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" required step="any" data-calculated="true">
                                </div>
                            @endforeach
                        </div>
                    </div>
                </div>

                <!-- Scenario Selection -->
                <div class="row mt-3">
                    <div class="col-md-6">
                        <label for="scenario" class="form-label">Scenario</label>
                        <select class="form-control" id="scenario" name="scenario" onchange="toggleBoxFields()">
                            <option value="open_air">Open Air</option>
                            <option value="sealed">Sealed</option>
                            <option value="ported">Ported</option>
                        </select>
                    </div>
                </div>

                <!-- Box Parameters -->
                <div id="boxParams" class="row mt-3" style="display: none;">
                    <div class="col-12">
                        <label class="form-label fw-bold">Box Dimensions</label>
                    </div>
                    <div class="col-md-4">
                        <label for="lx" class="form-label">l<sub>x</sub> (cm)</label>
                        <input type="number" class="form-control" id="lx" name="lx" step="0.1">
                    </div>
                    <div class="col-md-4">
                        <label for="ly" class="form-label">l<sub>y</sub> (cm)</label>
                        <input type="number" class="form-control" id="ly" name="ly" step="0.1">
                    </div>
                    <div class="col-md-4">
                        <label for="lz" class="form-label">l<sub>z</sub> (cm)</label>
                        <input type="number" class="form-control" id="lz" name="lz" step="0.1">
                    </div>
                </div>

                <!-- Ported Box Parameters -->
                <div id="portedParams" class="row mt-3" style="display: none;">
                    <div class="col-md-6">
                        <label for="port_length" class="form-label">Port length (cm)</label> <!-- Port Length -->
                        <input type="number" class="form-control" id="port_length" name="port_length" list="port_length-suggestions" step="0.1">
                        <datalist id="port_length-suggestions"></datalist>
                    </div>
                    <div class="col-md-6">
                        <label for="port_diameter" class="form-label">Port diameter (cm)</label> <!-- Port Diameter -->
                        <input type="number" class="form-control" id="port_diameter" name="port_diameter" list="port_diameter-suggestions" step="0.1">
                        <datalist id="port_diameter-suggestions"></datalist>
                    </div>
                </div>
                
                <div class="mt-4 text-center">
                    <button type="submit" class="btn btn-primary">Calculate Response</button>
                    <button type="button" id="clearChartBtn" class="btn btn-danger">Clear Chart</button>
                </div>
            </form>
        </div>

        <!-- Charts -->
        <div class="mt-5">
            <canvas id="responseChart"></canvas>
        </div>
        <div class="mt-5">
            <canvas id="impedanceChart"></canvas>
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
</html>