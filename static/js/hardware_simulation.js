// static/js/hardware_simulation.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Hardware simulation script loaded'); // Debug log

    const textarea = document.getElementById('python_code');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
        document.getElementById('back_python_code').value = this.value;
    });

    if (textarea.value) {
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
    }

    const connectBtn = document.getElementById('connectBtn');
    const connectBtnText = document.getElementById('connectBtnText');
    const connectSpinner = document.getElementById('connectSpinner');
    const submitBtn = document.getElementById('submitBtn');
    const submitBtnText = document.getElementById('submitBtnText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const backendSelect = document.getElementById('backend');
    const errorContainer = document.getElementById('errorContainer');
    const connectionStatus = document.getElementById('connectionStatus');
    const resultsTab = document.getElementById('resultsTab');
    const resultsTabContent = document.getElementById('resultsTabContent');
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    // Get dynamic values from form data attributes
    const form = document.getElementById('hardwareSimulationForm');
    const fetchBackendsUrl = form.dataset.fetchBackendsUrl;
    const runSimulationUrl = form.dataset.runSimulationUrl;
    const connectBtnLabel = form.dataset.connectLabel;
    const submitBtnLabel = form.dataset.submitLabel;
    let isConnected = form.dataset.connected === 'true';

    form.addEventListener('submit', function(event) {
        event.preventDefault();
    });

    form.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
        }
    });

    connectBtn.addEventListener('click', function(event) {
        event.preventDefault();
        console.log('Connect button clicked'); // Debug log
        const token = document.getElementById('ibm_token').value.trim();
        if (!token) {
            errorContainer.innerHTML = `
                <div  class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>IBM Quantum token is required.</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            return;
        }

        connectBtn.disabled = true;
        connectBtnText.textContent = 'Connecting...';
        connectSpinner.classList.remove('d-none');

        const formData = new FormData();
        formData.append('ibm_token', token);
        formData.append('csrf_token', csrfToken);

        fetch(fetchBackendsUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => {
            console.log('Fetch backends response:', response.status); // Debug log
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            connectBtn.disabled = false;
            connectBtnText.textContent = connectBtnLabel;
            connectSpinner.classList.add('d-none');

            if (data.success) {
                backendSelect.innerHTML = '';
                data.backends.forEach(backend => {
                    const option = document.createElement('option');
                    option.value = backend[0];
                    option.text = backend[1];
                    backendSelect.appendChild(option);
                });
                submitBtn.disabled = false;
                isConnected = true;
                connectionStatus.innerHTML = '<span style="color: #22C55E;">Status: Connected</span>';
                errorContainer.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show mb-4" role="alert" style="background: rgba(34, 197, 94, 0.2); border-color: #22C55E; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>Successfully connected to IBM Quantum.</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            } else {
                isConnected = false;
                connectionStatus.innerHTML = '<span style="color: #EF4444;">Status: Not Connected</span>';
                errorContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>${data.message}</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        })
        .catch(error => {
            console.error('Fetch backends error:', error); // Debug log
            connectBtn.disabled = false;
            connectBtnText.textContent = connectBtnLabel;
            connectSpinner.classList.add('d-none');
            isConnected = false;
            connectionStatus.innerHTML = '<span style="color: #EF4444;">Status: Not Connected</span>';
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Failed to connect to IBM Quantum: ${error.message.includes('401') ? 'Invalid token. Please check and try again.' : error.message}</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
        });
    });

    submitBtn.addEventListener('click', function(event) {
        event.preventDefault();
        console.log('Submit button clicked'); // Debug log
        if (!isConnected) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Please connect to IBM Quantum first.</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            return;
        }

        const pythonCode = document.getElementById('python_code').value.trim();
        const simulatorType = document.getElementById('simulator_type').value;
        if (!pythonCode) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Please provide Python code to simulate.</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            return;
        }
        if (simulatorType === 'sampler' && !pythonCode.includes('measure') && !pythonCode.includes('measure_all')) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Circuit must include measurements for Sampler simulation. Add qc.measure() or qc.measure_all().</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            return;
        }

        submitBtn.disabled = true;
        submitBtnText.textContent = 'Submitting...';
        loadingSpinner.classList.remove('d-none');

        const backend = document.getElementById('backend').value;
        const shots = document.getElementById('shots').value;

        fetch(runSimulationUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                python_code: pythonCode,
                backend: backend,
                simulator_type: simulatorType,
                shots: shots,
                token: document.getElementById('ibm_token').value.trim()
            })
        })
        .then(response => {
            console.log('Run simulation response:', response.status); // Debug log
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`HTTP ${response.status}: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            submitBtn.disabled = false;
            submitBtnText.textContent = submitBtnLabel;
            loadingSpinner.classList.add('d-none');

            if (data.success) {
                resultsTab.innerHTML = `
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="circuit-tab" data-bs-toggle="tab" data-bs-target="#circuit" type="button" role="tab" aria-controls="circuit" aria-selected="true" style="color: var(--text-secondary); font-size: 1.1rem; padding: 0.75rem 1.5rem;">Circuit</button>
                    </li>`;
                resultsTabContent.innerHTML = `
                    <div class="tab-pane fade show active" id="circuit" role="tabpanel" aria-labelledby="circuit-tab">
                        <h3 class="mb-3" style="color: var(--text-primary); font-size: 1.25rem; font-weight: 500;">Circuit Diagram</h3>
                        <div class="d-flex justify-content-center">
                            <img src="data:image/png;base64,${data.circuit_diagram}" alt="Circuit Diagram" class="img-fluid rounded shadow-sm" style="max-width: 100%; max-height: 400px;">
                        </div>
                    </div>`;
                if (data.simulation_counts && data.histogram_sim) {
                    resultsTab.innerHTML += `
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="histogram-tab" data-bs-toggle="tab" data-bs-target="#histogram" type="button" role="tab" aria-controls="histogram" aria-selected="false" style="color: var(--text-secondary); font-size: 1.1rem; padding: 0.75rem 1.5rem;">Local Simulation</button>
                        </li>`;
                    resultsTabContent.innerHTML += `
                        <div class="tab-pane fade" id="histogram" role="tabpanel" aria-labelledby="histogram-tab">
                            <h3 class="mb-3" style="color: var(--text-primary); font-size: 1.25rem; font-weight: 500;">Ideal Simulation Histogram</h3>
                            <div class="d-flex justify-content-center">
                                <img src="data:image/png;base64,${data.histogram_sim}" alt="Histogram" class="img-fluid rounded shadow-sm" style="max-width: 100%; max-height: 400px;">
                            </div>
                            <h3 class="mb-3" style="color: var(--text-primary); font-size: 1.25rem; font-weight: 500;">Simulation Counts</h3>
                            <pre class="text-sm p-3 rounded" style="background: #111827; color: var(--text-secondary);">${JSON.stringify(data.simulation_counts, null, 2)}</pre>
                        </div>`;
                }
                errorContainer.innerHTML = `
                    <div class="alert alert-info alert-dismissible fade show mb-4" role="alert" style="background: rgba(59, 130, 246, 0.2); border-color: #3B82F6; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>Job submitted (ID: ${data.job_id}). Please wait, as it may be queued due to backend demand. Check <a href="https://quantum-computing.ibm.com/services/resources?tab=systems" target="_blank">IBM Quantum Dashboard</a> for status.</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                if (data.redirect) window.location.href = data.redirect;
            } else {
                let errorMessage = data.message || 'Unknown error occurred.';
                if (data.message.includes('Invalid token') || data.message.includes('Session not initialized')) {
                    errorMessage = 'Invalid IBM Quantum token or session expired. Please reconnect with a valid token.';
                    isConnected = false;
                    connectionStatus.innerHTML = '<span style="color: #EF4444;">Status: Not Connected</span>';
                    submitBtn.disabled = true;
                }
                errorContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>${errorMessage}</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        })
        .catch(error => {
            console.error('Run simulation error:', error); // Debug log
            submitBtn.disabled = false;
            submitBtnText.textContent = submitBtnLabel;
            loadingSpinner.classList.add('d-none');
            let errorMessage = error.message.includes('HTTP 500') ?
                'Server error occurred. Please try again or contact support.' :
                error.message.includes('HTTP 401') ?
                'Not connected to IBM Quantum. Please reconnect with a valid token.' :
                `Failed to submit job: ${error.message}`;
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>${errorMessage}</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
        });
    });

    window.addEventListener('load', function() {
        submitBtn.disabled = !isConnected;
        submitBtnText.textContent = submitBtnLabel;
        loadingSpinner.classList.add('d-none');
        connectBtnText.textContent = connectBtnLabel;
        connectSpinner.classList.add('d-none');
    });
});