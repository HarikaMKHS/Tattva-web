import openpyxl
from datetime import datetime
from models import db, ClientDashboard
from app import app  # Import the Flask app instance

def import_excel_data(client_database):
    wb = openpyxl.load_workbook(client_database)
    sheet = wb.active

    with app.app_context():  # Ensures access to the DB
        for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
            client = ClientDashboard(
                client_code = row[0],
                client_name = row[1],
                investment_date = datetime.strptime(row[2], "%Y-%m-%d").date() if row[2] else None,
                total_value = row[3],
                portfolio_value = row[4],
                return_pct = row[5],
                equity = row[6],
                mf = row[7],
                re = row[8]
            )
            db.session.add(client)
        db.session.commit()
        print("✅ Data imported successfully!")

if __name__ == '__main__':
    import_excel_data("client_dashboard.xlsx")  # ✅ Correct filename
