import numpy as np
from scipy.special import jv, hankel2, lpmv, spherical_jn, spherical_yn
from scipy.special import struve
from scipy.special import gamma, hyp2f1, binom, factorial
from scipy.integrate import quad
import mpmath as mp
import json
import sys

# Constants
SOUND_CELERITY = 344.8  # Speed of sound in air, m/s
R_0 = 1.18  # Air density, kg/m^3
P_0 = 10**5  # Atmospheric pressure, Pa
GAMMA = 1.4  # Adiabatic index
P_REF = 20 * 10 ** (-6)  # Reference sound pressure, Pa (20 µPa)
PI = np.pi

# Material properties for flow resistance
m = 1.86 * 10 ** (-5)  # Viscosity coefficient, N.s/m^2
R = 60 * 10 ** (-6)  # Fiber diameter, m
LM = 6 * 10 ** (-8) # Molecular mean free path length between collisions
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
        """Initialize the loudspeaker object with unit conversions."""
        self.Re = lsp_par["re"]  # Voice coil resistance, Ω
        self.Le = lsp_par["le"] / 1000  # Convert from mH to H
        self.Znom = lsp_par["z"] # Nominal Impedance, Ω
        self.e_g = np.sqrt(self.Znom) # Input voltage, V
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
        self.Rg = 0.75

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
        J1 = jv(1, 2 * k * self.loudspeaker.a)
        H1 = complex(mp.struveh(1, 2 * k * self.loudspeaker.a))
        
        Z_MT = (self.loudspeaker.Bl**2) / (self.loudspeaker.Rg + self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le) + \
               1j * omega * self.loudspeaker.Mmd + self.loudspeaker.Rms + 1 / (1j * omega * self.loudspeaker.Cms) + \
               2 * self.loudspeaker.Sd * R_0 * SOUND_CELERITY * (1 - J1/(k * self.loudspeaker.a) + 1j * H1/(k * self.loudspeaker.a))

        u_c = np.abs(self.loudspeaker.e_g * self.loudspeaker.Bl / ((self.loudspeaker.Rg + self.loudspeaker.Re + 1j * omega * self.loudspeaker.Le) * Z_MT))
        p_rms = R_0 * f * self.loudspeaker.Sd * u_c
        SPL = 20 * np.log10((p_rms) / P_REF)
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
        # Eq. 13.116 - 13.118
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

        # return SPL
        return SPL

