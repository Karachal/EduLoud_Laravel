import numpy as np
from scipy.special import jv
from scipy.special import struve
import mpmath as mp
import json
import sys
from functools import lru_cache

# Constants
SOUND_CELERITY = 343  # Speed of sound in air, m/s
R_0 = 1.18  # Air density, kg/m^3
P_0 = 10**5  # Atmospheric pressure, Pa
GAMMA = 1.4  # Adiabatic index
P_REF = 20 * 10 ** (-6)  # Reference sound pressure, Pa (20 µPa)
PI = np.pi

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

def complex_to_dict(z):
    """Convert a complex number to a dictionary with real and imaginary parts."""
    return {"real": np.real(z).item(), "imaginary": np.imag(z).item()}

class Loudspeaker:
    """Loudspeaker model with Thiele-Small parameters."""

    def __init__(self, lsp_par):
        """Initialize the loudspeaker object with unit conversions."""
        self.Re = lsp_par["re"]  # Voice coil resistance, Ω
        self.Le = lsp_par["le"] / 1000  # Convert from mH to H
        self.e_g = np.sqrt(self.Re)  # Input voltage, V
        self.Qes = lsp_par["qes"]  # Electrical Q factor
        self.Qms = lsp_par["qms"]  # Mechanical Q factor
        self.fs = lsp_par["fs"]  # Resonant frequency, Hz
        self.Vas = lsp_par["vas"] / 1000  # Convert from L to m³
        self.Cms = lsp_par["cms"] / 1000000  # Convert from µm/N to m/N
        self.Mms = lsp_par["mms"] / 1000  # Convert from g to kg
        self.Bl = lsp_par["bl"]  # Force factor, N/A
        self.Sd = lsp_par["sd"] / 10000  # Convert from cm² to m²
        self.a = np.sqrt(self.Sd / np.pi)  # Diaphragm radius, m
        self.Rms = lsp_par["rms"]  # Mechanical resistance, Ns/m

        # Derived parameters
        self.Qts = (self.Qes * self.Qms) / (self.Qes + self.Qms)  # Total Q factor
        self.Mmd = self.Mms - (16 * R_0 * self.a**3 / 3)  # Effective moving mass, kg

        # Precompute constants
        self.k_const = 2 * np.pi / SOUND_CELERITY
        self.R_f = self.calculate_R_f()  # Precompute R_f

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

class OpenAir:
    """Open air loudspeaker model."""

    def __init__(self, loudspeaker):
        self.loudspeaker = loudspeaker

    def calculate_impedance(self, f):
        omega = 2 * np.pi * f
        Zes = self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le
        Zem = self.loudspeaker.Bl**2 / self.loudspeaker.Rms * (
            1j / self.loudspeaker.Qms * f / self.loudspeaker.fs /
            (1 - f**2 / self.loudspeaker.fs**2 + 1j / self.loudspeaker.Qms * f / self.loudspeaker.fs)
        )
        Ze = Zes + Zem
        return np.abs(Ze)

    def calculate_spl(self, f):
        omega = 2 * PI * f
        k = omega / SOUND_CELERITY
        J1 = jv(1, 2 * k * self.loudspeaker.Sd)
        H1 = complex(mp.struveh(1, 2 * k * self.loudspeaker.a))
        
        Z_MT = (self.loudspeaker.Bl**2) / (self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le) + \
               1j * omega * self.loudspeaker.Mms + self.loudspeaker.Rms + 1 / (1j * omega * self.loudspeaker.Cms) + \
               2 * self.loudspeaker.Sd * R_0 * SOUND_CELERITY * (1 - J1/(k * self.loudspeaker.Sd) + 1j * H1/(k * self.loudspeaker.Sd))

        u_c = np.abs(self.loudspeaker.e_g * self.loudspeaker.Bl / ((self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le) * Z_MT))
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10(np.abs(p_rms) / P_REF)
        return SPL


