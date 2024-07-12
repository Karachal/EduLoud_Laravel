const mix = require('laravel-mix');

mix.js('resources/js/app.js', 'public/js')
   .sass('resources/sass/app.scss', 'public/css')
   .scripts([
       'node_modules/jquery/dist/jquery.min.js',
       // Add other scripts as needed
   ], 'public/js/all.js');