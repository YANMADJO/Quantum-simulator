import os
# config.py

# NewsAPI Client
# NewsAPI key for fetching news articles. Register at https://newsapi.org/ to get your API key.
# Set it as an environment variable: export NEWSAPI_KEY='your_api_key_here'
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', 'Replace your API key')

# Gate mappings for user-friendly names to Qiskit gate names
GATE_MAPPINGS = {
    "hadamard": "h",
    "pauli_x": "x",
    "pauli_y": "y",
    "pauli_z": "z",
    "phase": "p",
    "cnot": "cx",
    "cy": "cy",
    "cz": "cz",
    "swap": "swap",
    "controlled_phase": "cp",
    "s": "s",
    "sdg": "sdg",
    "t": "t",
    "tdg": "tdg"
}

# Supported gates for circuit validation
PREDEFINED_CIRCUITS = {
            'bell_state': """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
        h q[0];
        cx q[0],q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];""",
            'phase_circuit': """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        cp(1.5708) q[0],q[1];
        """,
            'quantum_teleportation': """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg c[2];
        // Prepare entangled pair between q[1] and q[2]
        h q[1];
        cx q[1],q[2];
        // Prepare q[0] (state to teleport)
        h q[0];
        // Bell measurement on q[0] and q[1]
        cx q[0],q[1];
        h q[0];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        // Conditional operations on q[2] based on measurement (classical control not supported in QASM, so apply directly for simulation)
        cx q[1],q[2];
        cz q[0],q[2];
        """,
            'shor_factor_15': """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[9];
        creg c[4];
        h q[0];
        h q[1];
        h q[2];
        h q[3];
        cx q[0],q[4];
        cx q[0],q[5];
        cp(1.5708) q[0],q[6];
        cx q[1],q[5];
        cx q[1],q[6];
        cp(1.5708) q[1],q[7];
        cx q[2],q[6];
        cx q[2],q[7];
        cp(1.5708) q[2],q[4];
        cx q[3],q[7];
        cx q[3],q[4];
        cp(1.5708) q[3],q[5];
        h q[3];
        cp(-pi/2) q[2],q[3];
        h q[2];
        cp(-pi/4) q[1],q[3];
        cp(-pi/2) q[1],q[2];
        h q[1];
        cp(-pi/8) q[0],q[3];
        cp(-pi/4) q[0],q[2];
        cp(-pi/2) q[0],q[1];
        h q[0];
        swap q[0],q[3];
        swap q[1],q[2];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        measure q[2] -> c[2];
        measure q[3] -> c[3];
        """,
            "grover_2qubit": """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
        h q[0];
        h q[1];
        x q[0];
        x q[1];
        h q[1];
        cx q[0],q[1];
        h q[1];
        x q[0];
        x q[1];
        h q[0];
        h q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        """,
            "deutsch_jozsa": """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg c[2];
        h q[0];
        h q[1];
        x q[2];
        h q[2];
        cx q[0],q[2];
        cx q[1],q[2];
        h q[0];
        h q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        """,
            "quantum_fourier_transform": """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg c[3];
        h q[0];
        cp(pi/2) q[1],q[0];
        h q[1];
        cp(pi/4) q[2],q[0];
        cp(pi/2) q[2],q[1];
        h q[2];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        measure q[2] -> c[2];
        """,
            "quantum_phase_estimation": """OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        creg c[2];
        h q[0];
        h q[1];
        x q[2];
        cp(1.57) q[0],q[2];
        cp(3.14) q[1],q[2];
        h q[0];
        h q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        """
        }
# Learning gates for educational pages
LEARNING_GATES = [
    {
        "name": "Hadamard Gate (H)",
        "description": "Creates superposition by transforming |0⟩ to (|0⟩ + |1⟩)/√2 and |1⟩ to (|0⟩ - |1⟩)/√2.",
        "matrix": "1/√2 [[1, 1], [1, -1]]",
        "use_cases": ["Creating superposition", "Quantum Fourier Transform", "Randomized algorithms"],
        "qiskit_code": "qc.h(0)"
    },
    {
        "name": "Pauli-X Gate (X)",
        "description": "Acts as a quantum NOT gate, flipping |0⟩ to |1⟩ and |1⟩ to |0⟩.",
        "matrix": "[[0, 1], [1, 0]]",
        "use_cases": ["Bit flip", "Initialization", "Error correction"],
        "qiskit_code": "qc.x(0)"
    },
    {
        "name": "Pauli-Z Gate (Z)",
        "description": "Introduces a phase flip, leaving |0⟩ unchanged and mapping |1⟩ to -|1⟩.",
        "matrix": "[[1, 0], [0, -1]]",
        "use_cases": ["Phase flip", "Phase kickback", "Quantum algorithms"],
        "qiskit_code": "qc.z(0)"
    },
    {
        "name": "CNOT Gate (Controlled-NOT)",
        "description": "Flips the target qubit if the control qubit is |1⟩; otherwise, does nothing.",
        "matrix": "[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]",
        "use_cases": ["Entanglement", "Quantum circuits", "Error correction"],
        "qiskit_code": "qc.cx(0, 1)"
    }
]

