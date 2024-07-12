<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Speaker and Subwoofer Education App</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="{{ asset('css/app.css') }}" rel="stylesheet">
</head>
<body>
    <div id="app">
        <div class="container text-center"> <!-- Added text-center class to center align the content inside the container -->
            <h1>Welcome to EduLoud Education App</h1>
            <p>This is the main page of your application.</p>
            
            <!-- Image Section -->
            <div class="image-section">
                <img src="{{ asset('images/speaker_icon.webp') }}" alt="speaker_icon" class="img-fluid centered-image">
            </div>

            <a href="#" id="loadSpeakersButton" class="btn btn-primary">Load Speakers</a>
            
            <div id="content">
                <!-- Dynamic content will be loaded here -->
            </div>
        </div>
    </div>

    <!-- jQuery (required for Bootstrap JS plugins) -->
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    
    <!-- Bootstrap JS -->
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.bundle.min.js"></script>
    
    <!-- Custom JS -->
    <script src="{{ asset('js/frontpage.js') }}"></script>
</body>
</html>
