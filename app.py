from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openpyxl
import os
import smtplib
import random
from email.message import EmailMessage
from flask_sqlalchemy import SQLAlchemy
from models import db, ClientDashboard, User
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.pool import QueuePool
from flask import send_file
from flask import redirect, url_for
from flask import render_template






app = Flask(__name__,template_folder='templates', static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_6jtIqEBw5Yvp@ep-shy-river-a8ju7x65-pooler.eastus2.azure.neon.tech/Login-client?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "poolclass": QueuePool,
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 1800
}
db.init_app(app)
#db = SQLAlchemy(app)
@app.route('/register-user', methods=['POST'])
def register_user():
    data = request.get_json()
    # Check if username already exists
    existing_user = User.query.filter_by(username=data.get("username")).first()
    if existing_user:
        return jsonify({"status": "error", "message": "Username already exists"}), 409

    # Create a new User object
    new_user = User(
        email=data.get("email", ""),
        name=data.get("name", ""),
        client_id=data.get("clientId", ""),
        username=data.get("username", ""),
        #password=data.get("password", ""),
        role=data.get("role", "")
    )
    new_user.set_password(data.get("password", ""))  # ✅ hash the password
    # Add and commit to DB
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "message": "User registered successfully!"})

@app.route('/validate-client', methods=['POST'])
def validate_client():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    user = User.query.with_entities(User.username, User.password).filter_by(username=username).first()

    if user and user.check_password(password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401
    
    
@app.route('/validate-login', methods=['POST'])
def validate_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    # Query the user from the database
    user = User.query.filter_by(username=username, role=role).first()

    if user and user.check_password(password):
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([
        {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "name": user.name,
            "client_id": user.client_id
        } for user in users
    ])


@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data['email']
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "Email not registered"})

    otp = str(random.randint(100000, 999999))

    # Save OTP temporarily in a file (for demo/testing purposes)
    with open("otp_store.txt", "w") as f:
        f.write(f"{email}:{otp}")

    # Send email
    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = "harikahaari0914@gmail.com"
    msg["To"] = email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("harikahaari0914@gmail.com", "sxaftdirmrampoxx")  # ⚠️ Use env var in production
        server.send_message(msg)
        server.quit()
        return jsonify({"success": True})
    except Exception as e:
        print("Email error:", e)
        return jsonify({"success": False, "message": "Failed to send OTP"})
    
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data['email']
    entered_otp = data['otp']
    new_password = data['new_password']

    # Load saved OTP
    if not os.path.exists("otp_store.txt"):
        return jsonify({"success": False, "message": "No OTP found"})

    with open("otp_store.txt", "r") as f:
        content = f.read().strip()

    saved_email, saved_otp = content.split(":")

    if email != saved_email or entered_otp != saved_otp:
        return jsonify({"success": False, "message": "Invalid OTP"})

    # Update password in database
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found in database"})

    user.set_password(new_password)  #  hash new password
    db.session.commit()

    return jsonify({"success": True})

@app.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json()
    username = data.get('username')

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"success": False, "message": "User not found."})

    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True, "message": "User deleted successfully."})


@app.route('/dashboard-form', methods=['GET', 'POST'])
def client_dashboard():
    client_data = None 
    error = None

    if request.method == 'POST':
        client_id = request.form.get('client_id')
        client = ClientDashboard.query.filter_by(client_code=client_id).first()

        if client:
            client_data = {
                'Client Name': client.client_name,
                'Client Code': client.client_code,
                'Investment Date': client.investment_date.strftime('%Y-%m-%d'),
                'Total Investment Value': client.total_value,
                'Investment Portfolio Value': client.portfolio_value,
                'Return Percentage': f"{client.return_pct}%",
                'Investment in Equity': client.equity,
                'Investment in MF': client.mf,
                'Investment in RE': client.re,
                'Investment on Others': client.others

            }
        else:
            error = "Client ID not found."

    return render_template('star_dashboard.html', client_data=client_data, error=error)

