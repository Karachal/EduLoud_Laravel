import numpy as np
import mpmath
from scipy.special import jv
import json
import sys

# Constants
SOUND_CELERITY = 343  # Speed of sound in air, m/s
R_0 = 1.18  # Air density, kg/m^3
LM = 6 * 10 ** (-8)  # Molecular mean free path length between collisions, m
POROSITY = 0.99  # Porosity
P_0 = 10**5  # Atmospheric pressure, Pa
U = 0.03  # Flow velocity in the material, m/s
m = 1.86 * 10 ** (-5)  # Viscosity coefficient, N.s/m^2
R = 60 * 10 ** (-6)  # Fiber diameter, m
GAMMA = 1.4  # Adiabatic index

# Coefficients for characteristic impedance and wave number of a homogeneous absorbent material
A3 = 0.0858
A4 = 0.175
B3 = 0.7
B4 = 0.59

# Reference sound pressure, Pa (20 µPa)
P_REF = 20 * 10 ** (-6)

class Loudspeaker:
    """Loudspeaker model with Thiele-Small parameters."""
    def __init__(self, lsp_par):
        self.Re = lsp_par["re"]
        self.Le = lsp_par["le"]  # Already in H (Henries)
        self.e_g = lsp_par["eg"]
        self.Qes = lsp_par["qes"]
        self.Qms = lsp_par["qms"]
        self.fs = lsp_par["fs"]
        self.Vas = lsp_par["vas"]  # Already in m³
        self.Cms = lsp_par["cms"]  # Already in m/N
        self.Mms = lsp_par["mms"]  # Already in kg
        self.Bl = lsp_par["bl"]
        self.Sd = lsp_par["sd"]  # Already in m²
        self.a = np.sqrt(self.Sd / np.pi)  # Diaphragm radius

        # Derived parameters
        self.Qts = (self.Qes * self.Qms) / (self.Qes + self.Qms)
        self.Rms = (1 / self.Qms) * np.sqrt(self.Mms / self.Cms)
        self.Mmd = self.Mms - (16 * R_0 * self.a**3 / 3)

    def calculate_R_f(self):
        """Calculate flow resistance of lining material, Eq. 7.8."""
        R_f = ((4 * m * (1 - POROSITY)) / (POROSITY * R**2)) * (
            (1 - 4 / np.pi * (1 - POROSITY))
            / (2 + np.log((m * POROSITY) / (2 * R * R_0 * U)))
            + (6 / np.pi) * (1 - POROSITY)
        )
        return R_f

    def calculate_wave_number(self, f):
        """Calculate the wave number k."""
        R_f = self.calculate_R_f()
        k = (2 * np.pi * f / SOUND_CELERITY) * (
            (1 + A3 * (R_f / f) ** B3) - 1j * A4 * (R_f / f) ** B4
        )
        return k

    def calculate_spl(self, f):
        """Calculate the sound pressure level."""
        k = self.calculate_wave_number(f)
        H1 = float(mpmath.struveh(1, 2 * k * self.a))  # Convert to float
        Zmt = (
            self.Bl**2 / (self.Re + 1j * 2 * np.pi * f * self.Le)
            + 1j * 2 * np.pi * f * self.Mmd
            + self.Rms
            + 1 / (1j * 2 * np.pi * f * self.Cms)
            + 2
            * self.Sd
            * R_0
            * SOUND_CELERITY
            * (1 - jv(1, 2 * k * self.a) / (k * self.a) + 1j * H1 / (k * self.a))
        )
        u_c = self.e_g * self.Bl / ((self.Re + 1j * 2 * np.pi * f * self.Le) * Zmt)
        p_rms = R_0 * f * self.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        return SPL

