import io
import base64
import logging
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram, circuit_drawer, plot_bloch_multivector, plot_state_qsphere, plot_state_city
from qiskit.quantum_info import DensityMatrix
from Quantum_simulator import config
from qiskit_aer.noise import NoiseModel, depolarizing_error

# Helper Functions
def suggest_similar_gate_name(undefined_name):
    import difflib
    possible_gates = config.SUPPORTED_GATES + ['barrier']
    matches = difflib.get_close_matches(undefined_name, possible_gates, n=1, cutoff=0.6)
    return f"Did you mean '{matches[0]}'?" if matches else f"Supported gates: {', '.join(config.SUPPORTED_GATES)}."

def transpile_circuit(circuit, target, optimization_level=1):
    try:
        return transpile(circuit, target, optimization_level=optimization_level)
    except Exception as e:
        logging.error(f"Transpilation failed: {e}")
        raise ValueError(f"Failed to transpile circuit: {str(e)}")

def figure_to_base64(fig):
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        return img_base64
    except Exception as e:
        logging.error(f"Failed to convert figure to base64: {e}")
        return ""

def generate_circuit_image(circuit):
    try:
        return figure_to_base64(circuit_drawer(circuit, output='mpl'))
    except Exception as e:
        logging.error(f"Failed to generate circuit image: {e}")
        return generate_placeholder_image("Failed to generate circuit diagram.")

