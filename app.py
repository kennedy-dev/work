from flask import make_response, Flask, render_template, request, redirect, url_for, flash
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from models import User, Contact, DiasporaQuery
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import openpyxl
from database import db

# Load environment variables from .env file
load_dotenv()

# Configure the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize the Flask-Migrate object
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.init_app(app)

# Configure the Twilio client
account_sid_1 = os.getenv('TWILIO_ACCOUNT_SID')
auth_token_1 = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid_1, auth_token_1)

# Define the survey questions
survey_questions = [
    "What is your passport number?",
    "What is your gender?",
    "What is your location or address?",
    "How many people do you have in your household?",
    "What is your next of kin's name?",
    "What is your next of kin's contact?"
]

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager = LoginManager(app)

# Define the Flask routes
@app.route('/')
def index():
    return render_template('index.html')

emplate('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('signup'))

        # Create a new user
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Signup successful. Please login with your credentials.', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return 'Access Denied'   
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/bulk-messaging', methods=['GET', 'POST'])
@login_required
def bulk_messaging():
    if request.method == 'POST':
        message = request.form['message']
        contact_numbers = request.form.getlist('contacts')

        twilio_account_sid = app.config['TWILIO_ACCOUNT_SID']
        twilio_auth_token = app.config['TWILIO_AUTH_TOKEN']
        twilio_number_bulk = app.config['TWILIO_NUMBER']

        client = Client(twilio_account_sid, twilio_auth_token)

        for number in contact_numbers:
            message = client.messages.create(
                body=message,
                from_=twilio_number_bulk,
                to=number
            )
        return f'Message sent to {len(contact_numbers)} contacts.'
    else:
        return render_template('bulk_messaging.html')

@app.route('/textbot', methods=['POST'])
def textbot():
    incoming_message = request.values.get('Body', '').lower().strip()

    if incoming_message == '1':
        response = MessagingResponse()
        response.message('Welcome to the Ministry of Foreign and Diaspora Affairs citizen contact survey. Please enter your name')
        response.redirect('/textbot/question-1')
    elif incoming_message == '2':
        response = MessagingResponse()
        response.message('Please enter your name.')
        response.redirect('/textbot/report-issue')
    else:
        response = MessagingResponse()
        response.message('Welcome to our department! Text 1 to give or update your contact information, or text 2 to report an incident or contact the department.')

    return str(response)

@app.route('/textbot/question-<int:question_number>', methods=['POST'])
def survey_question(question_number):
    if question_number == 1:
        message = 'Welcome to the Ministry of Foreign and Diaspora Affairs citizen contact survey. Please enter your name'
    else:
        message = f'{survey_questions[question_number-2]}'
    response = MessagingResponse()
    response.message(message)
    response.redirect(f'/textbot/question-{question_number+1}')
    if question_number == len(survey_questions)+1:
        response.redirect('/textbot/complete')
    return str(response)

@app.route('/textbot/complete', methods=['POST'])
def survey_complete():
    # Save responses to Contact model
    contact = Contact.query.filter_by(phone_number=request.values.get('From')).first()
    if not contact:
        contact = Contact(phone_number=request.values.get('From'))
    setattr(contact, f'question_{len(survey_questions)}', request.values.get('Body'))
    db.session.add(contact)
    db.session.commit()

    response = MessagingResponse()
    response.message('Thank you for completing the survey!')
    return str(response)

@app.route('/textbot/report-issue', methods=['POST'])
def report_issue():
    name = request.values.get('Body', '').strip()
    phone_number = request.values.get('From', '').strip()
    description = request.values.get('Body', '').strip()

    # Save responses to DiasporaQuery model
    diaspora_query = DiasporaQuery(name=name, phone_number=phone_number, query=description)
    db.session.add(diaspora_query)
    db.session.commit()

    response = MessagingResponse()
    response.message(f'Thank you, {name}. Please describe your issue or request in detail.')
    response.message('Someone will be in touch with you soon.')
    return str(response)

@app.route('/admin/update-permissions', methods=['POST'])
@login_required
def update_permissions():
    if not current_user.is_admin:
        return 'Access Denied'

    user_id = request.form['user_id']
    new_role = request.form['new_role']

    user = User.query.filter_by(id=user_id).first()
    if user:
        if new_role == 'normal':
            user.is_admin = False
            user.is_superuser = False
        elif new_role == 'admin':
            user.is_admin = True
            user.is_superuser = False
        elif new_role == 'superuser':
            user.is_admin = True
            user.is_superuser = True

        db.session.commit()
        flash('User permissions updated successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('admin'))
    
@app.route('/admin/update-twilio-credentials', methods=['POST'])
@login_required
def update_twilio_credentials():
    if not current_user.is_admin:
        return 'Access Denied'
    account_sid_new = request.form['account_sid']
    auth_token_new = request.form['auth_token']
    twilio_number_new = request.form['twilio_number']
    
    # Set the environment variables
    os.environ['TWILIO_ACCOUNT_SID'] = account_sid_new
    os.environ['TWILIO_AUTH_TOKEN'] = auth_token_new
    os.environ['TWILIO_NUMBER'] = twilio_number_new

    # Update the .env file with new Twilio credentials
    with open('.env', 'w') as file:
        file.write(f'TWILIO_ACCOUNT_SID={account_sid_new}\n')
        file.write(f'TWILIO_AUTH_TOKEN={auth_token_new}\n')
        file.write(f'TWILIO_NUMBER={twilio_number_new}\n')
    
    # Validate the Twilio credentials here...
    app.config['TWILIO_ACCOUNT_SID'] = account_sid_new
    app.config['TWILIO_AUTH_TOKEN'] = auth_token_new
    return redirect(url_for('admin'))

@app.route('/citizen-contact')
@login_required
def citizen_contact():
    contacts = Contact.query.all()
    return render_template('citizen_contact.html', contacts=contacts)

@app.route('/download-contacts')
@login_required
def download_contacts():
    contacts = Contact.query.all()

    # Create a new workbook
    workbook = openpyxl.Workbook()

    # Get the active sheet
    sheet = workbook.active

    # Write the headers
    headers = ['Name', 'Phone Number', 'Passport Number', 'Gender', 'Location', 'Household Size', 'Next of Kin', 'Next of Kin Contact']
    sheet.append(headers)

    # Write the contact data
    for contact in contacts:
        data = [contact.name, contact.phone_number, contact.passport_number, contact.gender, contact.location, contact.household_size, contact.next_of_kin, contact.next_of_kin_contact]
        sheet.append(data)

    # Save the workbook to a BytesIO object
    excel_data = openpyxl.writer.excel.save_virtual_workbook(workbook)

    # Create a response with the Excel file
    response = make_response(excel_data)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=contacts.xlsx'

@app.route('/diaspora-queries')
@login_required
def diaspora_queries():
    diaspora_queries = DiasporaQuery.query.all()
    return render_template('diaspora_queries.html', diaspora_queries=diaspora_queries)
    
if __name__ == '__main__':
	# Perform database initialization and migrations
    with app.app_context():
        db.create_all()
        migrate.stamp()
        
    app.run(host='0.0.0.0', port=8081, debug=True)
