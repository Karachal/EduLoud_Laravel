import numpy as np
import mpmath
from scipy.special import jv
import json
import sys

# Constants
SOUND_CELERITY = 343  # Speed of sound in air (m/s)
R_0 = 1.18  # Air density (kg/m^3)
POROSITY = 0.99  # Porosity of the lining material
P_0 = 10**5  # Atmospheric pressure (Pa)
U = 0.03  # Flow velocity in the material (m/s)
m = 1.86 * 10 ** (-5)  # Viscosity coefficient (N.s/m^2)
R = 60 * 10 ** (-6)  # Fiber diameter (m)
GAMMA = 1.4  # Adiabatic index

# Coefficients for characteristic impedance and wave number
A3 = 0.0858
A4 = 0.175
B3 = 0.7
B4 = 0.59


class Loudspeaker:
    """Loudspeaker parameters class."""

    def __init__(self, lsp_par):
        """Initialize the loudspeaker object."""
        self.Re = lsp_par["re"]
        self.Le = lsp_par["le"] * 1e-3  # Convert from mH to H
        self.e_g = lsp_par["eg"]
        self.Qes = lsp_par["qes"]
        self.Qms = lsp_par["qms"]
        self.fs = lsp_par["fs"]
        self.Vas = lsp_par["vas"] / 1000  # Convert liters to cubic meters
        self.Qts = lsp_par["qts"]
        self.Cms = lsp_par["cms"] * 1e-3  # Convert from mm/N to m/N
        self.Mms = lsp_par["mms"] / 1000  # Convert from grams to kg
        self.Bl = lsp_par["bl"]
        self.Sd = lsp_par["sd"] / 10000  # Convert from cm² to m²
        self.Rms = (1 / self.Qms) * np.sqrt(self.Mms / self.Cms) + 0.1 * np.sqrt(self.fs)
        self.Mmd = self.Mms - 16 * R_0 * np.sqrt(self.Sd / np.pi) ** 3 / 3

    def calculate_R_f(self):
        """Calculate flow resistance of lining material."""
        R_f = ((4 * m * (1 - POROSITY)) / (POROSITY * R**2)) * (
            (1 - 4 / np.pi * (1 - POROSITY))
            / (2 + np.log((m * POROSITY) / (2 * R * R_0 * U)))
            + (6 / np.pi) * (1 - POROSITY)
        )
        return float(R_f)  # Convert mpf to float

    def calculate_wave_number(self, f):
        """Calculate the wave number k."""
        R_f = self.calculate_R_f()
        k = (2 * np.pi * f / SOUND_CELERITY) * (
            (1 + A3 * (R_f / f) ** B3) - 1j * A4 * (R_f / f) ** B4
        )
        return float(k)  # Convert mpf to float

    def calculate_acoustic_radiation_impedance(self, f):
        """Calculate acoustic radiation impedance."""
        r = np.sqrt(self.Sd / np.pi)
        wavelength = SOUND_CELERITY / f
        Z_r = R_0 * SOUND_CELERITY * (1 + (8 / (3 * np.pi)) * (r / wavelength) ** 2)
        return float(Z_r)  # Convert mpf to float

    def calculate_spl(self, f):
        """Calculate the sound pressure level."""
        k = self.calculate_wave_number(f)
        H1 = float(mpmath.struveh(1, 2 * k * np.sqrt(self.Sd / np.pi)))  # Convert mpf to float
        Z_r = self.calculate_acoustic_radiation_impedance(f)

        Zmt = (
            self.Bl**2 / (self.Re + 1j * 2 * np.pi * f * self.Le)
            + 1j * 2 * np.pi * f * self.Mmd
            + self.Rms
            + 1 / (1j * 2 * np.pi * f * self.Cms)
            + 2 * self.Sd * R_0 * SOUND_CELERITY * (1 - jv(1, 2 * k * np.sqrt(self.Sd / np.pi)) / (k * np.sqrt(self.Sd / np.pi)) + 1j * H1 / (k * np.sqrt(self.Sd / np.pi)))
        )

        u_c = self.e_g * self.Bl / ((self.Re + 0.01 * f + 1j * 2 * np.pi * f * self.Le) * Zmt)
        p_rms = R_0 * SOUND_CELERITY * np.abs(u_c) / self.Sd

        pref = 20e-6
        SPL = 20 * np.log10(max(np.abs(p_rms), 1e-12) / pref)  # Ensure p_rms is not zero
        return float(SPL)  # Convert mpf to float