class PortedBoxEnclosure:
    """Loudspeaker enclosure model for a ported box."""

    def __init__(self, loudspeaker, lx, ly, lz, port_length, port_section_aeria):
        self.lsp = loudspeaker
        self.lx = lx * 0.01  # Convert cm to m
        self.ly = ly * 0.01  # Convert cm to m
        self.lz = lz * 0.01  # Convert cm to m
        self.port_length = port_length * 0.01  # Convert cm to m
        self.port_section_aeria = port_section_aeria * 0.0001  # Convert cm² to m²
        self.truncation_limit = 5
        self.r = 0.15

        # Calculate box volume (Vb)
        self.Vb = self.lx * self.ly * self.lz  # Box volume in m³

        # Calculate port area (Sp) and port volume (Vp)
        self.Sp = self.port_section_aeria  # Port area in m²
        self.Vp = self.Sp * self.port_length  # Port volume in m³

        # Calculate effective box volume (Vab)
        self.Vab = self.Vb - self.Vp  # Effective box volume in m³

        # Initialize Va and Vm (if not provided, set to zero)
        self.Va = 0.0  # Volume of air in the box (if any)
        self.Vm = 0.0  # Volume of lining material (if any)

    def calculate_port(self):
        """Calculate the port parameters based on known port dimensions."""
        # Calculate the tuning frequency (fb) using Helmholtz resonator formula eq. 7.97
        fb = (SOUND_CELERITY / (2 * np.pi * self.port_length)) * np.sqrt(self.Vp / self.Vab)

        # Return port area (Sp), port length (t), and tuning frequency (fb)
        return self.Sp, self.port_length, fb

    def calculate_leakage_resistance(self):
        """Calculate the leakage resistance."""
        # Calculate compliance of the air in the box (CAA) and lining material (CAM)
        CAA = (self.Va) / (GAMMA * P_0)  # Compliance of the air in the box
        CAM = (self.Vm) / P_0  # Compliance of the air in the lining material
        Cab = CAA + GAMMA * CAM  # Apparent compliance of the air in the box

        # Calculate tuning frequency (fb)
        _, _, fb = self.calculate_port()

        # Calculate leakage resistance (Ral)
        Ral = 7 / (2 * np.pi * fb * Cab)
        return Ral
    
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
    
    def calculate_simplified_diaphragm_radiation_impedance(self, f, a):
        Rar = 0.01076 * f**2 #eq. 7.31
        Xar = 1.5 * f / a #eq. 7.32a
        Z_a1 = 1 * (Rar + 1j * Xar)

        return Z_a1
    def calculate_diaphragm_radiation_impedance(self, f):
        # Eq. 13.116 - 13.118
        k = self.lsp.calculate_wave_number(f)
        H1 = complex(mp.struveh(1, 2 * k * self.lsp.a))
        R_sp = R_0 * SOUND_CELERITY * (1 - jv(1, 2 * k * self.lsp.a) / (k * self.lsp.a))
        X_sp = R_0 * SOUND_CELERITY * (H1 / (k * self.lsp.a))
        Z_a2 = R_sp + 1j * X_sp
        return Z_a2    
    def calculate_port_impedance_Za2(self, f, r_d):
        """Calculate the rectangular port impedance based on equation 13.336 and 13.337."""
        q = self.lx / self.ly
        k = self.lsp.calculate_wave_number(f)

        Rs_a2 = (R_0 * SOUND_CELERITY) / (np.sqrt(np.pi))

        sum_Rs = 0
        sum_Xs = 0

        for m in range(self.truncation_limit + 1):
            for n in range(self.truncation_limit + 1):
                term1 = (-1) ** (m + n)
                term2 = (
                    (2 * m + 1)
                    * (2 * n + 1)
                    * factorial(m + 1)
                    * factorial(n + 1)
                    * gamma(m + n + 3 / 2)
                )
                term3 = (k * self.lx / 2) ** (2 * m + 1)
                term4 = (k * self.ly / 2) ** (2 * n + 1)
                sum_Rs += (term1 / term2) * term3 * term4

        Rs_a2 *= sum_Rs

        for m in range(self.truncation_limit + 1):
            term1 = (-1) ** m * self.fm(q, m)
            term2 = (2 * m + 1) * factorial(m) * factorial(m + 1)
            term3 = (k * self.lx / 2) ** (2 * m + 1)
            sum_Xs += (term1 / term2) * term3

        Xs_a2 = ((2 * r_d * SOUND_CELERITY) / (np.sqrt(np.pi))) * (
            (1 - np.sinc(k * self.lx)) / (q * k * self.lx)
            + (1 - np.sinc(q * k * self.lx)) / (k * self.lx)
            + sum_Xs
        )

        Z_a2 = (Rs_a2 + 1j * Xs_a2) / self.Sp

        return Z_a2

    def fm(self, q, m):
        """Helper function for the calculation of the rectangular port impedance based on equation 13.337."""
        result1 = hyp2f1(1, m + 0.5, m + 1.5, 1 / (1 + q**2))
        result2 = hyp2f1(1, m + 0.5, m + 1.5, 1 / (1 + q ** (-2)))

        sum_fm = 0
        for n in range(m + 1):
            sum_fm += self.gmn(m, n, q)

        return (result1 + result2) / ((2 * m + 1) * (1 + q ** (-2)) ** (m + 0.5)) + (
            1 / (2 * m + 3)
        ) * sum_fm

    def gmn(self, m, n, q):
        """Helper function for the calculation of the rectangular port impedance based on equation 13.337."""
        first_sum = 0

        for p in range(n, m + 1):
            first_sum += (
                ((-1) ** (p - n) * (q) ** (2 * n - 1))
                / ((2 * p - 1) * (1 + q**2) ** (p - 1 / 2))
                * binom((m - n), p - n)
            )

        first_term = binom((2 * m + 3), (2 * n)) * first_sum

        second_sum = 0

        for p in range(m - n, m + 1):
            second_sum += (
                binom((p - m + n), n) * (-1) ** (p - m + n) * (q) ** (2 * n + 2)
            ) / ((2 * p - 1) * (1 + q ** (-2)) ** (p - 1 / 2))

        second_term = binom((2 * m + 3), (2 * n + 3)) * second_sum

        return first_term + second_term
    
    # TEST WITH NOT SIMPLIFIED VERSIONS
    def integrand(self, thita, n, k):
        """Function to calculate the integrand"""
        r1 = (self.r * np.cos(self.lsp.a)) / np.cos(thita)
        hankel = spherical_jn(n, k * r1) - 1j * spherical_yn(n, k * r1)
        return (hankel) * lpmv(0, n, np.cos(thita)) * r1**2 * np.tan(thita)
    def calculate_circular_Za1(self, f):
        """Calculate the radiation impedance of a piston in a cap."""
        k = self.lsp.calculate_wave_number(f)
        alpha = np.arcsin(self.lsp.a / self.r)
        Z_a1 = (2 * R_0 * SOUND_CELERITY) / (self.r**2 * np.sin(alpha) ** 2)
        sum_n = 0
        for n in range(0, self.truncation_limit):
            if n == 0:
                An = (
                    1j
                    * k
                    * (-1)
                    * np.sin(alpha)
                    / (k * (-(1) * hankel2(1, k * self.r)))
                )
            elif n == 1:
                An = (
                    1j
                    * k
                    * (np.cos(alpha) ** 3 - 1)
                    / (
                        k
                        / (2 * 1 + 1)
                        * (
                            1 * hankel2(1 - 1, k * self.r)
                            - (1 + 1) * hankel2(1 + 1, k * self.r)
                        )
                    )
                )
            else:
                An = (
                    1j
                    * k
                    * (2 * n + 1)
                    * np.sin(alpha)
                    * (
                        np.sin(alpha) * lpmv(0, n, np.cos(alpha))
                        + np.cos(alpha) * lpmv(1, n, np.cos(alpha))
                    )
                    / (
                        2
                        * (n - 1)
                        * (n + 2)
                        * (
                            k
                            / (2 * n + 1)
                            * (
                                n * hankel2(n - 1, k * self.r)
                                - (n + 1) * hankel2(n + 1, k * self.r)
                            )
                        )
                    )
                )
            term3, _ = quad(self.integrand, 0, alpha, args=(n, k))
            sum_n += An * term3
        Z_a1 *= sum_n
        return Z_a1
    

    def calculate_impedance(self, f):    
        """Calculate the system response for a single speaker."""
        Sp, t, fb = self.calculate_port()
        ap = np.sqrt(Sp / np.pi)

        # Calculate the electrical impedance
        Z_e = self.lsp.Re + 1j * 2 * np.pi * f * self.lsp.Le

        # Calculate the mechanical impedance
        Mmd = self.lsp.Mms - 16 * R_0 * self.lsp.a**3 / 3
        Z_md = (
            1j * 2 * np.pi * f * Mmd
            + self.lsp.Rms
            + 1 / (1j * 2 * np.pi * f * self.lsp.Cms)
        )

        # Calculate the wave number k
        self.lsp.calculate_wave_number(f)

        # Calculate the simplified diaphragm radiation impedance
        # Z_a2 = self.calculate_simplified_diaphragm_radiation_impedance(f, ap)

        # Calculate the simplified box impedance for circular loudspeaker
        Zab = self.calculate_simplified_box_impedance_Zab(f, B=0.3)

        Z_a1 = self.calculate_diaphragm_radiation_impedance(f)
        #TEST INSTEAD Z_a3 with extensive type
        # Z_a1 = self.calculate_circular_Za1(f)

        # Calculate the leakage resistance
        Ral = self.calculate_leakage_resistance()

        # Calculate the port parameters
        ξ = 0.998 + 0.001j
        kp = (2 * np.pi * f * ξ) / SOUND_CELERITY
        Zp = (R_0 * SOUND_CELERITY * ξ) / Sp

        Kn = LM / ap
        Bu = (2 * 0.9 ** (-1) - 1) * Kn
        kv = np.sqrt((-1j * np.pi * 2 * f * R_0) / m)
        # Calculate the rectangular port impedance
        r_d = (-8 * R_0) / ((1 + 4 * Bu) * kv**2 * ap**2)  # Example value for r_d
        Z_a2 = self.calculate_port_impedance_Za2(f, r_d)

        # Transmission line matrices method
        C = np.array([[1, Z_e], [0, 1]])
        E = np.array([[0, self.lsp.Bl], [1 / self.lsp.Bl, 0]])
        D = np.array([[1, Z_md], [0, 1]])
        M = np.array([[self.lsp.Sd, 0], [0, 1 / self.lsp.Sd]])
        F = np.array([[1, Z_a1], [0, 1]])
        L = np.array([[1, 0], [1 / Ral, 1]])
        B = np.array([[1, 0], [1 / Zab, 1]])  # For simplified method
        P = np.array(
            [
                [np.cos(kp * t), 1j * Zp * np.sin(kp * t)],
                [1j * (1 / Zp) * np.sin(kp * t), np.cos(kp * t)],
            ]
        )
        R = np.array([[1, 0], [1 / Z_a2, 1]])

        A = np.dot(
            np.dot(
                np.dot(np.dot(np.dot(np.dot(np.dot(np.dot(C, E), D), M), F), L), B),
                P,
            ),
            R,
        )

        a11 = A[0, 0]
        a21 = A[1, 0]
        Z_tot = a11 / a21
        
        # Return only the magnitude (as a float) for plotting purposes
        return float(abs(Z_tot))
        
    
    def calculate_spl(self, f):
        """Calculate the system response for a single speaker."""
        Sp, t, fb = self.calculate_port()
        ap = np.sqrt(Sp / np.pi)

        # Calculate the electrical impedance
        Z_e = self.lsp.Re + 1j * 2 * np.pi * f * self.lsp.Le

        # Calculate the mechanical impedance
        Mmd = self.lsp.Mms - 16 * R_0 * self.lsp.a**3 / 3
        Z_md = (
            1j * 2 * np.pi * f * Mmd
            + self.lsp.Rms
            + 1 / (1j * 2 * np.pi * f * self.lsp.Cms)
        )

        # Calculate the wave number k
        self.lsp.calculate_wave_number(f)

        # Calculate the simplified diaphragm radiation impedance
        # Z_a2 = self.calculate_simplified_diaphragm_radiation_impedance(f, ap)

        # Calculate the simplified box impedance for circular loudspeaker
        Zab = self.calculate_simplified_box_impedance_Zab(f, B=0.3)

        Z_a1 = self.calculate_diaphragm_radiation_impedance(f)

        # Calculate the leakage resistance
        Ral = self.calculate_leakage_resistance()

        # Calculate the port parameters
        ξ = 0.998 + 0.001j
        kp = (2 * np.pi * f * ξ) / SOUND_CELERITY
        Zp = (R_0 * SOUND_CELERITY * ξ) / Sp

        Kn = LM / ap
        Bu = (2 * 0.9 ** (-1) - 1) * Kn
        kv = np.sqrt((-1j * np.pi * 2 * f * R_0) / m)
        # Calculate the rectangular port impedance
        r_d = (-8 * R_0) / ((1 + 4 * Bu) * kv**2 * ap**2)  # Example value for r_d
        Z_a2 = self.calculate_port_impedance_Za2(f, r_d)

        # Transmission line matrices method
        C = np.array([[1, Z_e], [0, 1]])
        E = np.array([[0, self.lsp.Bl], [1 / self.lsp.Bl, 0]])
        D = np.array([[1, Z_md], [0, 1]])
        M = np.array([[self.lsp.Sd, 0], [0, 1 / self.lsp.Sd]])
        F = np.array([[1, Z_a1], [0, 1]])
        L = np.array([[1, 0], [1 / Ral, 1]])
        B = np.array([[1, 0], [1 / Zab, 1]])  # For simplified method
        P = np.array(
            [
                [np.cos(kp * t), 1j * Zp * np.sin(kp * t)],
                [1j * (1 / Zp) * np.sin(kp * t), np.cos(kp * t)],
            ]
        )
        R = np.array([[1, 0], [1 / Z_a2, 1]])

        A = np.dot(
            np.dot(
                np.dot(np.dot(np.dot(np.dot(np.dot(np.dot(C, E), D), M), F), L), B),
                P,
            ),
            R,
        )

        a11 = A[0, 0]
        a21 = A[1, 0]

        p9 = self.lsp.e_g / a11
        Up = p9 / Z_a2

        N = np.dot(np.dot(B, P), R)
        n21 = N[1, 0]

        U6 = n21 * p9
        UB = (n21 - 1 / Z_a2) * p9

        # Calculate the system response
        U_ref = (self.lsp.e_g * self.lsp.Bl * self.lsp.Sd) / (
            2 * np.pi * f * self.lsp.Mms * self.lsp.Re
        )
        response = 20 * np.log10(float(abs(UB)) / float(abs(U_ref)))
        response_diaphragm = 20 * np.log10(float(abs(U6)) / float(abs(U_ref)))
        response_port = 20 * np.log10(float(abs(Up)) / float(abs(U_ref)))

        # Calculate the system impedance
        Ze = np.abs((a11) / (a21))

        # Calculate the power Lw
        Rmr = (
            (2 * np.pi * f) ** 2
            * (self.lsp.Sd) ** 2
            * R_0
        ) / (2 * np.pi * SOUND_CELERITY)
        W = (
            np.abs((UB) / (np.sqrt(2) * self.lsp.Sd)) ** 2
            * 1
            * Rmr
        )
        W_ref = 10 ** (-12)
        power = 10 * np.log10(float(W / W_ref))

        # Calculate the sound pressure level
        r_rms = R_0 * f * UB
        d_rms = R_0 * f * U6
        p_rms = R_0 * f * Up
        pref = 20e-6
        SPL = 20 * np.log10(float(abs(r_rms)) / float(abs(pref)))
        SPL_port = 20 * np.log10(float(abs(p_rms)) / float(abs(pref)))
        SPL_diaphragm = 20 * np.log10(float(abs(d_rms)) / float(abs(pref)))
        return SPL,  SPL_port, SPL_diaphragm
    
