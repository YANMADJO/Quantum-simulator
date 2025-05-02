from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FloatField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional
from Quantum_simulator import config


# === Form Definitions ===
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

class NewsForm(FlaskForm):
    year = SelectField('Year', choices=[('all', 'All')] + [(str(y), str(y)) for y in range(2025, 2015, -1)], default='all')
    submit = SubmitField('Filter')

class PaperForm(FlaskForm):
    year = SelectField('Year', choices=[('all', 'All')] + [(str(y), str(y)) for y in range(2025, 2015, -1)], default='all')
    submit = SubmitField('Filter')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class CircuitSimulationForm(FlaskForm):
    predefined_circuit = SelectField('Predefined Circuit', choices=[
        ('', 'Custom Python'),
        ('bell_state', 'Bell State'),
        ('phase_circuit', 'Phase Circuit'),
        ('quantum_teleportation', 'Quantum Teleportation'),
        ('shor_factor_15', "Shor's Algorithm (Factor 15)"),
        ('grover_2qubit', "Grover's Algorithm (2 Qubits)"),
        ('deutsch_jozsa', 'Deutsch-Jozsa Algorithm'),
        ('quantum_fourier_transform', 'Quantum Fourier Transform'),
        ('quantum_phase_estimation', 'Quantum Phase Estimation')
    ], default='')
    python_code = TextAreaField('Python Code', validators=[DataRequired()])
    shots = IntegerField('Shots', validators=[DataRequired(), NumberRange(min=config.MIN_SHOTS, max=config.MAX_SHOTS)], default=config.DEFAULT_SHOTS)
    noise_prob = FloatField('Noise Probability', validators=[Optional(), NumberRange(min=0.0, max=1.0)], default=config.DEFAULT_NOISE_PROB)
    show_bloch = BooleanField('Show Bloch Sphere (1 qubit only)', default=False)
    show_density_matrix = BooleanField('Show Density Matrix', default=False)
    show_statevector = BooleanField('Show Statevector', default=False)
    show_unitary = BooleanField('Show Unitary Matrix', default=False)
    submit = SubmitField('Run Simulation')

class HardwareSimulationForm(FlaskForm):
    python_code = TextAreaField('Python Code', validators=[DataRequired()])
    ibm_token = PasswordField('IBM Quantum Token', validators=[DataRequired()])
    simulator_type = SelectField('Simulator Type', choices=[('sampler', 'Sampler'), ('estimator', 'Estimator')])
    backend = SelectField('Backend', choices=[])
    shots = IntegerField('Shots', validators=[NumberRange(min=config.MIN_SHOTS, max=config.MAX_SHOTS)])
    connect = SubmitField('Connect')
    submit = SubmitField('Run Simulation')