class ClosedBoxEnclosure:
    """Closed box enclosure parameters class."""

    def __init__(self, lsp, Vb):
        """Initialize the closed box enclosure object."""
        self.lsp = lsp
        self.Vb = Vb / 1000  # Convert liters to cubic meters

    def calculate_response(self, frequencies):
        """Calculate the system response for a closed box enclosure."""
        # Calculate the new compliance due to the enclosure
        Cms_new = self.lsp.Cms / (1 + self.lsp.Vas / self.Vb)

        # Calculate the new resonant frequency
        fs_new = self.lsp.fs * np.sqrt(1 + self.lsp.Vas / self.Vb)

        # Calculate the new Q-factor
        Qts_new = self.lsp.Qts * np.sqrt(1 + self.lsp.Vas / self.Vb)

        # Create a copy of the loudspeaker object to avoid modifying the original
        lsp_copy = Loudspeaker({
            "re": self.lsp.Re,
            "le": self.lsp.Le * 1e3,  # Convert back to mH
            "eg": self.lsp.e_g,
            "qes": self.lsp.Qes,
            "qms": self.lsp.Qms,
            "fs": fs_new,
            "vas": self.lsp.Vas * 1000,  # Convert back to liters
            "qts": Qts_new,
            "cms": Cms_new * 1e3,  # Convert back to mm/N
            "mms": self.lsp.Mms * 1000,  # Convert back to grams
            "bl": self.lsp.Bl,
            "sd": self.lsp.Sd * 10000,  # Convert back to cm²
        })

        # Calculate the SPL response
        spl = np.zeros_like(frequencies)
        for i, f in enumerate(frequencies):
            spl[i] = lsp_copy.calculate_spl(f)
        return spl


class BassReflexEnclosure:
    """Bass reflex enclosure parameters class."""

    def __init__(self, lsp, Vb, port_length, port_diameter):
        """Initialize the bass reflex enclosure object."""
        self.lsp = lsp
        self.Vb = Vb / 1000  # Convert liters to cubic meters
        self.port_length = port_length / 100  # Convert cm to meters
        self.port_diameter = port_diameter / 100  # Convert cm to meters

    def calculate_response(self, frequencies):
        """Calculate the system response for a bass reflex enclosure."""
        # Calculate the port resonance frequency
        port_area = np.pi * (self.port_diameter / 2) ** 2
        port_volume = port_area * self.port_length
        fb = (SOUND_CELERITY / (2 * np.pi)) * np.sqrt(port_area / (self.Vb * port_volume))

        # Create a copy of the loudspeaker object to avoid modifying the original
        lsp_copy = Loudspeaker({
            "re": self.lsp.Re,
            "le": self.lsp.Le * 1e3,  # Convert back to mH
            "eg": self.lsp.e_g,
            "qes": self.lsp.Qes,
            "qms": self.lsp.Qms,
            "fs": fb,  # Set the resonant frequency to the port resonance frequency
            "vas": self.lsp.Vas * 1000,  # Convert back to liters
            "qts": self.lsp.Qts,
            "cms": self.lsp.Cms * 1e3,  # Convert back to mm/N
            "mms": self.lsp.Mms * 1000,  # Convert back to grams
            "bl": self.lsp.Bl,
            "sd": self.lsp.Sd * 10000,  # Convert back to cm²
        })

        # Calculate the SPL response
        spl = np.zeros_like(frequencies)
        for i, f in enumerate(frequencies):
            spl[i] = lsp_copy.calculate_spl(f)
        return spl


def calculate_speaker_response(parameters):
    """Calculate the SPL response for the selected scenario."""
    try:
        # Extract parameters
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 500)

        # Create loudspeaker object
        lsp_par = {
            "re": parameters["re"],
            "le": parameters["le"],
            "eg": parameters["eg"],
            "qes": parameters["qes"],
            "qms": parameters["qms"],
            "fs": parameters["fs"],
            "vas": parameters["vas"],
            "qts": parameters["qts"],
            "cms": parameters["cms"],
            "mms": parameters["mms"],
            "bl": parameters["bl"],
            "sd": parameters["sd"],
        }
        loudspeaker = Loudspeaker(lsp_par)

        # Calculate response based on scenario
        if scenario == "open_air":
            spl = [loudspeaker.calculate_spl(f) for f in frequencies]
            response_data = {
                "frequencies": frequencies.tolist(),
                "spl": {"open_air": spl}
            }
        elif scenario == "sealed":
            enclosure = ClosedBoxEnclosure(loudspeaker, parameters["Vb"])
            spl = enclosure.calculate_response(frequencies)
            response_data = {
                "frequencies": frequencies.tolist(),
                "spl": {"sealed": spl.tolist()}
            }
        elif scenario == "ported":
            enclosure = BassReflexEnclosure(loudspeaker, parameters["Vb"], parameters["port_length"], parameters["port_diameter"])
            spl = enclosure.calculate_response(frequencies)
            response_data = {
                "frequencies": frequencies.tolist(),
                "spl": {"ported": spl.tolist()}
            }
        else:
            raise ValueError("Invalid scenario selected.")

        return response_data

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    try:
        input_data = json.loads(sys.stdin.read())
        print(json.dumps(calculate_speaker_response(input_data)))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)