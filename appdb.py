from flask import Flask, render_template, request
from models import db, ClientDashboard
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://username:password@localhost/Tattvainfo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def client_dashboard():
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
                'Investment in RE': client.re
            }
        else:
            error = "Client ID not found."

    return render_template('client_dashboard.html', client_data=client_data, error=error)
