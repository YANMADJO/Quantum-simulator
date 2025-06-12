document.addEventListener('DOMContentLoaded', function() {
    console.log('Hardware simulation script loaded');

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
        console.log('Connect button clicked');
        const token = document.getElementById('ibm_token').value.trim();
        if (!token || token.length < 10) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Please enter a valid IBM Quantum token (minimum 10 characters).</li>
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
            console.log('Fetch backends response:', response.status);
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
                    option.text = `${backend[1]} (${backend.num_qubits || 'N/A'} qubits, ${backend.pending_jobs || 'N/A'} jobs queued)`;
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
                    <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>${data.message}</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        })
        .catch(error => {
            console.error('Fetch backends error:', error);
            connectBtn.disabled = false;
            connectBtnText.textContent = connectBtnLabel;
            connectSpinner.classList.add('d-none');
            isConnected = false;
            connectionStatus.innerHTML = '<span style="color: #EF4444;">Status: Not Connected</span>';
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Failed to connect to IBM Quantum: ${error.message.includes('401') ? 'Invalid token. Please check and try again.' : error.message}</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
        });
    });

    submitBtn.addEventListener('click', function(event) {
        event.preventDefault();
        console.log('Submit button clicked');
        if (!isConnected) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
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
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
                    <ul class="mb-0">
                        <li>Please provide Python code to simulate.</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
            return;
        }
        if (simulatorType === 'sampler' && !pythonCode.match(/\b(measure|measure_all)\b/)) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
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
            console.log('Run simulation response:', response.status);
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
                errorContainer.innerHTML = `
                    <div class="alert alert-info alert-dismissible fade show mb-4" role="alert" style="background: rgba(59, 130, 246, 0.2); border-color: #3B82F6; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>Job submitted (ID: ${data.job_id}). Please enter this ID in the Hardware Results page to retrieve results.</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                if (data.redirect) window.location.href = data.redirect;
            } else {
                let errorMessage = data.message || 'Unknown error occurred';
                if (data.message.includes('Invalid token') || (data.error && data.error.includes('Session not initialized'))) {
                    errorMessage = 'Invalid IBM Quantum token or session expired. Please reconnect with a valid token.';
                    isConnected = false;
                    connectionStatus.innerHTML = '<span style="color: #EF4444;">Status: Not Connected</span>';
                    submitBtn.disabled = true;
                }
                errorContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
                        <ul class="mb-0">
                            <li>${errorMessage}</li>
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        })
        .catch(error => {
            console.error('Run simulation error:', error);
            submitBtn.disabled = false;
            submitBtnText.textContent = submitBtnLabel;
            loadingSpinner.classList.add('d-none');
            let errorMessage = error.message.includes('HTTP 500') ?
                'Server error occurred. Please try again or contact support.' :
                error.message.includes('HTTP 401') ?
                'Not connected to IBM Quantum. Please reconnect with a valid token.' :
                `Failed to submit job: ${error.message}`;
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 186, 0.2); border-color: #EF4444; font-size: 1rem;">
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