@app.route('/upload-dashboard', methods=['POST'])
def upload_dashboard():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(filepath)

        try:
            wb = openpyxl.load_workbook(filepath)
            sheet = wb.active

            for row in sheet.iter_rows(min_row=2, values_only=True):
                try:
                    # Extract and normalize values
                    client_code = str(row[0]).strip()
                    client_name = row[1]
                    inv_date = row[2]
                    total_val = float(row[3]) if row[3] is not None else 0.0
                    port_val = float(row[4]) if row[4] is not None else 0.0
                    ret_pct = float(row[5]) if row[5] is not None else 0.0
                    equity = float(row[6]) if row[6] is not None else 0.0
                    mf = float(row[7]) if row[7] is not None else 0.0
                    re = float(row[8]) if row[8] is not None else 0.0
                    others=row[9]
                    # Convert investment_date to a date object
                    if isinstance(inv_date, datetime):
                        inv_date = inv_date.date()
                    elif isinstance(inv_date, str):
                        try:
                            inv_date = datetime.strptime(inv_date.strip(), '%Y-%m-%d').date()
                        except:
                            inv_date = None
                    else:
                        inv_date = None

                    # Check for existing client and update or add
                    client = ClientDashboard.query.filter_by(client_code=client_code).first()
                    if client:
                        print(f"🔄 Updating client: {client_code}")
                        client.client_name = client_name
                        client.investment_date = inv_date
                        client.total_value = total_val
                        client.portfolio_value = port_val
                        client.return_pct = ret_pct
                        client.equity = equity
                        client.mf = mf
                        client.re = re
                        client.others = float(others) if others is not None else 0.0

                    else:
                        print(f"➕ Adding new client: {client_code}")
                        new_client = ClientDashboard(
                            client_code=client_code,
                            client_name=client_name,
                            investment_date=inv_date,
                            total_value=total_val,
                            portfolio_value=port_val,
                            return_pct=ret_pct,
                            equity=equity,
                            mf=mf,
                            re=re,
                            others=float(others) if others is not None else 0.0
                        )
                        db.session.add(new_client)
                except Exception as row_error:
                    print(f"❌ Error processing row {row}: {row_error}")

            db.session.commit()
            print("✅ Database commit successful")
            return jsonify({'status': 'success', 'message': 'Dashboard uploaded successfully'})

        except Exception as e:
            print("❌ Upload failed:", e)
            return jsonify({'status': 'error', 'message': str(e)}), 500

    else:
        return jsonify({'status': 'error', 'message': 'Only .xlsx files are allowed'}), 400

@app.route('/clients', methods=['GET'])
def get_clients():
    clients = ClientDashboard.query.all()
    return jsonify([
        {
            'client_code': client.client_code,
            'client_name': client.client_name,
            'investment_date': client.investment_date.strftime('%Y-%m-%d') if client.investment_date else None,
            'total_value': str(client.total_value),
            'portfolio_value': str(client.portfolio_value),
            'return_pct': str(client.return_pct),
            'equity': str(client.equity),
            'mf': str(client.mf),
            're': str(client.re),
            'others': str(client.others)

        } for client in clients
    ])

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard_form():
    client_data = None
    error = None

    if request.method == 'POST':
        client_id = request.form['client_id']
        client = ClientDashboard.query.filter_by(client_code=client_id).first()

        if client:
            client_data = {
                'Client Name': client.client_name,
                'Client Code': client.client_code,
                'Investment Date': client.investment_date.strftime('%Y-%m-%d'),
                'Total Investment Value': client.total_value,
                'Investment Portfolio Value': client.portfolio_value,
                'Return Percentage': f"{client.return_pct}%",
                'Investment in Equity': client.equity,
                'Investment in MF': client.mf,
                'Investment in RE': client.re,
                'Investment on Others': client.others

            }
        else:
            error = "Client ID not found."

    return render_template('client_dashboard.html', client_data=client_data, error=error)

@app.route('/client_dashboard')
def client_dashboard_page():
    return render_template('client_dashboard.html')

@app.route('/show-tables')
def show_tables():
    # Optional: Print users
    users = User.query.all()
    dashboards = ClientDashboard.query.all()

    return jsonify({
        "users": [
            {
                "username": u.username,
                "email": u.email,
                "role": u.role
            } for u in users
        ],
        "client_dashboards": [
            {
                "client_code": d.client_code,
                "client_name": d.client_name,
                "investment_date": d.investment_date.isoformat() if d.investment_date else None,
                "total_value": d.total_value,
                "portfolio_value": d.portfolio_value
            } for d in dashboards
        ]
    })

@app.route('/ping')
def ping():
    try:
        db.session.execute("SELECT 1")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/')
def home():
    return redirect(url_for('login_client'))


@app.route('/login-client')
def login_client():
    return render_template('login-client.html')


with app.app_context():
    db.create_all()
    
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))  # Use Render's PORT or default 10000
    with app.app_context():
        db.create_all()  # Creates tables if they don't exist
    app.run(host="0.0.0.0", port=port, debug=False)
