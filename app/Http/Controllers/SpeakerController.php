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

    public function calculateSpeakerResponse(Request $request)
    {
        // Validate the request data
        $validated = $request->validate([
            'fs' => 'required|numeric',
            'qts' => 'required|numeric',
            'vas' => 'required|numeric',
            're' => 'required|numeric'
        ]);

        // Use the SpeakerService to calculate the response
        $output = $this->speakerService->calculateResponse($validated);

        // Return the output as JSON response
        return response()->json(['response' => $output]);
    }
}
