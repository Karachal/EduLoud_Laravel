<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Speaker and Subwoofer Education App</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Your custom CSS -->
    <link href="{{ asset('css/app.css') }}" rel="stylesheet">
    <style>
        .center-image {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50vh; /* Adjust height as needed */
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="container">
            <h1 class="text-center">Welcome to EduLoud Education App</h1>
            <p class="text-center">This is the main page of your application.</p>
            
            <div class="center-image">
                <img src="{{ asset('images/speaker_icon.webp') }}" alt="speaker_icon" class="img-fluid">
            </div>
            
            <div class="text-center">
                <a href="#" id="loadSpeakersButton" class="btn btn-primary">Load Speakers</a>
            </div>

            <hr>

            <!-- Toggle Button -->
            <div class="text-center mb-3">
                <button class="btn btn-info" type="button" data-toggle="collapse" data-target="#formCollapse" aria-expanded="false" aria-controls="formCollapse">
                    Calculate Speaker Response
                </button>
            </div>

            <!-- Collapsible Form -->
            <div class="collapse" id="formCollapse">
                <div class="card card-body">
                    <h2 class="text-center">Enter Speaker Parameters</h2>
                    <form id="speakerForm" action="{{ route('calculate.speaker.response') }}" method="POST">
                        @csrf <!-- CSRF token for security -->
                        <div class="form-group">
                            <label for="fs">Fs (Resonant Frequency):</label>
                            <input type="number" step="0.01" class="form-control" id="fs" name="fs" required>
                        </div>
                        <div class="form-group">
                            <label for="qts">Qts (Total Q Factor):</label>
                            <input type="number" step="0.01" class="form-control" id="qts" name="qts" required>
                        </div>
                        <div class="form-group">
                            <label for="vas">Vas (Equivalent Volume of Compliance):</label>
                            <input type="number" step="0.01" class="form-control" id="vas" name="vas" required>
                        </div>
                        <div class="form-group">
                            <label for="re">Re (DC Resistance):</label>
                            <input type="number" step="0.01" class="form-control" id="re" name="re" required>
                        </div>
                        <div class="text-center">
                            <button type="submit" class="btn btn-success">Calculate Response</button>
                        </div>
                    </form>
                </div>
            </div>

            <hr>
            
            <div id="content">
                <!-- Dynamic content will be loaded here -->
            </div>
        </div>
    </div>

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    
    <!-- Bootstrap JS -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    
    <!-- Your custom JS -->
    <script src="{{ asset('js/frontpage.js') }}"></script>
</body>
</html>
