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
from . import utils, config, cache_utils

job_results_lock = Lock()
job_results = {}
image_cache = cache_utils.FileCache(cache_dir="cache/images", ttl=3600)

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
            backend_choices = [(b.name, f"{b.name} ({b.num_qubits} qubits, {b.status().pending_jobs} jobs queued)") for b in backends if b.status().operational]
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
        try:
            backend = self.service.backend(backend_name)
            if circuit.num_qubits > backend.num_qubits:
                return False, f"Circuit has {circuit.num_qubits} qubits, backend supports {backend.num_qubits}."
            return True, None
        except Exception as e:
            self.logger.error(f"Failed to validate circuit: {str(e)}")
            return False, f"Invalid backend: {str(e)}"

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

        circuit_image_id = str(uuid.uuid4())
        histogram_image_id = str(uuid.uuid4())
        image_cache.set(circuit_image_id, circuit_diagram)
        image_cache.set(histogram_image_id, histogram_sim)

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
                            hardware_histogram = utils.generate_histogram_image(counts_hw_formatted)
                            with job_results_lock:
                                job_results[job_id] = {
                                    'status': 'Completed',
                                    'hardware_counts': counts_hw_formatted,
                                    'counts_sim': counts_sim,
                                    'job_id': job_id,
                                    'queue_info': queue_info,
                                    'hardware_histogram': hardware_histogram,
                                    'program_type': 'sampler'
                                }
                                if hardware_histogram:
                                    image_cache.set(f'hardware_histogram_{job_id}', hardware_histogram)
                        else:
                            with job_results_lock:
                                job_results[job_id] = {'status': 'Failed', 'error': f'Job failed: {status}'}
                    except Exception as e:
                        with job_results_lock:
                            job_results[job_id] = {'status': 'Failed', 'error': str(e)}

                threading.Thread(target=monitor_job, daemon=True).start()

            else:  # estimator
                active_qubits = sorted(transpiled_hw._layout.final_index_layout())
                if len(active_qubits) < 2:
                    return False, "Transpiled circuit has fewer than 2 qubits."
                pauli_str = "I" * transpiled_hw.num_qubits
                qubit_indices = active_qubits[:2]
                pauli_list = list(pauli_str)
                for idx in qubit_indices:
                    pauli_list[idx] = "Z"
                pauli_str = "".join(pauli_list)
                observable = SparsePauliOp.from_list([(pauli_str, 1)], num_qubits=transpiled_hw.num_qubits)
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
                                    'queue_info': queue_info,
                                    'program_type': 'estimator'
                                }
                        else:
                            with job_results_lock:
                                job_results[job_id] = {'status': 'Failed', 'error': f'Job failed: {status}'}
                    except Exception as e:
                        with job_results_lock:
                            job_results[job_id] = {'status': 'Failed', 'error': str(e)}

                threading.Thread(target=monitor_estimator_job, daemon=True).start()

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
            self.logger.error(f"Simulation failed: {str(e)}")
            return False, utils.handle_simulation_errors(e)

    def check_job_status(self, job_id):
        """Check the status of a quantum job."""
        with job_results_lock:
            job_result = job_results.get(job_id, {'status': 'Pending'})

        if job_result['status'] == 'Pending' or job_result.get('status') not in ['Completed', 'Failed']:
            try:
                job = self.service.job(job_id)
                status = job.status()
                queue_info = self.get_queue_info(job.backend().name)
                job_result['queue_info'] = queue_info
                job_metadata = self.service._api_client.job_get(job_id)
                job_result['program_type'] = job_metadata['program']['id'].lower()

                if status == 'QUEUED':
                    job_result['status'] = 'On Queue'
                elif status == 'RUNNING':
                    job_result['status'] = 'Executing'
                elif status == 'DONE':
                    result_hw = job.result()
                    if job_result['program_type'] == 'sampler':
                        counts_hw = result_hw[0].data.c.get_counts()
                        counts_hw_formatted = {k: int(v) for k, v in counts_hw.items() if int(v) > 0}
                        job_result['hardware_counts'] = counts_hw_formatted
                        cached_histogram = image_cache.get(f'hardware_histogram_{job_id}')
                        if not cached_histogram:
                            cached_histogram = utils.generate_histogram_image(counts_hw_formatted)
                            if cached_histogram:
                                image_cache.set(f'hardware_histogram_{job_id}', cached_histogram)
                        job_result['hardware_histogram'] = cached_histogram
                        job_result['counts_sim'] = session.get('counts_sim')
                    elif job_result['program_type'] == 'estimator':
                        job_result['expectation_value'] = result_hw[0].data.evs
                    else:
                        raise ValueError(f"Unknown job type: {job_result['program_type']}")
                    job_result['status'] = 'Completed'
                else:
                    job_result['status'] = 'Failed'
                    job_result['error'] = f'Job failed with status: {status}'

                with job_results_lock:
                    job_results[job_id] = job_result
            except Exception as e:
                self.logger.error(f"Failed to retrieve job status for {job_id}: {str(e)}")
                job_result = {'status': 'Failed', 'error': f'Invalid job ID or access error: {str(e)}'}
                if "401" in str(e) or "Unauthorized" in str(e):
                    session.pop('ibm_token', None)
                    session.pop('backends', None)
                    session.modified = True
                with job_results_lock:
                    job_results[job_id] = job_result

        return job_result