class SealedBoxEnclosure:
    """Loudspeaker enclosure model for a sealed box."""
    
    def __init__(self, loudspeaker, lx, ly, lz):
        self.lsp = loudspeaker
        self.lx = lx * 0.01  # Convert cm to m
        self.ly = ly * 0.01  # Convert cm to m
        self.lz = lz * 0.01  # Convert cm to m
        self.Vb = self.lx * self.ly * self.lz  # Calculate Vb in m³

    def calculate_diaphragm_radiation_impedance(self, f):
        k = self.lsp.calculate_wave_number(f)
        H1 = complex(mp.struveh(1, 2 * k * self.lsp.a))
        R_sp = R_0 * SOUND_CELERITY * (1 - jv(1, 2 * k * self.lsp.a) / (k * self.lsp.a))
        X_sp = R_0 * SOUND_CELERITY * (H1 / (k * self.lsp.a))
        Z_a2 = R_sp + 1j * X_sp
        return Z_a2

    def calculate_simplified_box_impedance_Zab(self, f, B):
        """Calculate the simplified box impedance for circular loudspeaker using Vb."""
        # Calculate Va and Vm from Vb
        Va = (3 / 4) * self.Vb
        Vm = self.Vb / 4

        Mab = float(B) * R_0 / (np.pi * self.lsp.a)

        CAA = (Va) / (1.4 * P_0)
        CAM = (Vm) / P_0

        Xab = 2 * np.pi * f * Mab - 1 / (2 * np.pi * f * (CAA + CAM))

        Ram = R_0 * SOUND_CELERITY / (self.lx * self.ly)

        Rab = Ram / (
            (1 + Va / (1.4 * Vm)) ** 2 + (2 * np.pi * f) ** 2 * Ram**2 * CAA**2
        )

        Zab = 1 * (Rab + 1j * Xab)
        return Zab

    def calculate_impedance(self, f):
        """Calculate the system response."""
        # Calculate the electrical impedance
        Z_e = self.lsp.Re + 1j * 2 * np.pi * f * self.lsp.Le

        # Calculate the mechanical impedance
        Mmd = self.lsp.Mms - (16 * R_0 * self.lsp.a**3 / 3)
        Z_md = (
            1j * 2 * np.pi * f * Mmd
            + self.lsp.Rms
            + 1 / (1j * 2 * np.pi * f * self.lsp.Cms)
        )

        # Calculate the wave number k
        self.lsp.calculate_wave_number(f)

        # Calculate the diaphragm radiation impedance
        Z_a2 = self.calculate_diaphragm_radiation_impedance(f)

        # Calculate the simplified box impedance for circular loudspeaker
        Zab = self.calculate_simplified_box_impedance_Zab(f, B=0.46)

        # Transmission line matrices method (simplified for 1 speaker)
        C = np.array([[1, Z_e], [0, 1]])
        E = np.array([[0, self.lsp.Bl], [1 / self.lsp.Bl, 0]])
        D = np.array([[1, Z_md], [0, 1]])
        M = np.array([[self.lsp.Sd, 0], [0, 1 / self.lsp.Sd]])
        F = np.array([[1, Z_a2], [0, 1]])
        B = np.array([[1, 0], [1 / Zab, 1]])

        A = np.dot(np.dot(np.dot(np.dot(np.dot(C, E), D), M), F), B)

        a11 = A[0, 0]
        a21 = A[1, 0]
        Z_tot = a11 / a21
        
        # Return only the magnitude (as a float) for plotting purposes
        return float(abs(Z_tot))
    
    def calculate_spl(self, f):
        """Calculate the system response."""
        # Calculate the electrical impedance
        Z_e = self.lsp.Re + 1j * 2 * np.pi * f * self.lsp.Le

        # Calculate the mechanical impedance
        Mmd = self.lsp.Mms - (16 * R_0 * self.lsp.a**3 / 3)
        Z_md = (
            1j * 2 * np.pi * f * Mmd
            + self.lsp.Rms
            + 1 / (1j * 2 * np.pi * f * self.lsp.Cms)
        )

        # Calculate the wave number k
        self.lsp.calculate_wave_number(f)

        # Calculate the diaphragm radiation impedance
        Z_a2 = self.calculate_diaphragm_radiation_impedance(f)

        # Calculate the simplified box impedance for circular loudspeaker
        Zab = self.calculate_simplified_box_impedance_Zab(f, B=0.46)

        # Transmission line matrices method (simplified for 1 speaker)
        C = np.array([[1, Z_e], [0, 1]])
        E = np.array([[0, self.lsp.Bl], [1 / self.lsp.Bl, 0]])
        D = np.array([[1, Z_md], [0, 1]])
        M = np.array([[self.lsp.Sd, 0], [0, 1 / self.lsp.Sd]])
        F = np.array([[1, Z_a2], [0, 1]])
        B = np.array([[1, 0], [1 / Zab, 1]])

        A = np.dot(np.dot(np.dot(np.dot(np.dot(C, E), D), M), F), B)

        a11 = A[0, 0]
        a21 = A[1, 0]

        p_6 = self.lsp.e_g / a11
        U_c = p_6 / Zab

        # Calculate the system response
        U_ref = (self.lsp.e_g * self.lsp.Bl * self.lsp.Sd) / (
            2 * np.pi * f * self.lsp.Mms * self.lsp.Re
        )
        response = 20 * np.log10(float(np.abs(U_c)) / float(np.abs(U_ref)))

        # Calculate the system impedance
        Ze = np.abs(a11 / a21)

        # Calculate the power Lw
        Rmr = (
            (2 * np.pi * f) ** 2
            * (self.lsp.Sd) ** 2
            * R_0
        ) / (2 * np.pi * SOUND_CELERITY)
        W = (
            np.abs(U_c / (np.sqrt(2) * self.lsp.Sd)) ** 2
            * Rmr
        )
        W_ref = 10 ** (-12)
        power = 10 * np.log10(float(np.abs(W)) / float(np.abs(W_ref)))

        # Calculate the sound pressure level
        prms = R_0 * f * U_c
        pref = 20e-6
        SPL = 20 * np.log10(float(np.abs(prms)) / float(np.abs(pref)))

        return SPL

