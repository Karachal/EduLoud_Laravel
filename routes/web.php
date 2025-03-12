<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\SpeakerController;
use Illuminate\Support\Facades\Storage;

Route::get('/', function () {
    return view('frontpage');
});

Route::post('/calculate-speaker-response', [SpeakerController::class, 'calculate'])->name('calculate.speaker.response');

Route::get('/speakers', function () {
    $path = storage_path('app/data/speakers.json');

    if (!file_exists($path)) {
        return response()->json(["error" => "Speakers file not found"], 404);
    }

    return response()->json(json_decode(file_get_contents($path), true));
});
