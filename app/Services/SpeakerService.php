<?php

namespace App\Services;

use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

class SpeakerService
{
    public function calculateResponse($data)
    {
        // Convert data to JSON format
        $jsonData = json_encode($data);

        // Path to the Python script
        $pythonScript = base_path('app/Services/Python/python_script.py');

        // Use Symfony Process to execute the Python script
        $process = new Process(['python3', $pythonScript]);
        $process->setInput($jsonData);
        $process->run();

        // Check if the process was successful
        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        // Decode the JSON response from Python
        $response = json_decode($process->getOutput(), true);

        // Check if decoding was successful
        if ($response === null) {
            return ["error" => "Failed to parse Python response: " . $process->getOutput()];
        }

        return $response;
    }
}