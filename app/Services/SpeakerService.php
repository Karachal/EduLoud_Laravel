<?php

namespace App\Services;

class SpeakerService
{
    public function calculateResponse($data)
    {
        // Prepare the command to call the Python script
        $scriptPath = base_path('app/Services/Python/python_script.py'); // Get the absolute path to the Python script
        $command = escapeshellcmd("python3 {$scriptPath} {$data['fs']} {$data['qts']} {$data['vas']} {$data['re']}");

        // Execute the Python script and capture the output
        $output = shell_exec($command);

        // Return the Python script output
        return $output;
    }
}
