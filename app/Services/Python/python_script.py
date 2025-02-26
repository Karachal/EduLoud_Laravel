import numpy as np
import mpmath
from scipy.special import jv
import json
import sys

# Constants
SOUND_CELERITY = 343  # Speed of sound in air, m/s
R_0 = 1.18  # Air density, kg/m^3
P_0 = 10**5  # Atmospheric pressure, Pa
GAMMA = 1.4  # Adiabatic index
P_REF = 20 * 10 ** (-6)  # Reference sound pressure, Pa (20 µPa)

# Material properties for flow resistance
m = 1.86 * 10 ** (-5)  # Viscosity coefficient, N.s/m^2
R = 60 * 10 ** (-6)  # Fiber diameter, m
POROSITY = 0.99  # Porosity
U = 0.03  # Flow velocity in the material, m/s

# Coefficients for wave number calculation
A3 = 0.0858
A4 = 0.175
B3 = 0.7
B4 = 0.59

class Loudspeaker:
    """Loudspeaker model with Thiele-Small parameters."""
    def __init__(self, lsp_par):
        self.Re = lsp_par["re"]  # Voice coil resistance, Ω
        self.Le = lsp_par["le"]  # Voice coil inductance, H
        self.e_g = lsp_par["eg"]  # Input voltage, V
        self.Qes = lsp_par["qes"]  # Electrical Q factor
        self.Qms = lsp_par["qms"]  # Mechanical Q factor
        self.fs = lsp_par["fs"]  # Resonant frequency, Hz
        self.Vas = lsp_par["vas"]  # Equivalent volume of compliance, m³
        self.Cms = lsp_par["cms"]  # Mechanical compliance, m/N
        self.Mms = lsp_par["mms"]  # Mechanical mass, kg
        self.Bl = lsp_par["bl"]  # Force factor, N/A
        self.Sd = lsp_par["sd"]  # Diaphragm surface area, m²
        self.a = np.sqrt(self.Sd / np.pi)  # Diaphragm radius, m

        # Derived parameters
        self.Qts = (self.Qes * self.Qms) / (self.Qes + self.Qms)  # Total Q factor
        self.Rms = (1 / self.Qms) * np.sqrt(self.Mms / self.Cms)  # Mechanical resistance, N·s/m
        self.Mmd = self.Mms - (16 * R_0 * self.a**3 / 3)  # Effective moving mass, kg

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
        H1 = mpmath.struveh(1, 2 * k * self.a)
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
        pref = 20e-6
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(pref)))
        return SPL

class SealedBoxEnclosure:
    """Sealed box (closed) loudspeaker enclosure model."""
    def __init__(self, loudspeaker, Vb):
        self.loudspeaker = loudspeaker
        self.Vb = Vb * 0.001  # Convert liters to m³

    def calculate_impedance_sealed(self, f):
        """Calculate total system impedance in a sealed enclosure."""
        if self.Vb <= 0:
            return np.inf  # Prevent division errors

        # Air compliance in the box
        C_air = self.Vb / (GAMMA * P_0)  # Box volume affects air compliance
        C_total = 1 / (1 / self.loudspeaker.Cms + 1 / C_air)  # Total compliance

        # Mechanical impedance
        Z_mech = (
            1j * 2 * np.pi * f * self.loudspeaker.Mms
            + self.loudspeaker.Rms
            + 1 / (1j * 2 * np.pi * f * C_total)
        )

        # Electrical impedance
        Z_electrical = self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le

        # Total impedance
        Z_tot = Z_electrical + (self.loudspeaker.Bl**2) / Z_mech
        return Z_tot

    def calculate_spl_sealed(self, f):
        """Calculate SPL in a sealed box."""
        Z_tot = self.calculate_impedance_sealed(f)
        if np.isinf(Z_tot):
            return -100  # If impedance is infinite, return very low SPL

        Z_coil = self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (Z_coil * Z_tot)
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        p_rms = max(np.abs(p_rms), P_REF * 0.1)  # Ensure p_rms is reasonable
        SPL = 20 * np.log10(p_rms / P_REF)
        return SPL

    def calculate_response(self, frequencies):
        return [self.calculate_spl_sealed(f) for f in frequencies]