class PortedBoxEnclosure:
    """Ported (Bass Reflex) Loudspeaker Enclosure Model based on Beranek & Mellow."""

    def __init__(self, loudspeaker, lx, ly, lz, port_length, port_diameter):
        """
        Initialize the ported box enclosure.

        Parameters:
            loudspeaker: Loudspeaker object containing Thiele-Small parameters.
            Vb: Known box volume in liters.
            port_length: Length of the port (cm).
            port_diameter: Diameter of the port (cm).
        """
        self.loudspeaker = loudspeaker
        self.lx = lx * 0.01 #convert cm to m
        self.ly = ly * 0.01 #convert cm to m
        self.lz = lz * 0.01 #convert cm to m
        self.Vb = lx * ly * lz #Calculate Vb in m³
        self.port_length = port_length * 0.01  # Convert cm to meters
        self.port_diameter = port_diameter * 0.01  # Convert cm to meters
        self.Sp = np.pi * (self.port_diameter / 2) ** 2  # Port cross-sectional area (m²)
        self.V_input = np.sqrt(1 * self.loudspeaker.Re)  # 1W @ nominal impedance

    def calculate_helmholtz_resonance(self):
        """Calculate Helmholtz resonance frequency of the ported box."""
        L_eff = self.port_length + 1.7 * (self.port_diameter / 2)  # Effective length with end correction
        fb = (SOUND_CELERITY / (2 * np.pi)) * np.sqrt(self.Sp / (self.Vb * L_eff))
        return fb

    def calculate_impedance(self, f):
        """Calculate impedance of a ported loudspeaker enclosure."""
        omega = 2 * np.pi * f  # Angular frequency

        # Compute Helmholtz resonance parameters
        L_eff = self.port_length + 1.7 * (self.port_diameter / 2)  # Effective length with end correction
        M_port = R_0 * L_eff / self.Sp  # Mass reactance of port
        C_box = self.Vb / (GAMMA * P_0)  # Corrected air compliance

        # Compute Mechanical & Port Impedances
        Z_mech = (
            1j * omega * self.loudspeaker.Mms
            + self.loudspeaker.Rms
            + 1 / (1j * omega * self.loudspeaker.Cms)
        )
        Z_port = 1j * (omega * M_port - 1 / (omega * C_box))

        # Compute total impedance
        Z_total = self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le + (self.loudspeaker.Bl**2) / (Z_mech + Z_port)

        return np.abs(Z_total)

    def calculate_spl(self, f):
        """Calculate SPL for a ported loudspeaker enclosure at 1W/1m."""
        omega = 2 * np.pi * f  # Angular frequency

        # Compute Helmholtz resonance frequency
        fb = self.calculate_helmholtz_resonance()

        # Compute system Q-factor Qtp (ported box total Q factor)
        Qtp = self.loudspeaker.Qts * np.sqrt(self.loudspeaker.Vas / self.Vb)

        # Compute resonance frequency ratio (Eq. 7.54)
        a_B_f = (-f**2 / fb**2) / (1 - f**2 / fb**2 + 1j * (1 / Qtp) * (f / fb))

        # Compute nominal impedance (Z_nom)
        Z_nom = self.loudspeaker.Re * (1 + self.loudspeaker.Qes / self.loudspeaker.Qms)

        # Compute diaphragm and port velocity
        Z_mech = (
            1j * omega * self.loudspeaker.Mms
            + self.loudspeaker.Rms
            + 1 / (1j * omega * self.loudspeaker.Cms)
        )
        Z_port = 1j * (omega * (R_0 * self.port_length / self.Sp) - 1 / (omega * (self.Vb / (R_0 * SOUND_CELERITY**2))))
        Z_total = Z_mech + Z_port

        u_c = self.loudspeaker.e_g * self.loudspeaker.Bl / (
            (self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le) * Z_total
        )

        # Compute sound pressure at 1m (port + diaphragm)
        p_rms = R_0 * f * self.loudspeaker.Sd * np.abs(u_c)

        # Compute SPL using reference pressure (20 µPa)
        SPL = 20 * np.log10(p_rms / P_REF)

        return SPL

    def calculate_response(self, frequencies):
        """Calculate SPL and impedance over a range of frequencies."""
        spl = np.zeros_like(frequencies)
        impedance = np.zeros_like(frequencies)

        for i, f in enumerate(frequencies):
            spl[i] = self.calculate_spl(f)
            impedance[i] = self.calculate_impedance(f)

        return spl, impedance
    