def generate_histogram_image(counts):
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    plot_histogram(counts, ax=ax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def generate_bloch_image(statevector, num_qubits):
    try:
        if num_qubits <= config.MAX_QUBITS_FOR_BLOCH:
            return figure_to_base64(plot_bloch_multivector(statevector))
        else:
            return generate_placeholder_image("Bloch sphere visualization is only available for single-qubit states.\nUse density matrix or statevector visualization for multi-qubit states.")
    except Exception as e:
        logging.error(f"Failed to generate Bloch image: {e}")
        return generate_placeholder_image("Failed to generate Bloch sphere.")

def generate_density_matrix_image(statevector, num_qubits):
    try:
        if num_qubits > config.MAX_QUBITS_FOR_VISUALIZATION:
            return generate_placeholder_image("Density matrix visualization is only available for circuits with 5 or fewer qubits.")
        dm = DensityMatrix(statevector)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        real_matrix = dm.data.real
        im1 = ax1.imshow(real_matrix, cmap='viridis')
        ax1.set_title('Real Part')
        fig.colorbar(im1, ax=ax1)
        imag_matrix = dm.data.imag
        im2 = ax2.imshow(imag_matrix, cmap='viridis')
        ax2.set_title('Imaginary Part')
        fig.colorbar(im2, ax=ax2)
        plt.tight_layout()
        return figure_to_base64(fig)
    except Exception as e:
        logging.error(f"Failed to generate density matrix image: {e}")
        return generate_placeholder_image("Failed to generate density matrix.")

def generate_statevector_visualization(statevector, num_qubits):
    try:
        if num_qubits > config.MAX_QUBITS_FOR_VISUALIZATION:
            return generate_placeholder_image("Statevector visualization is only available for circuits with 5 or fewer qubits.")
        if num_qubits <= 5:
            fig = plot_state_qsphere(statevector)
        else:
            fig = plot_state_city(statevector)
        return figure_to_base64(fig)
    except Exception as e:
        logging.error(f"Failed to generate statevector visualization: {e}")
        return generate_placeholder_image("Failed to generate statevector visualization.")

def generate_placeholder_image(message):
    try:
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.text(0.5, 0.5, message, horizontalalignment='center', verticalalignment='center', wrap=True, fontsize=10, color='red')
        ax.axis('off')
        return figure_to_base64(fig)
    except Exception as e:
        logging.error(f"Failed to generate placeholder image: {e}")
        return ""

def compute_unitary(circuit):
    try:
        circuit_no_measure = circuit.copy()
        circuit_no_measure.remove_final_measurements()
        unitary_simulator = AerSimulator(method='unitary')
        job = unitary_simulator.run(transpile_circuit(circuit_no_measure, unitary_simulator))
        unitary = job.result().get_unitary()
        return np.array2string(unitary, precision=3, suppress_small=True)
    except Exception as e:
        logging.error(f"Unitary computation failed: {e}")
        return f"Could not compute unitary: {str(e)}"

def extract_pure_circuit(circuit):
    try:
        pure_circuit = circuit.copy()
        pure_circuit.remove_final_measurements()
        pure_ops = []
        for inst, qargs, cargs in pure_circuit.data:
            if not hasattr(inst, 'condition') or inst.condition is None:
                pure_ops.append((inst, qargs, cargs))
        new_circuit = QuantumCircuit(pure_circuit.num_qubits)
        for inst, qargs, cargs in pure_ops:
            new_circuit.append(inst, qargs, cargs)
        return new_circuit
    except Exception as e:
        logging.error(f"Failed to extract pure circuit: {e}")
        raise ValueError(f"Failed to extract pure circuit: {str(e)}")

def generate_learning_diagram(item_type, name):
    try:
        logging.debug(f"Processing {item_type} with name: '{name}'")
        qc = None
        valid_algorithms = [
            "Shor's Algorithm",
            "Grover's Algorithm",
            "Deutsch-Jozsa Algorithm",
            "Quantum Fourier Transform",
            "Quantum Phase Estimation"
        ]

        if item_type == 'gate':
            qc = QuantumCircuit(1) if name != "CNOT Gate (Controlled-NOT)" else QuantumCircuit(2)
            if name == "Hadamard Gate (H)":
                qc.h(0)
            elif name == "Pauli-X Gate (X)":
                qc.x(0)
            elif name == "Pauli-Z Gate (Z)":
                qc.z(0)
            elif name == "CNOT Gate (Controlled-NOT)":
                qc.cx(0, 1)
            else:
                logging.warning(f"Unknown gate: '{name}'")
                return generate_placeholder_image(f"No diagram available for {name}")
        else:  # algorithm
            if name not in valid_algorithms:
                logging.warning(f"Unknown algorithm: '{name}'")
                return generate_placeholder_image(f"No diagram available for {name}")
            if name == "Shor's Algorithm":
                from qiskit.circuit.library import QFT
                n_count = 4
                qc = QuantumCircuit(n_count + 1, n_count)
                qc.h(range(n_count))
                qc.x(n_count)
                for q in range(n_count):
                    for _ in range(2 ** q):
                        qc.cx(q, n_count)
                qc.append(QFT(n_count, inverse=True), range(n_count))
            elif name == "Grover's Algorithm":
                qc = QuantumCircuit(2, 2)
                qc.h([0, 1])
                qc.cz(0, 1)
                qc.h([0, 1])
                qc.x([0, 1])
                qc.cz(0, 1)
                qc.x([0, 1])
                qc.h([0, 1])
            elif name == "Deutsch-Jozsa Algorithm":
                qc = QuantumCircuit(3, 2)
                qc.h([0, 1])
                qc.x(2)
                qc.h(2)
                qc.cx(0, 2)
                qc.cx(1, 2)
                qc.h([0, 1])
            elif name == "Quantum Fourier Transform":
                qc = QuantumCircuit(3)
                qc.h(0)
                qc.cp(1.57, 0, 1)
                qc.h(1)
                qc.cp(0.785, 0, 2)
                qc.cp(1.57, 1, 2)
                qc.h(2)
            elif name == "Quantum Phase Estimation":
                qc = QuantumCircuit(3, 2)
                qc.h([0, 1])
                qc.x(2)
                qc.cp(1.57, 0, 2)
                qc.cp(3.14, 1, 2)
                qc.h([0, 1])

        if qc is None:
            logging.error(f"No circuit defined for {item_type} '{name}'")
            return generate_placeholder_image(f"No diagram available for {name}")

        diagram = generate_circuit_image(qc)
        return diagram or generate_placeholder_image(f"No diagram available for {name}")
    except Exception as e:
        logging.error(f"Failed to generate diagram for {item_type} '{name}': {str(e)}")
        return generate_placeholder_image(f"Error generating diagram for {name}")

def execute_circuit_code(python_code):
    try:
        local_vars = {}
        exec_globals = {"QuantumCircuit": QuantumCircuit}
        exec(python_code, exec_globals, local_vars)
        circuit = local_vars.get('qc')
        if not isinstance(circuit, QuantumCircuit):
            return None, "Python code must define a QuantumCircuit object named 'qc'. Example:\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(1)\nqc.x(0)"
        if circuit.num_qubits > config.MAX_QUBITS_FOR_VISUALIZATION:
            return None, f"Circuit has {circuit.num_qubits} qubits; maximum allowed is {config.MAX_QUBITS_FOR_VISUALIZATION}."
        if not circuit.data:
            return None, "Circuit has no operations. Add gates or measurements to simulate. Example: qc.x(0)"
        return circuit, None
    except TypeError as e:
        if "not iterable" in str(e) or "not an integer" in str(e):
            return None, f"TypeError: {str(e)}. Use a loop for qubit indices, e.g., 'for i in range(qc.num_qubits): qc.h(i)'."
        return None, f"TypeError: {str(e)}. Ensure gate arguments are valid."
    except NameError as e:
        undefined_name = str(e).split("'")[1]
        suggestion = f" Did you mean a Qiskit gate like 'h', 'x', or 'cx'? Example: qc.h(0)" if undefined_name.lower() != 'barrier' else "Use 'qc.barrier()' instead."
        return None, f"NameError: {undefined_name}.{suggestion}"
    except SyntaxError as e:
        return None, f"SyntaxError at line {e.lineno}: {e.msg}. Check for missing parentheses or indentation."
    except Exception as e:
        return None, f"Failed to execute code: {str(e)}. Ensure valid Qiskit syntax."

def generate_circuit_visualizations(circuit, counts=None):
    visualizations = {}
    try:
        fig = circuit_drawer(circuit, output='mpl', scale=0.7)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        visualizations['diagram'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        visualizations['diagram'] = None

    if counts:
        try:
            fig, ax = plt.subplots()
            plot_histogram(counts, ax=ax)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            visualizations['histogram'] = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            visualizations['histogram'] = None

    return visualizations

def run_local_simulation(circuit, shots, noise_prob=0.0):
    try:
        if shots < config.MIN_SHOTS or shots > config.MAX_SHOTS:
            return None, f"Shots must be between {config.MIN_SHOTS} and {config.MAX_SHOTS}."

        noise_model = NoiseModel()
        if noise_prob > 0:
            if not 0.0 <= noise_prob <= 1.0:
                return None, "Noise probability must be between 0.0 and 1.0."
            error_1q = depolarizing_error(noise_prob, 1)
            error_2q = depolarizing_error(noise_prob * 2, 2)
            noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'x', 'y', 'z', 't', 's', 'p'])
            noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'swap', 'cp', 'cy', 'cz'])

        simulator = AerSimulator(noise_model=noise_model)
        job = simulator.run(circuit, shots=shots)
        result = job.result()
        counts = result.get_counts()
        return counts, None
    except Exception as e:
        return None, f"Simulation failed: {str(e)}."

