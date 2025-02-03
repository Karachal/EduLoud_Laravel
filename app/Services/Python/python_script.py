import numpy as np
import sys
import json

AIR_DENSITY = 1.2  # kg/m^3 (air density at sea level)
SPEED_OF_SOUND = 343  # m/s (speed of sound in air)

def calculate_speaker_response(parameters):
    try:
        # Extract parameters
        fs = parameters["fs"]
        qts = parameters["qts"]
        vas = parameters["vas"] / 1000  # Convert liters to cubic meters
        re = parameters["re"]
        le = parameters["le"] * 1e-3  # Convert from mH to H
        eg = parameters["eg"]
        qes = parameters["qes"]
        qms = parameters["qms"]
        cms = parameters["cms"] * 1e-3  # Convert from mm/N to m/N
        mms = parameters["mms"] / 1000  # Convert from grams to kg
        bl = parameters["bl"]
        sd = parameters["sd"] / 10000  # Convert from cm² to m²
        rms = parameters["rms"]
        scenario = parameters["scenario"]  

        # Frequency range
        frequencies = np.logspace(np.log10(20), np.log10(20000), 500)
        omega = 2 * np.pi * frequencies

        response_data = {
            "frequencies": frequencies.tolist(),
            "spl": {}
        }

        def calculate_displacement():
            """Helper function to calculate displacement"""
            ze = re + 1j * omega * le
            zm = (1j * omega * mms) + (1 / (1j * omega * cms)) + rms
            zmot = (bl ** 2) / zm
            ztotal = ze + zmot

            current = eg / ztotal
            force = bl * current
            velocity = force / zm
            return velocity / (1j * omega)

        # Open Air (Free Space) Response
        if "open_air" in scenario:
            displacement = calculate_displacement()
            sound_pressure = sd * (omega ** 2) * abs(displacement)
            spl_open_air = 20 * np.log10(sound_pressure / (20e-6))
            response_data["spl"]["open_air"] = spl_open_air.tolist()

        # Sealed Box Response
        if "sealed" in scenario:
            Vb = parameters.get("Vb", 0.03)  # Default: 30L (0.03 m³)
            displacement = calculate_displacement()  # Ensure displacement is recalculated
            sound_pressure = sd * (omega ** 2) * abs(displacement) * 1.2  # Factor for sealed box
            spl_sealed = 20 * np.log10(sound_pressure / (20e-6))
            response_data["spl"]["sealed"] = spl_sealed.tolist()

        # Ported Box Response
        if "ported" in scenario:
            Vb = parameters.get("Vb", 0.03)
            port_length = parameters.get("port_length", 0.1)
            port_diameter = parameters.get("port_diameter", 0.05)
            port_area = np.pi * (port_diameter ** 2) / 4

            displacement = calculate_displacement()  # Ensure displacement is recalculated
            sound_pressure = sd * (omega ** 2) * abs(displacement) * 1.5  # Factor for ported box
            spl_ported = 20 * np.log10(sound_pressure / (20e-6))
            response_data["spl"]["ported"] = spl_ported.tolist()

        return response_data

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    try:
        input_data = json.loads(sys.stdin.read())
        print(json.dumps(calculate_speaker_response(input_data)))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