class PortedBoxEnclosure:
    """Ported (bass reflex) loudspeaker enclosure model."""
    def __init__(self, loudspeaker, Vb, port_length, port_diameter):
        self.loudspeaker = loudspeaker
        self.Vb = Vb * 0.001  # Convert liters to m³
        self.port_length = port_length * 0.01  # Convert cm to m
        self.port_diameter = port_diameter * 0.01  # Convert cm to m
        self.Sp = np.pi * (self.port_diameter / 2) ** 2  # Port area

    def calculate_tuning_frequency(self):
        """Calculate Helmholtz resonance frequency."""
        return (SOUND_CELERITY / (2 * np.pi)) * np.sqrt(self.Sp / (self.Vb * self.port_length))

    def calculate_impedance_ported(self, f):
        """Calculate impedance in a ported enclosure."""
        # Helmholtz resonance frequency
        fb = (SOUND_CELERITY / (2 * np.pi)) * np.sqrt(self.Sp / (self.Vb * self.port_length))

        # Mechanical impedance
        Z_mech = (
            1j * 2 * np.pi * f * self.loudspeaker.Mms
            + self.loudspeaker.Rms
            + 1 / (1j * 2 * np.pi * f * self.loudspeaker.Cms)
        )

        # Port impedance
        M_port = R_0 * self.port_length / self.Sp  # Mass of air in the port
        C_box = self.Vb / (R_0 * SOUND_CELERITY**2)  # Compliance of the air in the box
        Z_port = 1j * (2 * np.pi * f * M_port - 1 / (2 * np.pi * f * C_box))

        # Total impedance (parallel combination of Z_mech and Z_port)
        Z_tot = 1 / (1 / Z_mech + 1 / Z_port)
        return Z_tot

    def calculate_spl_ported(self, f):
        """Calculate SPL in a ported box."""
        Z_tot = self.calculate_impedance_ported(f)
        if np.isinf(Z_tot):
            return -100  # If impedance is infinite, return very low SPL

        Z_coil = self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (Z_coil * Z_tot)
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        p_rms = max(np.abs(p_rms), P_REF * 0.1)  # Ensure p_rms is reasonable
        SPL = 20 * np.log10(p_rms / P_REF)
        return SPL

    def calculate_response(self, frequencies):
        return [self.calculate_spl_ported(f) for f in frequencies]

def calculate_speaker_response(parameters):
    """Calculate the frequency response for the given scenario."""
    try:
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 1500)  # Logarithmic frequency range

        lsp_par = {key: parameters[key] for key in ["re", "le", "eg", "qes", "qms", "fs", "vas", "cms", "mms", "bl", "sd"]}
        loudspeaker = Loudspeaker(lsp_par)

        if scenario == "open_air":
            spl = [loudspeaker.calculate_spl(f) for f in frequencies]
        elif scenario == "sealed":
            Vb = parameters["Vb"]  # Box volume in liters
            enclosure = SealedBoxEnclosure(loudspeaker, Vb)
            spl = enclosure.calculate_response(frequencies)
        elif scenario == "ported":
            Vb = parameters["Vb"]  # Box volume in liters
            port_length = parameters["port_length"]  # Port length in cm
            port_diameter = parameters["port_diameter"]  # Port diameter in cm
            enclosure = PortedBoxEnclosure(loudspeaker, Vb, port_length, port_diameter)
            spl = enclosure.calculate_response(frequencies)

        return {"frequencies": frequencies.tolist(), "spl": {scenario: spl}}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    try:
        input_data = json.loads(sys.stdin.read())
        response = calculate_speaker_response(input_data)
        print(json.dumps(response))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)