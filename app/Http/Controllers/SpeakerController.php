<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Services\SpeakerService;

class SpeakerController extends Controller
{
    protected $speakerService;

    public function __construct(SpeakerService $speakerService)
    {
        $this->speakerService = $speakerService;
    }

    public function calculate(Request $request)
    {
        $validated = $request->validate([
            'fs' => 'required|numeric',
            'qts' => 'required|numeric',
            'vas' => 'required|numeric',
            're' => 'required|numeric',
            'le' => 'required|numeric',
            'eg' => 'required|numeric',
            'qes' => 'required|numeric',
            'qms' => 'required|numeric',
            'cms' => 'required|numeric',
            'mms' => 'required|numeric',
            'bl' => 'required|numeric',
            'sd' => 'required|numeric',
            'rms' => 'required|numeric',
            'scenario' => 'required|string'
        ]);

        $response = $this->speakerService->calculateResponse($validated);
        return response()->json($response);
    }
}