def calculate_speaker_response(parameters):
    try:
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 800)

        loudspeaker = Loudspeaker(parameters)

        if scenario == "open_air":
            enclosure = OpenAir(loudspeaker)
            spl = [enclosure.calculate_spl(f) for f in frequencies]
            impedance = [enclosure.calculate_impedance(f) for f in frequencies]
            
        elif scenario == "sealed":
            enclosure = SealedBoxEnclosure(loudspeaker, parameters["lx"], parameters["ly"], parameters["lz"])
            spl = [enclosure.calculate_spl(f) for f in frequencies]
            impedance = [enclosure.calculate_impedance(f) for f in frequencies]
        elif scenario == "ported":
            enclosure = PortedBoxEnclosure(loudspeaker, parameters["lx"], parameters["ly"], parameters["lz"], parameters["port_length"], parameters["port_diameter"])
            spl = [enclosure.calculate_spl(f) for f in frequencies]
            impedance = [complex_to_dict(enclosure.calculate_impedance(f)) for f in frequencies]
        # spl = [enclosure.calculate_spl(f) for f in frequencies]
        # impedance = [enclosure.calculate_impedance(f) for f in frequencies]

        return {"frequencies": frequencies.tolist(), "spl": {scenario: spl}, "impedance": {scenario: impedance}}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    response = calculate_speaker_response(input_data)
    print(json.dumps(response))
