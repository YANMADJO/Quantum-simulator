import uuid
import threading
import time
import logging
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerOptions, EstimatorOptions
from qiskit_ibm_runtime import SamplerV2 as Sampler, EstimatorV2 as Estimator
from qiskit.quantum_info import SparsePauliOp
from flask import session, jsonify
from threading import Lock
from . import utils, config

job_results_lock = Lock()
job_results = {}
image_cache = {}


class HardwareSimulationHandler:
    def __init__(self, token=None):
        self.service = None
        self.token = token
        self.logger = logging.getLogger(__name__)

    def connect_to_ibm_quantum(self, token):
        """Connect to IBM Quantum and retrieve operational backends."""
        try:
            self.service = QiskitRuntimeService(channel="ibm_quantum", token=token.strip())
            backends = self.service.backends()
            backend_choices = [(b.name, b.name) for b in backends if b.status().operational]
            if not backend_choices:
                return False, "No operational backends available."
            session['backends'] = backend_choices
            session['ibm_token'] = token
            session.modified = True
            return True, backend_choices
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to connect to IBM Quantum: {error_msg}")
            if "401" in error_msg or "Unauthorized" in error_msg:
                return False, "Invalid IBM Quantum token."
            return False, utils.handle_simulation_errors(e)

    def validate_circuit(self, circuit, backend_name):
        """Validate circuit against backend constraints."""
        backend = self.service.backend(backend_name)
        if circuit.num_qubits > backend.num_qubits:
            return False, f"Circuit has {circuit.num_qubits} qubits, backend supports {backend.num_qubits}."
        return True, None

    def get_queue_info(self, backend_name):
        """Retrieve queue information for a backend."""
        queue_info = {'position': None, 'estimated_wait_seconds': None}
        try:
            backend = self.service.backend(backend_name)
            backend_status = backend.status()
            queue_info['position'] = backend_status.pending_jobs
            queue_info['estimated_wait_seconds'] = queue_info['position'] * 10
        except Exception as e:
            self.logger.warning(f"Failed to retrieve backend status: {str(e)}")
        return queue_info

    def run_simulation(self, circuit, backend_name, shots, simulator_type, python_code):
        """Run hardware simulation (Sampler or Estimator)."""
        if not self.service:
            return False, "Not connected to IBM Quantum."

        valid, error = self.validate_circuit(circuit, backend_name)
        if not valid:
            return False, error

        # Generate visualizations
        visualizations = utils.generate_circuit_visualizations(circuit)
        circuit_diagram = visualizations.get('diagram')
        if not circuit_diagram:
            return False, "Failed to generate circuit diagram."

        counts_sim, error = utils.run_local_simulation(circuit, shots)
        if error:
            return False, error
        histogram_sim = utils.generate_histogram_image(counts_sim)
        if not histogram_sim:
            return False, "Failed to generate histogram."

        # Store images in cache
        circuit_image_id = str(uuid.uuid4())
        histogram_image_id = str(uuid.uuid4())
        image_cache[circuit_image_id] = circuit_diagram
        image_cache[histogram_image_id] = histogram_sim

        try:
            backend = self.service.backend(backend_name)
            transpiled_hw = utils.transpile_circuit(circuit, backend)
            queue_info = self.get_queue_info(backend_name)

            if simulator_type == 'sampler':
                if not any(i.operation.name == 'measure' for i in circuit.data):
                    return False, "Circuit must include measurements for Sampler."
                options = SamplerOptions()
                options.dynamical_decoupling.enable = True
                options.dynamical_decoupling.sequence_type = "XY4"
                sampler = Sampler(mode=backend, options=options)
                job = sampler.run([(transpiled_hw, None, None)], shots=shots)
                job_id = job.job_id()

                def monitor_job():
                    try:
                        status = job.status()
                        while status not in ['DONE', 'CANCELLED', 'ERROR']:
                            time.sleep(5)
                            status = job.status()
                        if status == 'DONE':
                            result_hw = job.result()
                            counts_hw = result_hw[0].data.c.get_counts()
                            counts_hw_formatted = {k: int(v) for k, v in counts_hw.items() if int(v) > 0}
                            hardware_histogram = utils.generate_histogram_image(
                                counts_hw_formatted)  # Generate histogram
                            with job_results_lock:
                                job_results[job_id] = {
                                    'status': 'Completed',
                                    'hardware_counts': counts_hw_formatted,
                                    'counts_sim': counts_sim,
                                    'job_id': job_id,
                                    'queue_info': queue_info,
                                    'hardware_histogram': hardware_histogram  # Store histogram
                                }
                                if hardware_histogram:
                                    image_cache[f'hardware_histogram_{job_id}'] = hardware_histogram  # Cache it
                        else:
                            with job_results_lock:
                                job_results[job_id] = {'status': 'Failed', 'error': f'Job failed: {status}'}
                    except Exception as e:
                        with job_results_lock:
                            job_results[job_id] = {'status': 'Failed', 'error': str(e)}

                threading.Thread(target=monitor_job).start()

            else:  # estimator
                observable = SparsePauliOp.from_list([(f"Z{'Z' * (i + 1)}", 1) for i in range(circuit.num_qubits - 1)])
                options = EstimatorOptions()
                options.resilience_level = 1
                estimator = Estimator(mode=backend, options=options)
                job = estimator.run([(transpiled_hw, observable, None)])
                job_id = job.job_id()

                def monitor_estimator_job():
                    try:
                        status = job.status()
                        while status not in ['DONE', 'CANCELLED', 'ERROR']:
                            time.sleep(5)
                            status = job.status()
                        if status == 'DONE':
                            result_hw = job.result()
                            with job_results_lock:
                                job_results[job_id] = {
                                    'status': 'Completed',
                                    'expectation_value': result_hw[0].data.evs,
                                    'job_id': job_id,
                                    'queue_info': queue_info
                                }
                        else:
                            with job_results_lock:
                                job_results[job_id] = {'status': 'Failed', 'error': f'Job failed: {status}'}
                    except Exception as e:
                        with job_results_lock:
                            job_results[job_id] = {'status': 'Failed', 'error': str(e)}

                threading.Thread(target=monitor_estimator_job).start()

            # Update session
            session['current_job_id'] = job_id
            session['circuit_image_id'] = circuit_image_id
            session['histogram_image_id'] = histogram_image_id
            session['counts_sim'] = counts_sim
            session['python_code'] = python_code
            session.modified = True

            return True, {
                'mode': simulator_type,
                'job_id': job_id,
                'circuit_diagram': circuit_diagram,
                'simulation_counts': counts_sim,
                'histogram_sim': histogram_sim,
                'redirect': '/hardware_results'
            }

        except Exception as e:
            return False, utils.handle_simulation_errors(e)

    def check_job_status(self, job_id):
        """Check the status of a quantum job."""
        with job_results_lock:
            job_result = job_results.get(job_id, {'status': 'Pending'})

        if job_result['status'] == 'Pending':
            try:
                job = self.service.job(job_id)
                status = job.status()
                queue_info = self.get_queue_info(job.backend().name)
                job_result['queue_info'] = queue_info
                if status == 'QUEUED':
                    job_result['status'] = 'On Queue'
                elif status == 'RUNNING':
                    job_result['status'] = 'Executing'
                elif status == 'DONE':
                    result_hw = job.result()
                    if 'counts_sim' in job_result:  # Sampler job
                        counts_hw = result_hw[0].data.c.get_counts()
                        counts_hw_formatted = {k: int(v) for k, v in counts_hw.items() if int(v) > 0}
                        job_result['hardware_counts'] = counts_hw_formatted
                        # Regenerate histogram if not present
                        if 'hardware_histogram' not in job_result or job_result['hardware_histogram'] is None:
                            job_result['hardware_histogram'] = utils.generate_histogram_image(counts_hw_formatted)
                            if job_result['hardware_histogram']:
                                image_cache[f'hardware_histogram_{job_id}'] = job_result['hardware_histogram']
                    else:  # Estimator job
                        job_result['expectation_value'] = result_hw[0].data.evs
                    job_result['status'] = 'Completed'
            except Exception as e:
                job_result = {'status': 'Failed', 'error': str(e)}
                if "401" in str(e) or "Unauthorized" in str(e):
                    session.pop('ibm_token', None)
                    session.pop('backends', None)
                    session.modified = True
        return job_result

