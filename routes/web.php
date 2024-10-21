<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\FrontPageController;
use App\Http\Controllers\SpeakerController;

Route::get('/', [FrontPageController::class, 'index']);
Route::post('/calculate-speaker-response', [SpeakerController::class, 'calculateSpeakerResponse'])->name('calculate.speaker.response');
