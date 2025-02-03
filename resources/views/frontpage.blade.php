<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>Speaker Response Calculator</title>

    <!-- Bootstrap (optional) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- jQuery (Load before other scripts) -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body { padding: 20px; }
        canvas { max-width: 100%; height: 400px; }
        .form-container { display: block; }
        .toggle-button { margin-bottom: 20px; }
        #formIcon { width: 100px; margin-top: 20px; }
    </style>
</head>

<body>
    <div class="container">
        <h2 class="mb-4 text-center">Speaker Response Calculator</h2>

        <!-- Display the icon -->
        <div class="text-center">
            <img id="formIcon" src="/images/speaker_icon.webp" alt="Speaker Icon">
        </div>

        <!-- Button to toggle the form -->
        <button class="btn btn-secondary toggle-button" id="toggleFormBtn">Hide Form</button>

        <!-- Error Message -->
        <div id="errorMessage" class="alert alert-danger d-none"></div>

        <!-- Speaker Form -->
        <div class="form-container" id="speakerFormContainer">
            <form id="speakerForm">
                <div class="row">
                    @foreach (['fs' => 'Fs (Hz)', 'qts' => 'Qts', 'vas' => 'Vas (L)'] as $id => $label)
                        <div class="col-md-4">
                            <label for="{{ $id }}" class="form-label">{{ $label }}</label>
                            <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                            <datalist id="{{ $id }}-suggestions"></datalist>
                        </div>
                    @endforeach
                </div>

                <div class="row mt-3">
                    @foreach (['re' => 'Re (Ohms)', 'le' => 'Le (mH)', 'eg' => 'Eg (V)'] as $id => $label)
                        <div class="col-md-4">
                            <label for="{{ $id }}" class="form-label">{{ $label }}</label>
                            <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                            <datalist id="{{ $id }}-suggestions"></datalist>
                        </div>
                    @endforeach
                </div>

                <div class="row mt-3">
                    @foreach (['qes' => 'Qes', 'qms' => 'Qms', 'cms' => 'Cms (mm/N)'] as $id => $label)
                        <div class="col-md-4">
                            <label for="{{ $id }}" class="form-label">{{ $label }}</label>
                            <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                            <datalist id="{{ $id }}-suggestions"></datalist>
                        </div>
                    @endforeach
                </div>

                <div class="row mt-3">
                    @foreach (['mms' => 'Mms (g)', 'bl' => 'BL (Tm)', 'sd' => 'Sd (cm²)'] as $id => $label)
                        <div class="col-md-4">
                            <label for="{{ $id }}" class="form-label">{{ $label }}</label>
                            <input type="number" class="form-control" id="{{ $id }}" name="{{ $id }}" list="{{ $id }}-suggestions" required step="any">
                            <datalist id="{{ $id }}-suggestions"></datalist>
                        </div>
                    @endforeach
                </div>

                <div class="row mt-3">
                    <div class="col-md-4">
                        <label for="rms" class="form-label">Rms (kg/s)</label>
                        <input type="number" class="form-control" id="rms" name="rms" list="rms-suggestions" required step="any">
                        <datalist id="rms-suggestions"></datalist>
                    </div>
                    <div class="col-md-4">
                        <label for="scenario" class="form-label">Scenario</label>
                        <select class="form-control" id="scenario" name="scenario">
                            <option value="open_air">Open Air</option>
                            <option value="sealed">Sealed</option>
                            <option value="ported">Ported</option>
                        </select>
                    </div>
                </div>

                <div class="mt-4 text-center">
                    <button type="submit" class="btn btn-primary">Calculate Response</button>
                </div>
            </form>
        </div>

        <!-- Chart Container -->
        <div class="mt-5">
            <canvas id="responseChart"></canvas>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="{{ asset('js/frontpage.js') }}"></script>
</body>
</html>