# Learning algorithms for educational pages
LEARNING_ALGORITHMS = [
    {
        "name": "Shor's Algorithm",
        "description": "Efficiently factors large integers, with implications for cryptography.",
        "use_cases": ["Cryptography", "Number theory"],
        "qiskit_code": """
                        from qiskit import QuantumCircuit
                        from qiskit.circuit.library import QFT
                        n_count = 4
                        qc = QuantumCircuit(n_count + 1, n_count)
                        qc.h(range(n_count))
                        qc.x(n_count)
                        for q in range(n_count):
                            for _ in range(2 ** q):
                                qc.cx(q, n_count)
                        qc.append(QFT(n_count, inverse=True), range(n_count))
"""
    },
    {
        "name": "Grover's Algorithm",
        "description": "Provides a quadratic speedup for unstructured search problems.",
        "use_cases": ["Search problems", "Optimization"],
        "qiskit_code": """
                        from qiskit import QuantumCircuit
                        qc = QuantumCircuit(2, 2)
                        qc.h([0, 1])
                        qc.cz(0, 1)
                        qc.h([0, 1])
                        qc.x([0, 1])
                        qc.cz(0, 1)
                        qc.x([0, 1])
                        qc.h([0, 1])
                        """
    },
    {
        "name": "Deutsch-Jozsa Algorithm",
        "description": "Determines if a function is constant or balanced with one query.",
        "use_cases": ["Function evaluation", "Quantum advantage demonstration"],
        "qiskit_code": """
                        from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3, 2)
                        qc.h([0, 1])
                        qc.x(2)
                        qc.h(2)
                        qc.cx(0, 2)
                        qc.cx(1, 2)
                        qc.h([0, 1])
                        """
    },
    {
        "name": "Quantum Fourier Transform",
        "description": "Performs a quantum analogue of the discrete Fourier transform.",
        "use_cases": ["Shor's algorithm", "Phase estimation"],
        "qiskit_code": """
                        from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3)
                        qc.h(0)
                        qc.cp(1.57, 0, 1)
                        qc.h(1)
                        qc.cp(0.785, 0, 2)
                        qc.cp(1.57, 1, 2)
                        qc.h(2)
                        """
    },
    {
        "name": "Quantum Phase Estimation",
        "description": "Estimates the phase of an eigenvalue of a unitary operator.",
        "use_cases": ["Quantum simulation", "Shor's algorithm"],
        "qiskit_code": """
                        from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3, 2)
                        qc.h([0, 1])
                        qc.x(2)
                        qc.cp(1.57, 0, 2)
                        qc.cp(3.14, 1, 2)
                        qc.h([0, 1])
                        """
    }
]

# Simulation parameters
DEFAULT_NOISE_PROB = 0.01
DEFAULT_SHOTS = 1024
MAX_QUBITS_FOR_BLOCH = 1
MAX_QUBITS_FOR_VISUALIZATION = 9
MIN_SHOTS = 1
MAX_SHOTS = 10000
MAX_QUBITS_FOR_STATEVECTOR = 10
MAX_QUBITS_FOR_UNITARY = 5
SIMULATION_TIMEOUT_SECONDS = 30

# Default Python code for simulation forms
DEFAULT_PYTHON_CODE = """
from qiskit import QuantumCircuit
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])
"""

# Learning Data
LEARNING_GATES = [
    {
        'name': "Hadamard Gate (H)",
        'description': "The Hadamard gate creates superposition by transforming a qubit into an equal superposition of |0⟩ and |1⟩. It’s like flipping a coin to be both heads and tails at once until measured.",
        'use_cases': ["Creating superposition in algorithms like Deutsch-Jozsa", "Initializing qubits for quantum algorithms"],
        'matrix': r"\frac{1}{\sqrt{2}} \begin{bmatrix} 1 & 1 \\ 1 & -1 \end{bmatrix}",
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(1)
                        qc.h(0)
                        print(qc)"""
    },
    {
        'name': "Pauli-X Gate (X)",
        'description': "The Pauli-X gate acts like a quantum NOT gate, flipping a qubit from |0⟩ to |1⟩ or vice versa. It’s the quantum equivalent of a classical bit flip.",
        'use_cases': ["Flipping qubit states in algorithms like Grover’s", "Error correction in quantum codes"],
        'matrix': r"\begin{bmatrix} 0 & 1 \\ 1 & 0 \end{bmatrix}",
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(1)
                        qc.x(0)
                        print(qc)"""
    },
    {
        'name': "Pauli-Z Gate (Z)",
        'description': "The Pauli-Z gate applies a phase flip, leaving |0⟩ unchanged and mapping |1⟩ to -|1⟩. It’s used to introduce phase differences in quantum states.",
        'use_cases': ["Phase manipulation in quantum algorithms", "Error correction in quantum codes"],
        'matrix': r"\begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix}",
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(1)
                        qc.z(0)
                        print(qc)"""
    },
    {
        'name': "CNOT Gate (Controlled-NOT)",
        'description': "The CNOT gate is a two-qubit gate that flips the target qubit if the control qubit is |1⟩. It’s essential for creating entanglement between qubits.",
        'use_cases': ["Creating entanglement in Bell states", "Used in quantum teleportation and superdense coding"],
        'matrix': r"\begin{bmatrix} 1 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{bmatrix}",
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(2)
                        qc.cx(0, 1)
                        print(qc)"""
    }
]

