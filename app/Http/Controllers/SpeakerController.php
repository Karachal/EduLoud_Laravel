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
            'fs' => 'required|numeric', // Resonant frequency (Hz)
            'qes' => 'required|numeric', // Electrical Q factor
            'qms' => 'required|numeric', // Mechanical Q factor
            'vas' => 'required|numeric', // Equivalent volume of compliance (m³)
            're' => 'required|numeric', // Voice coil resistance (Ω)
            'le' => 'required|numeric', // Voice coil inductance (H)
            'eg' => 'required|numeric', // Voice coil height (V)
            'cms' => 'required|numeric', // Mechanical compliance
            'mms' => 'required|numeric', // Mechanical mass (g)
            'bl' => 'required|numeric', // Force factor (Tm)
            'sd' => 'required|numeric', // Diaphragm surface area (m²)
            'scenario' => 'required|string|in:open_air,sealed,ported', // Box scenario
        ]);

        // Conditional validation for Vb, port_length, and port_diameter
        if ($validated['scenario'] === 'sealed' || $validated['scenario'] === 'ported') {
            $request->validate(['Vb' => 'required|numeric']); // Box volume (L)
            $validated['Vb'] = $request->input('Vb');
        }

        if ($validated['scenario'] === 'ported') {
            $request->validate([
                'port_length' => 'required|numeric', // Port length (cm)
                'port_diameter' => 'required|numeric', // Port diameter (cm)
            ]);
            $validated['port_length'] = $request->input('port_length');
            $validated['port_diameter'] = $request->input('port_diameter');
        }

        return response()->json($this->speakerService->calculateResponse($validated));
    }
}