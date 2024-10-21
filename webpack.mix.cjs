const mix = require('laravel-mix');

// Compile app.js and frontpage.js
mix.js('resources/js/app.js', 'public/js')
   .js('resources/js/frontpage.js', 'public/js')
   .sass('resources/sass/app.scss', 'public/css')
   .scripts([
       'node_modules/jquery/dist/jquery.min.js',
       'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
       // Add other scripts as needed
   ], 'public/js/all.js')
   .version()
   .sourceMaps();