def handle_simulation_errors(exception):
    if isinstance(exception, TypeError):
        return f"TypeError: {str(exception)}. Ensure gate arguments are valid."
    elif isinstance(exception, NameError):
        undefined_name = str(exception).split("'")[1]
        suggestion = f" Did you mean a Qiskit gate like 'h', 'x', or 'cx'? Example: qc.h(0)" if undefined_name.lower() != 'barrier' else "Use 'qc.barrier()' instead."
        return f"NameError: {undefined_name}.{suggestion}"
    elif isinstance(exception, SyntaxError):
        return f"SyntaxError at line {exception.lineno}: {exception.msg}. Check syntax."
    else:
        return f"Error: {str(exception)}. Please check your circuit or parameters."

def qasm_to_python_code(circuit, circuit_name):
    python_code = f"from qiskit import QuantumCircuit\n# {circuit_name.replace('_', ' ').title()}\n"
    python_code += f"qc = QuantumCircuit({circuit.num_qubits}, {circuit.num_clbits})\n"
    for instruction in circuit.data:
        gate = instruction.operation.name
        qubits = [circuit.qubits.index(q) for q in instruction.qubits]
        clbits = [circuit.clbits.index(c) for c in instruction.clbits] if instruction.clbits else []
        params = instruction.operation.params
        if gate == 'measure':
            python_code += f"qc.measure({qubits}, {clbits})\n"
        elif gate in ['h', 'x', 'y', 'z', 's', 'sdg', 't', 'tdg', 'p']:
            python_code += f"qc.{gate}({qubits[0]})\n"
        elif gate in ['cx', 'cy', 'cz', 'swap']:
            python_code += f"qc.{gate}({qubits[0]}, {qubits[1]})\n"
        elif gate == 'cp':
            python_code += f"qc.cp({params[0]}, {qubits[0]}, {qubits[1]})\n"
    return python_code


