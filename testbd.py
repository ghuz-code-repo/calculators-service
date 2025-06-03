from app import app, db
from models import User, Bank, Object

def print_users():
    users = User.query.all()
    for user in users:
        print(f"User: {user.full_name}, Login: {user.login}")

def print_banks():
    banks = Bank.query.all()
    for bank in banks:
        print(f"Bank: Installment Period: {bank.installment_period}, Interest Rate: {bank.interest_rate}, Cashback Value: {bank.cashback_value}")

def print_objects():
    objects = Object.query.all()
    for obj in objects:
        print(f"Object: ID: {obj.apartment_id}, Area: {obj.area}, Price: {obj.price}, Project: {obj.project}")

if __name__ == '__main__':
    with app.app_context():
        print("Users:")
        print_users()
        print("\nBanks:")
        print_banks()
        print("\nObjects:")
        print_objects()