// static/js/circuit_simulation.js
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('python_code');
    const predefinedSelect = document.getElementById('predefined_circuit');
    const loadCircuitBtn = document.getElementById('loadCircuitBtn');
    const simulationForm = document.getElementById('simulationForm');
    const hardwareForm = document.getElementById('hardwareForm');
    const errorContainer = document.getElementById('errorContainer');
    const hardwarePythonCode = document.getElementById('hardware_python_code');
    const loadingIndicator = document.getElementById('loadingIndicator');

    console.log('Initial textarea value:', textarea.value);
    console.log('Textarea disabled:', textarea.disabled);
    console.log('Textarea readonly:', textarea.readOnly);

    textarea.disabled = false;
    textarea.readOnly = false;
    console.log('Textarea initialized, editable:', !textarea.disabled && !textarea.readOnly);

    textarea.addEventListener('input', function() {
        console.log('Textarea input detected, new value:', this.value);
        this.style.height = 'auto';
        this.style.height = `${this.scrollHeight}px`;
        hardwarePythonCode.value = this.value;
    });

    if (!textarea.value) {
        console.log('Textarea empty, setting default circuit');
        textarea.value = `from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\nqc.x(0)\nqc.measure(0, 0)`;
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
        hardwarePythonCode.value = textarea.value;
    }

    [simulationForm, hardwareForm].forEach(form => {
        form.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && event.target.id !== 'python_code') {
                event.preventDefault();
                console.log('Enter key submission prevented for', form.id);
            }
        });
    });

    simulationForm.addEventListener('submit', function() {
        console.log('Simulation form submitted, showing loading indicator');
        loadingIndicator.classList.remove('d-none');
    });

    loadCircuitBtn.addEventListener('click', function() {
        console.log('Load Circuit button clicked, selected value:', predefinedSelect.value);
        if (predefinedSelect.value === '') {
            console.log('Custom Python selected, skipping predefined load');
            textarea.value = `from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\nqc.x(0)\nqc.measure(0, 0)`;
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
            hardwarePythonCode.value = textarea.value;
            errorContainer.innerHTML = '';
            return;
        }

        const formData = new FormData(simulationForm);
        formData.append('load_predefined', 'true');

        fetch(window.location.href, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            console.log('Predefined circuit loaded successfully');
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTextarea = doc.getElementById('python_code');
            const newErrorContainer = doc.getElementById('errorContainer');

            textarea.value = newTextarea.value;
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
            errorContainer.innerHTML = newErrorContainer.innerHTML;
            hardwarePythonCode.value = textarea.value;
        })
        .catch(error => {
            console.error('Error loading predefined circuit:', error);
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444;">
                    <ul class="mb-0">
                        <li>Failed to load predefined circuit: ${error.message}. Please try again.</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        });
    });

    predefinedSelect.addEventListener('change', function() {
        console.log('Predefined circuit changed to:', this.value);
        errorContainer.innerHTML = '';
        if (this.value === '') {
            textarea.value = `from qiskit import QuantumCircuit\nqc = QuantumCircuit(1, 1)\nqc.x(0)\nqc.measure(0, 0)`;
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
            hardwarePythonCode.value = textarea.value;
        }
    });

    hardwareForm.addEventListener('submit', function(event) {
        console.log('Hardware form submission attempted, python_code:', textarea.value);
        const pythonCode = textarea.value;
        if (!pythonCode.includes('measure') && !pythonCode.includes('measure_all')) {
            event.preventDefault();
            console.log('Hardware submission blocked: missing measurements');
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show mb-4" role="alert" style="background: rgba(239, 68, 68, 0.2); border-color: #EF4444;">
                    <ul class="mb-0">
                        <li>Circuit must include measurements for hardware simulation. Add qc.measure() or qc.measure_all().</li>
                    </ul>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
        } else {
            console.log('Hardware form submitted with CSRF token');
        }
    });
});