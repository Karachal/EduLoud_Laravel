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
        // Base validation rules
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
            'scenario' => 'required|string|in:open_air,sealed,ported',
        ]);

        // Conditional validation for Vb, port_length, and port_diameter
        if ($validated['scenario'] === 'sealed' || $validated['scenario'] === 'ported') {
            $request->validate(['Vb' => 'required|numeric']);
            $validated['Vb'] = $request->input('Vb');
        }

        if ($validated['scenario'] === 'ported') {
            $request->validate([
                'port_length' => 'required|numeric',
                'port_diameter' => 'required|numeric',
            ]);
            $validated['port_length'] = $request->input('port_length');
            $validated['port_diameter'] = $request->input('port_diameter');
        }

        return response()->json($this->speakerService->calculateResponse($validated));
    }
}