class SealedBoxEnclosure:
    """Sealed Box (Closed Box) Loudspeaker Enclosure Parameters."""

    def __init__(self, loudspeaker, Vb):
        self.loudspeaker = loudspeaker
        self.Vb = Vb  # Box volume is directly provided

    def calculate_impedance_sealed(self, f):
        """Calculate the impedance in a sealed box at a given frequency."""
        V_eff = self.loudspeaker.Vas * (1 + self.Vb / self.loudspeaker.Vas)  # Effective compliance
        Zmt = self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le + 1 / (1j * 2 * np.pi * f * self.loudspeaker.Cms) + 1j * 2 * np.pi * f * self.loudspeaker.Mms
        return Zmt

    def calculate_spl_sealed(self, f):
        """Calculate the SPL in a sealed box."""
        Zmt = self.calculate_impedance_sealed(f)
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le) / Zmt
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        return SPL

    def calculate_response(self, frequencies):
        """Calculate the system response for a sealed box."""
        spl_values = np.zeros_like(frequencies)
        for i in range(len(frequencies)):
            spl_values[i] = self.calculate_spl_sealed(frequencies[i])
        return spl_values

class PortedBoxEnclosure:
    """Ported Box (Bass Reflex) Loudspeaker Enclosure Parameters."""

    def __init__(self, loudspeaker, Vb):
        self.loudspeaker = loudspeaker
        self.Vb = Vb  # Box volume is directly provided
        self.calculate_port()

    def calculate_port(self):
        """Calculate the port parameters."""
        fb = self.loudspeaker.fs * 0.9735  # Tuning frequency (fixed value based on alignment)
        Vmax = 0.001 * self.loudspeaker.Sd * fb  # Maximum volume displacement
        Vp = 10 * Vmax  # Port volume
        port_length = 345 / (2 * np.pi * fb) * np.sqrt(Vp / self.Vb)  # Length of the port
        Sp = (Vp * 0.001) / port_length  # Area of the port
        return Sp, port_length, fb

    def calculate_impedance_ported(self, f):
        """Calculate the impedance in a ported box at a given frequency."""
        Sp, port_length, fb = self.calculate_port()
        Zmt = self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le + 1 / (1j * 2 * np.pi * f * self.loudspeaker.Cms) + 1j * 2 * np.pi * f * self.loudspeaker.Mms
        Z_port = 1 / (1j * 2 * np.pi * f * Sp)  # Port impedance
        return Zmt + Z_port  # Combined impedance

    def calculate_spl_ported(self, f):
        """Calculate the SPL in a ported box."""
        Zmt = self.calculate_impedance_ported(f)
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le) / Zmt
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        return SPL

    def calculate_response(self, frequencies):
        """Calculate the system response for a ported box."""
        spl_values = np.zeros_like(frequencies)
        for i in range(len(frequencies)):
            spl_values[i] = self.calculate_spl_ported(frequencies[i])
        return spl_values

def calculate_speaker_response(parameters):
    """Calculate the frequency response for the given scenario."""
    try:
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 500)  # Logarithmic frequency range

        lsp_par = {key: parameters[key] for key in ["re", "le", "eg", "qes", "qms", "fs", "vas", "cms", "mms", "bl", "sd"]}
        loudspeaker = Loudspeaker(lsp_par)

        if scenario == "open_air":
            spl = [loudspeaker.calculate_spl(f) for f in frequencies]
            response_data = {"frequencies": frequencies.tolist(), "spl": {"open_air": spl}}
        elif scenario == "sealed":
            enclosure = SealedBoxEnclosure(loudspeaker, parameters["Vb"])
            spl = enclosure.calculate_response(frequencies)
            response_data = {"frequencies": frequencies.tolist(), "spl": {"sealed": spl.tolist()}}
        elif scenario == "ported":
            enclosure = PortedBoxEnclosure(loudspeaker, parameters["Vb"])
            spl = enclosure.calculate_response(frequencies)
            response_data = {"frequencies": frequencies.tolist(), "spl": {"ported": spl.tolist()}}
        return response_data
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    try:
        # Read input data from stdin
        input_data = json.loads(sys.stdin.read())
        # Calculate response
        response = calculate_speaker_response(input_data)
        # Output JSON response
        print(json.dumps(response))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)