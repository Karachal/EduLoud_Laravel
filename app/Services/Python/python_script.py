import numpy as np
from scipy.special import jv
import json
import sys
from functools import lru_cache

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
        """Initialize the loudspeaker object."""
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

        # Precompute constants
        self.k_const = 2 * np.pi / SOUND_CELERITY
        self.R_f = self.calculate_R_f()  # Precompute R_f

    @lru_cache(maxsize=None)  # Cache results for repeated calls
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
        k = self.k_const * f * ((1 + A3 * (self.R_f / f) ** B3) - 1j * A4 * (self.R_f / f) ** B4)
        return k

    def calculate_spl_and_impedance(self, f):
        """Calculate the sound pressure level and total impedance."""
        k = self.calculate_wave_number(f)
        H1 = jv(1, 2 * k * self.a)  # Use scipy's Bessel function for speed
        Zmt = (
            self.Bl**2 / (self.Re + 1j * 2 * np.pi * f * self.Le)
            + 1j * 2 * np.pi * f * self.Mmd
            + self.Rms
            + 1 / (1j * 2 * np.pi * f * self.Cms)
            + 2
            * self.Sd
            * R_0
            * SOUND_CELERITY
            * (1 - H1 / (k * self.a) + 1j * H1 / (k * self.a))
        )
        u_c = self.e_g * self.Bl / ((self.Re + 1j * 2 * np.pi * f * self.Le) * Zmt)
        p_rms = R_0 * f * self.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        Z_tot = self.Re + 1j * 2 * np.pi * f * self.Le + (self.Bl**2) / Zmt
        return SPL, np.abs(Z_tot)


class SealedBoxEnclosure:
    """Sealed box (closed) loudspeaker enclosure model."""

    def __init__(self, loudspeaker, Vb):
        self.loudspeaker = loudspeaker
        self.Vb = Vb * 0.001  # Convert liters to m³

    def calculate_spl_and_impedance(self, f):
        """Calculate SPL and impedance in a sealed box."""
        # Air compliance in the box
        C_air = self.Vb / (GAMMA * P_0)
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

        # Calculate SPL
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (Z_electrical * Z_tot)
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        return SPL, np.abs(Z_tot)

    def calculate_response(self, frequencies):
        spl = []
        impedance = []
        for f in frequencies:
            SPL, Z_tot = self.calculate_spl_and_impedance(f)
            spl.append(SPL)
            impedance.append(Z_tot)
        return np.array(spl), np.array(impedance)


class PortedBoxEnclosure:
    """Ported (bass reflex) loudspeaker enclosure model."""

    def __init__(self, loudspeaker, Vb, port_length, port_diameter):
        self.loudspeaker = loudspeaker
        self.Vb = Vb * 0.001  # Convert liters to m³
        self.port_length = port_length * 0.01  # Convert cm to m
        self.port_diameter = port_diameter * 0.01  # Convert cm to m
        self.Sp = np.pi * (self.port_diameter / 2) ** 2  # Port area

    def calculate_spl_and_impedance(self, f):
        """Calculate SPL and impedance in a ported box."""
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

        # Calculate SPL
        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (
            (self.loudspeaker.Re + 1j * 2 * np.pi * f * self.loudspeaker.Le) * Z_tot
        )
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10(float(np.abs(p_rms)) / float(np.abs(P_REF)))
        return SPL, np.abs(Z_tot)

    def calculate_response(self, frequencies):
        spl = []
        impedance = []
        for f in frequencies:
            SPL, Z_tot = self.calculate_spl_and_impedance(f)
            spl.append(SPL)
            impedance.append(Z_tot)
        return np.array(spl), np.array(impedance)


def calculate_speaker_response(parameters):
    """Calculate the frequency response and impedance for the given scenario."""
    try:
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 1500)  # Logarithmic frequency range

        lsp_par = {key: parameters[key] for key in ["re", "le", "eg", "qes", "qms", "fs", "vas", "cms", "mms", "bl", "sd"]}
        loudspeaker = Loudspeaker(lsp_par)

        if scenario == "open_air":
            spl = []
            impedance = []
            for f in frequencies:
                SPL, Z_tot = loudspeaker.calculate_spl_and_impedance(f)
                spl.append(SPL)
                impedance.append(Z_tot)
            spl = np.array(spl)
            impedance = np.array(impedance)
        elif scenario == "sealed":
            Vb = parameters["Vb"]  # Box volume in liters
            enclosure = SealedBoxEnclosure(loudspeaker, Vb)
            spl, impedance = enclosure.calculate_response(frequencies)
        elif scenario == "ported":
            Vb = parameters["Vb"]  # Box volume in liters
            port_length = parameters["port_length"]  # Port length in cm
            port_diameter = parameters["port_diameter"]  # Port diameter in cm
            enclosure = PortedBoxEnclosure(loudspeaker, Vb, port_length, port_diameter)
            spl, impedance = enclosure.calculate_response(frequencies)

        # Normalized frequency (f/fs)
        f_over_fs = frequencies / loudspeaker.fs

        return {
            "frequencies": frequencies.tolist(),
            "spl": {scenario: spl.tolist()},
            "impedance": {scenario: impedance.tolist()},
            "f_over_fs": f_over_fs.tolist(),
            "Re": loudspeaker.Re  # Ensure Re is included
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    try:
        input_data = json.loads(sys.stdin.read())
        response = calculate_speaker_response(input_data)
        print(json.dumps(response))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)