def calculate_speaker_response(parameters):
    try:
        scenario = parameters["scenario"]
        frequencies = np.logspace(np.log10(20), np.log10(20000), 500)

        loudspeaker = Loudspeaker(parameters)

        if scenario == "open_air":
            enclosure = OpenAir(loudspeaker)
            spl = [enclosure.calculate_spl(f) for f in frequencies]
            impedance = [enclosure.calculate_impedance(f) for f in frequencies]
            return {"frequencies": frequencies.tolist(), "spl": {scenario: spl}, "impedance": {scenario: impedance}}
            
        elif scenario == "sealed":
            enclosure = SealedBoxEnclosure(loudspeaker, parameters["lx"], parameters["ly"], parameters["lz"])
            spl = [enclosure.calculate_spl(f) for f in frequencies]
            impedance = [enclosure.calculate_impedance(f) for f in frequencies]
            return {"frequencies": frequencies.tolist(), "spl": {scenario: spl}, "impedance": {scenario: impedance}}
        
        elif scenario == "ported":
            port_diagram_response = parameters.get("port_diagram_response", False)

            enclosure = PortedBoxEnclosure(
                loudspeaker,
                parameters["lx"],
                parameters["ly"],
                parameters["lz"],
                parameters["port_length"],
                parameters["port_section_aeria"],
            )

            if port_diagram_response:
                # Get SPL, SPL_port, and SPL_diaphragm if the checkbox is checked
                spl, spl_port, spl_diaphragm = zip(*[enclosure.calculate_spl(f) for f in frequencies])
                impedance = [enclosure.calculate_impedance(f) for f in frequencies]

                return {
                    "frequencies": frequencies.tolist(),
                    "spl": {"ported": spl},
                    "spl_port": {"ported": spl_port},
                    "spl_diaphragm": {"ported": spl_diaphragm},
                    "impedance": {"ported": impedance},
                }
            else:
                # Default behavior if checkbox is NOT checked (return only SPL)
                spl = [enclosure.calculate_spl(f)[0] for f in frequencies]  # Take only the main SPL
                impedance = [enclosure.calculate_impedance(f) for f in frequencies]

                return {
                    "frequencies": frequencies.tolist(),
                    "spl": {"ported": spl},
                    "impedance": {"ported": impedance},
                }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    response = calculate_speaker_response(input_data)
    print(json.dumps(response))