# List of supported gates for error messages
SUPPORTED_GATES = ['h', 'x', 'y', 'z', 's', 'sdg', 't', 'tdg', 'p', 'cx', 'cy', 'cz', 'swap', 'cp', 'measure']

LEARNING_ALGORITHMS = [
    {
        'name': "Shor's Algorithm",
        'description': "Shor's Algorithm efficiently factors large integers, which could break classical encryption methods like RSA. It uses quantum period finding with modular exponentiation and the quantum Fourier transform to achieve exponential speedup over classical algorithms.",
        'use_cases': ["Breaking RSA encryption", "Driving research into post-quantum cryptography"],
        'qiskit_code': """from qiskit import QuantumCircuit
                        from qiskit.circuit.library import QFT
                        # Simplified Shor's for N=15, a=7
                        n_count = 4  # Number of counting qubits
                        qc = QuantumCircuit(n_count + 4, n_count)  # Adjusted for modular exponentiation
                        qc.h(range(n_count))  # Superposition on counting qubits
                        qc.x(n_count)  # Initialize work qubit to |1>
                        # Simplified modular exponentiation for a=7, N=15
                        for q in range(n_count):
                            for _ in range(2 ** q):
                                # Controlled modular multiplication (simplified)
                                qc.cx(q, n_count + 1)
                                qc.cx(q, n_count + 2)
                        qc.append(QFT(n_count, inverse=True), range(n_count))  # Inverse QFT
                        qc.measure(range(n_count), range(n_count))  # Measure counting qubits
                        print(qc)"""
    },
    {
        'name': "Grover's Algorithm",
        'description': "Grover’s Algorithm provides a quadratic speedup for unstructured search problems. It uses an oracle to mark the target state and a diffusion operator to amplify its probability, finding a marked item in O(√N) steps.",
        'use_cases': ["Database search optimization", "Solving NP-complete problems more efficiently"],
        'qiskit_code': """from qiskit import QuantumCircuit
                        # 2-qubit Grover's for searching |11>
                        qc = QuantumCircuit(2, 2)
                        # Initialize superposition
                        qc.h([0, 1])
                        # Oracle for |11>
                        qc.cz(0, 1)  # Marks |11> (simplified oracle)
                        # Diffusion operator
                        qc.h([0, 1])
                        qc.x([0, 1])
                        qc.cz(0, 1)
                        qc.x([0, 1])
                        qc.h([0, 1])
                        # Measure
                        qc.measure([0, 1], [0, 1])
                        print(qc)"""
    },
    {
        'name': "Deutsch-Jozsa Algorithm",
        'description': "The Deutsch-Jozsa Algorithm determines whether a function is constant or balanced with a single query, compared to multiple queries classically. It showcases quantum parallelism.",
        'use_cases': ["Demonstrating quantum advantage", "Testing quantum hardware capabilities"],
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3, 2)
                        qc.h([0, 1])
                        qc.x(2)
                        qc.h(2)
                        qc.cx(0, 2)
                        qc.cx(1, 2)
                        qc.h([0, 1])
                        qc.measure([0, 1], [0, 1])
                        print(qc)"""
    },
    {
        'name': "Quantum Fourier Transform",
        'description': "The Quantum Fourier Transform is the quantum analog of the classical Fourier transform. It’s a key component in algorithms like Shor’s, enabling efficient periodicity detection.",
        'use_cases': ["Period finding in Shor’s Algorithm", "Signal processing in quantum systems"],
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3)
                        qc.h(0)
                        qc.cp(1.57, 0, 1)
                        qc.h(1)
                        qc.cp(0.785, 0, 2)
                        qc.cp(1.57, 1, 2)
                        qc.h(2)
                        print(qc)"""
    },
    {
        'name': "Quantum Phase Estimation",
        'description': "Quantum Phase Estimation estimates the phase (eigenvalue) of an eigenvector of a unitary operator. It’s a key subroutine in many quantum algorithms, including Shor’s.",
        'use_cases': ["Phase estimation in Shor’s Algorithm", "Quantum simulation of physical systems"],
        'qiskit_code': """from qiskit import QuantumCircuit
                        qc = QuantumCircuit(3, 2)
                        qc.h([0, 1])
                        qc.x(2)  # Eigenstate |1> for a simple unitary
                        qc.cp(1.57, 0, 2)  # Controlled-U
                        qc.cp(3.14, 1, 2)  # Controlled-U^2
                        qc.h([0, 1])  # Inverse QFT (simplified)
                        qc.measure([0, 1], [0, 1])
                        print(qc)"""
    }
]

