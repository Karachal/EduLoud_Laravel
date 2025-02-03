<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\SpeakerController;

Route::get('/', function () {
    return view('frontpage');
});

Route::post('/calculate-speaker-response', [SpeakerController::class, 'calculate'])->name('calculate.speaker.response');
