import os
import time
import logging
import threading
import uuid
from threading import Lock
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import bcrypt
import arxiv
try:
    from newsapi import NewsApiClient
except ImportError:
    NewsApiClient = None
from qiskit import QuantumCircuit, transpile
from qiskit.qasm2 import dumps as qasm2_dumps
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.visualization import plot_histogram
from qiskit.quantum_info import SparsePauliOp
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerOptions, EstimatorOptions
from qiskit_ibm_runtime import SamplerV2 as Sampler, EstimatorV2 as Estimator
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from flask_caching import Cache
from Quantum_simulator import database, config, forms, utils, hardware_utils

# Application Configuration
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('qiskit').setLevel(logging.WARNING)
logging.getLogger('stevedore').setLevel(logging.INFO)
logging.getLogger('matplotlib').setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600

# Initialize Database
database.init_db(app)

# CSRF Protection
csrf = CSRFProtect(app)

# Cache Setup
cache = Cache(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# NewsAPI Client
newsapi = NewsApiClient(api_key=config.NEWSAPI_KEY) if NewsApiClient else None

# Global Variables
QISKIT_AVAILABLE = True

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    user = database.User.query.get(int(user_id))
    logging.debug(f"Loaded user {user_id}")
    return user

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found. Please check the URL or return to the homepage."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', message="An unexpected error occurred. Please try again later or contact support."), 500

# Routes: General Pages
@app.route('/')
@cache.cached(timeout=3600)
def index():
    articles = []
    try:
        if newsapi:
            query = 'quantum computing'
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            response = newsapi.get_everything(q=query, from_param=from_date, to=to_date, language='en', sort_by='publishedAt')
            articles = [{
                'title': a.get('title', 'No Title'),
                'summary': a.get('description', 'No summary available.'),
                'publishedAt': a.get('publishedAt', 'N/A'),
                'url': a.get('url', '#')
            } for a in response.get('articles', [])[:4]]
        else:
            articles = []
    except Exception as e:
        logging.error(f"Failed to fetch news for index: {e}")
        articles = []
    return render_template('index.html', articles=articles)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = forms.ContactForm()
    if request.method == 'POST':
        logging.debug(f"Contact form submitted: {form.data}")
        try:
            if form.validate_on_submit():
                logging.debug("Contact form validated successfully")
                name = form.name.data
                email = form.email.data
                message = form.message.data
                logging.info(f"Contact message received - Name: {name}, Email: {email}, Message: {message}")
                flash('Thank you for your message! We will get back to you soon.', 'success')
                return redirect(url_for('contact'))
            else:
                logging.debug(f"Contact form validation failed: {form.errors}")
                if 'email' in form.errors:
                    flash('Please provide a valid email address.', 'error')
                else:
                    flash('Please fill out all required fields correctly.', 'error')
        except Exception as e:
            logging.error(f"Error processing contact form: {str(e)}")
            flash('An error occurred while processing your message. Please try again later.', 'error')
    return render_template('contact.html', form=form)

# Routes: Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tools'))
    form = forms.LoginForm()
    if request.method == 'POST':
        logging.debug(f"Login form submitted: {form.data}")
        if form.validate_on_submit():
            logging.debug("Login form validated successfully")
            username = form.username.data
            password = form.password.data.encode('utf-8')
            user = database.User.query.filter_by(username=username).first()
            if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('tools'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            logging.debug(f"Login form validation failed: {form.errors}")
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tools'))
    form = forms.RegisterForm()
    if request.method == 'POST':
        logging.debug(f"Register form submitted: {form.data}")
        if form.validate_on_submit():
            logging.debug("Register form validated successfully")
            username = form.username.data
            email = form.email.data
            password = form.password.data.encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
            try:
                new_user = database.User(username=username, email=email, password=hashed_password)
                database.db.session.add(new_user)
                database.db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except database.db.exc.IntegrityError:
                database.db.session.rollback()
                flash('Username or email already exists.', 'error')
        else:
            logging.debug(f"Register form validation failed: {form.errors}")
    return render_template('register.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('tools'))
    form = forms.ForgotPasswordForm()
    if request.method == 'POST':
        logging.debug(f"Forgot password form submitted: {form.data}")
        if form.validate_on_submit():
            logging.debug("Forgot password form validated successfully")
            username = form.username.data
            email = form.email.data
            new_password = form.new_password.data.encode('utf-8')
            user = database.User.query.filter_by(username=username, email=email).first()
            if user:
                hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt()).decode('utf-8')
                user.password = hashed_password
                database.db.session.commit()
                flash('Password reset successful! Please log in with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Invalid username or email.', 'error')
        else:
            logging.debug(f"Forgot password form validation failed: {form.errors}")
    return render_template('forgot_password.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logging.debug(f"Logout triggered for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Routes: Tools and Learning
@app.route('/tools')
@login_required
def tools():
    logging.debug(f"Accessing tools page for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    return render_template('tools.html')

@app.route('/learning')
@login_required
def learning():
    gates = config.LEARNING_GATES.copy()
    algorithms = config.LEARNING_ALGORITHMS.copy()
    for gate in gates:
        gate['circuit_diagram'] = utils.generate_learning_diagram('gate', gate['name'])
    for algo in algorithms:
        algo['circuit_diagram'] = utils.generate_learning_diagram('algorithm', algo['name'])
    resources = [
        {'title': 'Qiskit Textbook', 'url': 'https://qiskit.org/learn'},
        {'title': 'IBM Quantum Learning', 'url': 'https://quantum-computing.ibm.com/learn'},
        {'title': 'Quantum Computing for the Curious', 'url': 'https://quantum-computing-for-the-curious.org/'}
    ]
    return render_template('learning.html', gates=gates, algorithms=algorithms, resources=resources)

@app.route('/quantum_gates')
@login_required
def quantum_gates():
    gates = config.LEARNING_GATES.copy()
    for gate in gates:
        gate['circuit_diagram'] = utils.generate_learning_diagram('gate', gate['name'])
    return render_template('quantum_gates.html', gates=gates)

@app.route('/quantum_algorithms')
@login_required
def quantum_algorithms():
    algorithms = config.LEARNING_ALGORITHMS.copy()
    for algo in algorithms:
        algo['circuit_diagram'] = utils.generate_learning_diagram('algorithm', algo['name'])
    return render_template('quantum_algorithms.html', algorithms=algorithms)

@app.route('/learning_resources')
@login_required
def learning_resources():
    logging.debug(f"Accessing learning resources page for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    try:
        resources = [
            {'title': 'Qiskit Textbook', 'url': 'https://qiskit.org/learn'},
            {'title': 'IBM Quantum Learning', 'url': 'https://quantum-computing.ibm.com/learn'},
            {'title': 'Quantum Computing for the Curious', 'url': 'https://quantum-computing-for-the-curious.org/'}
        ]
        return render_template('learning_resources.html', resources=resources)
    except Exception as e:
        logging.error(f"Error in learning_resources route: {str(e)}")
        flash(f"An error occurred while loading the learning resources page: {str(e)}", "danger")
        return render_template('learning_resources.html', resources=[])

# Routes: Simulation
@app.route('/circuit_simulation', methods=['GET', 'POST'])
@login_required
def circuit_simulation():
    logging.debug(f"Accessing circuit simulation page for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    form = forms.CircuitSimulationForm()
    outputs = {'circuit_diagram': None, 'result_sim': None, 'histogram_sim': None, 'bloch_img': None,
               'density_matrix_img': None, 'statevector_img': None, 'unitary_str': None, 'qasm_code': None}
    python_code = request.form.get('python_code') or session.get('python_code') or config.DEFAULT_PYTHON_CODE
    errors = []

    if request.method == 'POST' and 'load_predefined' in request.form:
        predefined_circuit = form.predefined_circuit.data
        if predefined_circuit and predefined_circuit in config.PREDEFINED_CIRCUITS:
            try:
                circuit = QuantumCircuit.from_qasm_str(config.PREDEFINED_CIRCUITS[predefined_circuit])
                python_code = utils.qasm_to_python_code(circuit, predefined_circuit)
                form.python_code.data = python_code
            except Exception as e:
                errors.append(f"Failed to load predefined circuit '{predefined_circuit}': {str(e)}.")
        else:
            errors.append(f"Invalid predefined circuit '{predefined_circuit}'.")
        return render_template('circuit_simulation.html', form=form, errors=errors, python_code=python_code)

    if form.validate_on_submit():
        python_code = form.python_code.data
        if not python_code:
            errors.append('Please provide Python code to simulate.')
            return render_template('circuit_simulation.html', form=form, errors=errors, python_code=python_code)

        circuit, error = utils.execute_circuit_code(python_code)
        if error:
            errors.append(error)
            return render_template('circuit_simulation.html', form=form, errors=errors, python_code=python_code)

        try:
            outputs['qasm_code'] = qasm2_dumps(circuit)
        except Exception as e:
            errors.append(f"Failed to transpile to QASM: {str(e)}.")
            return render_template('circuit_simulation.html', form=form, errors=errors, python_code=python_code)

        shots = form.shots.data
        noise_prob = form.noise_prob.data or 0.0

        visualizations = utils.generate_circuit_visualizations(circuit)
        outputs['circuit_diagram'] = visualizations.get('diagram')
        if not outputs['circuit_diagram']:
            errors.append("Failed to generate circuit diagram.")
            return render_template('circuit_simulation.html', form=form, errors=errors, python_code=python_code)

        has_measurements = any(instruction.operation.name == 'measure' for instruction in circuit.data)
        if has_measurements:
            counts, error = utils.run_local_simulation(circuit, shots, noise_prob)
            if error:
                errors.append(error)
            else:
                outputs['result_sim'] = str(counts)
                outputs['histogram_sim'] = utils.generate_histogram_image(counts)
                if not outputs['histogram_sim']:
                    errors.append("Failed to generate histogram.")

        if circuit.num_qubits <= config.MAX_QUBITS_FOR_STATEVECTOR and (
                form.show_statevector.data or form.show_density_matrix.data or form.show_bloch.data):
            try:
                statevector_circuit = circuit.copy()
                statevector_circuit.remove_final_measurements()
                statevector_circuit.save_statevector()
                statevector_simulator = AerSimulator(method='statevector')
                statevector_job = statevector_simulator.run(
                    utils.transpile_circuit(statevector_circuit, statevector_simulator))
                statevector = statevector_job.result().get_statevector()
                if form.show_bloch.data and circuit.num_qubits == 1:
                    outputs['bloch_img'] = utils.generate_bloch_image(statevector, circuit.num_qubits)
                    if not outputs['bloch_img']:
                        errors.append("Failed to generate Bloch sphere visualization.")
                if form.show_density_matrix.data:
                    outputs['density_matrix_img'] = utils.generate_density_matrix_image(statevector, circuit.num_qubits)
                    if not outputs['density_matrix_img']:
                        errors.append("Failed to generate density matrix visualization.")
                if form.show_statevector.data:
                    outputs['statevector_img'] = utils.generate_statevector_visualization(statevector, circuit.num_qubits)
                    if not outputs['statevector_img']:
                        errors.append("Failed to generate statevector visualization.")
            except Exception as e:
                errors.append(utils.handle_simulation_errors(e))

        if form.show_unitary.data and circuit.num_qubits <= config.MAX_QUBITS_FOR_UNITARY:
            try:
                unitary_circuit = circuit.copy()
                unitary_circuit.remove_final_measurements()
                unitary_simulator = AerSimulator(method='unitary')
                unitary_circuit.save_unitary()
                unitary_job = unitary_simulator.run(utils.transpile_circuit(unitary_circuit, unitary_simulator))
                outputs['unitary_str'] = str(unitary_job.result().get_unitary())
            except Exception as e:
                errors.append(utils.handle_simulation_errors(e))

        session['python_code'] = python_code
        session.modified = True

    if not form.is_submitted():
        form.python_code.data = python_code

    return render_template('circuit_simulation.html', form=form, **outputs, errors=errors, python_code=python_code)

@app.route('/hardware_simulation', methods=['GET', 'POST'])
@login_required
def hardware_simulation():
    logging.debug(f"Accessing hardware simulation page for user {current_user.username}")
    form = forms.HardwareSimulationForm()
    outputs = {'circuit_diagram': None, 'result_sim': None, 'histogram_sim': None}
    python_code = (request.form.get('python_code') or session.get('python_code') or request.args.get('python_code') or None)
    errors = []
    connected = 'backends' in session

    if python_code and not form.is_submitted():
        form.python_code.data = python_code

    form.backend.choices = session.get('backends', [('', 'Connect to IBM Quantum first')])
    handler = hardware_utils.HardwareSimulationHandler(session.get('ibm_token'))

    if request.method == 'POST':
        if form.connect.data:
            token = form.ibm_token.data
            logging.debug(f"Attempting to connect with token: {token[:4]}...{token[-4:]}")
            if not token:
                errors.append('IBM Quantum token is required.')
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)
            success, result = handler.connect_to_ibm_quantum(token)
            if not success:
                logging.error(f"Connection failed: {result}")
                errors.append(result)
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)
            form.backend.choices = result
            return render_template('hardware_simulation.html', form=form, python_code=form.python_code.data,
                                   errors=errors, connected=True)

        elif form.submit.data:
            if 'backends' not in session:
                errors.append('Please connect to IBM Quantum first.')
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)

            python_code = form.python_code.data
            if not python_code:
                errors.append('Please provide Python code to simulate.')
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)

            circuit, error = utils.execute_circuit_code(python_code)
            if error:
                errors.append(error)
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)

            success, result = handler.run_simulation(circuit, form.backend.data, form.shots.data, form.simulator_type.data, python_code)
            if not success:
                logging.error(f"Simulation failed: {result}")
                errors.append(result)
                return render_template('hardware_simulation.html', form=form, errors=errors, python_code=python_code)
            flash(f"Job submitted successfully! Job ID: {result['job_id']}", 'success')
            return redirect(url_for('hardware_results'))

    return render_template('hardware_simulation.html', form=form, **outputs, errors=errors, python_code=python_code,
                           connected=connected)

@app.route('/fetch_backends', methods=['POST'])
@login_required
def fetch_backends():
    logging.debug(f"Fetching backends for user {current_user.username}")
    token = request.form.get('ibm_token')
    if not token:
        logging.error("No IBM Quantum token provided")
        return jsonify({"success": False, "message": "IBM Quantum token is required."}), 400

    handler = hardware_utils.HardwareSimulationHandler()
    success, result = handler.connect_to_ibm_quantum(token)
    if not success:
        logging.error(f"Failed to fetch backends: {result}")
        return jsonify({"success": False, "message": result}), 400 if "Invalid" not in result else 401
    return jsonify({"success": True, "backends": result})

@app.route('/run_hardware_simulation', methods=['POST'])
@login_required
def run_hardware_simulation():
    logging.debug(f"Running hardware simulation for user {current_user.username}")
    if not request.is_json:
        logging.error("Invalid request format")
        return jsonify({"success": False, "message": "Invalid request format"}), 400

    data = request.json
    logging.debug(f"Received JSON data: {data}")
    python_code = data.get('python_code')
    backend_name = data.get('backend')
    token = data.get('token') or session.get('ibm_token')
    simulator_type = data.get('simulator_type', 'sampler')
    shots = int(data.get('shots', 1024))

    if not all([python_code, backend_name, token]):
        logging.error(f"Missing required parameters: python_code={bool(python_code)}, backend_name={bool(backend_name)}, token={bool(token)}")
        return jsonify({"success": False, "message": "Python code, backend name, and token are required"}), 400

    circuit, error = utils.execute_circuit_code(python_code)
    if error:
        logging.error(f"Circuit execution failed: {error}")
        return jsonify({"success": False, "message": error}), 400

    if shots < config.MIN_SHOTS or shots > config.MAX_SHOTS:
        logging.error(f"Invalid shots value: {shots}")
        return jsonify({"success": False, "message": f"Shots must be between {config.MIN_SHOTS} and {config.MAX_SHOTS}"}), 400

    handler = hardware_utils.HardwareSimulationHandler(token)
    if not handler.service:
        logging.debug(f"Handler not connected, attempting to connect with token: {token[:4]}...{token[-4:]}")
        success, result = handler.connect_to_ibm_quantum(token)
        if not success:
            logging.error(f"Failed to connect to IBM Quantum: {result}")
            return jsonify({"success": False, "message": result}), 400 if "Invalid" not in result else 401

    success, result = handler.run_simulation(circuit, backend_name, shots, simulator_type, python_code)
    if not success:
        logging.error(f"Simulation failed: {result}")
        return jsonify({"success": False, "message": result}), 400
    return jsonify({"success": True, "job_id": result['job_id'], "redirect": "/hardware_results"})

@app.route('/job_status/<job_id>', methods=['GET'])
def job_status(job_id):
    logging.debug(f"Checking status for job {job_id}")
    handler = hardware_utils.HardwareSimulationHandler(session.get('ibm_token'))
    if not handler.service and session.get('ibm_token'):
        logging.debug(f"Handler not connected, attempting to reconnect with session token")
        handler.connect_to_ibm_quantum(session.get('ibm_token'))
    job_result = handler.check_job_status(job_id)
    return jsonify(job_result)

@app.route('/hardware_results', methods=['GET', 'POST'])
@login_required
def hardware_results():
    logging.debug(f"Accessing hardware results for user {current_user.username}")
    form = forms.JobIDForm()
    outputs = {
        'circuit_diagram': None,
        'result_sim': None,
        'histogram_sim': None,
        'hardware_counts': None,
        'hardware_histogram': None,
        'comparison_img': None,
        'expectation_value': None,
        'job_id': None,
        'job_status': 'Pending',
        'queue_info': {'position': None, 'estimated_wait_seconds': None}
    }
    errors = []
    connected = 'backends' in session

    if request.method == 'POST' and form.validate_on_submit():
        job_id = form.job_id.data
        handler = hardware_utils.HardwareSimulationHandler(session.get('ibm_token'))
        if not handler.service and session.get('ibm_token'):
            logging.debug(f"Handler not connected, attempting to reconnect with session token")
            success, message = handler.connect_to_ibm_quantum(session.get('ibm_token'))
            if not success:
                errors.append(message)
                return render_template('hardware_results.html', form=form, **outputs, errors=errors, connected=connected)

        job_result = handler.check_job_status(job_id)
        if job_result['status'] == 'Failed':
            errors.append(job_result.get('error', 'Failed to retrieve job results.'))
        else:
            outputs['job_id'] = job_id
            outputs['job_status'] = job_result['status']
            outputs['queue_info'] = job_result.get('queue_info', {'position': None, 'estimated_wait_seconds': None})
            outputs['hardware_counts'] = job_result.get('hardware_counts')
            outputs['hardware_histogram'] = job_result.get('hardware_histogram')
            outputs['expectation_value'] = job_result.get('expectation_value')
            # Fetch circuit diagram and simulation results from session if available
            outputs['circuit_diagram'] = hardware_utils.image_cache.get(session.get('circuit_image_id'))
            outputs['result_sim'] = str(session.get('counts_sim')) if session.get('counts_sim') else None
            outputs['histogram_sim'] = hardware_utils.image_cache.get(session.get('histogram_image_id'))
            # Generate comparison histogram if both counts are available
            if outputs['hardware_counts'] and session.get('counts_sim'):
                outputs['comparison_img'] = utils.generate_comparison_histogram(session.get('counts_sim'), outputs['hardware_counts'])

    elif request.method == 'POST':
        errors.append('Invalid Job ID. Please enter a valid Job ID.')

    return render_template('hardware_results.html', form=form, **outputs, errors=errors, connected=connected)

# Routes: News and Papers
@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    logging.debug(f"Accessing news page for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    form = forms.NewsForm()
    articles = []
    try:
        if form.validate_on_submit():
            year = form.year.data
        else:
            year = 'all'
        if newsapi:
            query = 'quantum computing'
            from_date = f"{year}-01-01" if year != 'all' else (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = f"{year}-12-31" if year != 'all' else datetime.now().strftime('%Y-%m-%d')
            response = newsapi.get_everything(q=query, from_param=from_date, to=to_date, language='en',
                                              sort_by='publishedAt')
            articles = [{
                'title': a.get('title', 'No Title'),
                'summary': a.get('description', 'No summary available.'),
                'publishedAt': a.get('publishedAt', 'N/A'),
                'url': a.get('url', '#')
            } for a in response.get('articles', [])]
        else:
            articles = []
    except Exception as e:
        logging.error(f"Failed to fetch news: {e}")
        articles = []
    return render_template('news.html', form=form, articles=articles)

@app.route('/scientific_paper', methods=['GET', 'POST'])
@login_required
def scientific_paper():
    logging.debug(f"Accessing scientific_paper page for user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    form = forms.PaperForm()
    papers = []
    try:
        if form.validate_on_submit():
            year = form.year.data
        else:
            year = 'all'
        query = 'quantum computing'
        search = arxiv.Search(query=query, max_results=10, sort_by=arxiv.SortCriterion.SubmittedDate)
        for result in search.results():
            published_year = result.published.year
            if year == 'all' or str(published_year) == year:
                papers.append({
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'published': result.published.strftime('%Y-%m-%d'),
                    'summary': result.summary,
                    'url': result.entry_id
                })
    except Exception as e:
        logging.error(f"Failed to fetch papers: {e}")
        flash('Failed to load scientific papers.', 'error')
    return render_template('scientific_papers.html', form=form, papers=papers)

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Page not found. Please check the URL or return to the homepage."}), 404

# Application Entry Point
if __name__ == '__main__':
    app.run(debug=True)