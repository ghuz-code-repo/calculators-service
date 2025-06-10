import os
from flask import render_template, redirect, url_for, flash, request, session, Blueprint, jsonify
from models import db, User, Bank, Object, Apartment
import math
from datetime import datetime
import time
from models import CalculationHistory
from pytz import timezone
import logging
from sqlalchemy import desc
import base64

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
ALLOWED_EXTENSIONS = {'xlsx'}

bp_routes = Blueprint('routes', __name__) 
# Check if app is behind proxy
behind_proxy = True

prefix = '/calculators' if behind_proxy else ''
bp_routes = Blueprint('routes', __name__) 
def get_prefix_url(path):
    """Add the correct prefix to a URL path depending on whether app is behind proxy"""
    if not path.startswith('/'):
        path = '/' + path
    return prefix + path

def decode_header_full_name(request):
    """
    Декодирует base64-закодированное полное имя из заголовков запроса
    
    Args:
        request: Объект запроса Flask с заголовками
        
    Returns:
        str: Декодированное полное имя или оригинальное значение, если не закодировано
    """
    # Получаем закодированное имя и флаг кодировки
    encoded_full_name = request.headers.get('X-User-Full-Name', '')
    encoding = request.headers.get('X-User-Full-Name-Encoding', '')
    
    print(f"Received full name header: {encoded_full_name}, encoding: {encoding}")
    
    if encoding == 'base64' and encoded_full_name:
        try:
            # Декодируем base64
            decoded_bytes = base64.b64decode(encoded_full_name)
            decoded_name = decoded_bytes.decode('utf-8')
            print(f"Decoded name: '{decoded_name}'")
            return decoded_name
        except Exception as e:
            print(f"Error decoding full name: {e}")
            return encoded_full_name  # Возвращаем как есть, если декодирование не удалось
    else:
        return encoded_full_name  # Не закодировано или нет указания кодировки


def get_current_user():
    """Get current user information from request headers"""
    # Получение имени пользователя из заголовка аутентификации
    username = request.headers.get('X-User-Name')
    # Поиск пользователя в базе данных
    user = User.query.filter_by(login=username).first()
    
    is_admin = request.headers.get('X-User-Admin', 'false').lower() == 'true'
    full_name = decode_header_full_name(request)

    role_str = request.headers.get('X-User-Roles')
    roles = str.split(role_str, ',')
    role=''
    if 'admin' in roles or 'calculator-admin' in roles:
        role = 'admin'
    elif 'calculator-user' in roles or 'user' in roles:
        role = 'user'
    if user:
        if user.role != 'admin' and is_admin:
            user.role = 'admin'
            db.session.commit()
    print(f"User found: {user}, is_admin: {is_admin}")
    # Если пользователь не найден, но у него есть доступ через шлюз (т.е. заголовок X-User-Name присутствует),
    # создаем нового пользователя в базе данных
    if not user and username:
        # Получаем дополнительную информацию из заголовков и декодируем Base64 если нужно
        full_name = decode_header_full_name(request)
        
        # Создаем нового пользователя с декодированным полным именем
        user = User(
            login=username,
            full_name=full_name,
            role = role,
        )
        db.session.add(user)
        
    if user and ( user.full_name!=full_name):
        user.full_name = full_name
    if user and (user.role != role):
        user.role = role
    try:
        db.session.commit()  # This should set the user.id
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {str(e)}")
    return user


def calculate_FI_monthly_payment(loan_amount, month_count):
    monthly_interest_rate = 0.01375
    total_payment = 0
    monthly_principal = loan_amount / month_count

    payment = monthly_principal
    remaining_balance = loan_amount - payment
    total_payment += payment
    # Calculate decreasing payments and their sum
    for i in range(1, month_count):     
        payment =  (remaining_balance * (1 + monthly_interest_rate))/(month_count-i)

        remaining_balance = (remaining_balance * (1 + monthly_interest_rate))-payment
        # This month's total payment (principal + interest)
        total_payment += payment
        
        # Reduce the balance for next month
        
    # Calculate average monthly payment to make it constant
    average_monthly_payment = total_payment / month_count
    
    return average_monthly_payment, total_payment

def get_apartments_history(date_from=None, date_to=None):
    apartments = []
    if not date_from and not date_to:
        apartments = Apartment.query.filter_by(date_deleted=None).all()
    elif date_from and not date_to:
        apartments = Apartment.query.filter(Apartment.date_added >= date_from).all()
    elif not date_from and date_to:
        apartments = Apartment.query.filter(Apartment.date_added <= date_to).all()
    else:
        apartments = Apartment.query.filter(Apartment.date_added >= date_from, Apartment.date_added <= date_to).all()
    return apartments

@bp_routes.route('/calculate_installment_plan', methods=['GET', 'POST'])
def calculate_installment_plan():
    user = get_current_user()

    if request.method == 'POST':
        try:
            # Get apartment ID and other form data
            apartment_id = request.form.get('apartment_id')
            obj = Object.query.filter_by(apartment_id=apartment_id).first()
            if not obj:
                flash('Неверный ID квартиры.', 'danger')
                return render_template('calculate_installment_plan.html')
            
            if not Apartment.query.filter_by(apartment_id=apartment_id).first() and user.role != 'admin':
                flash('Квартира не участвует в акции.', 'danger')
                return render_template('calculate_installment_plan.html')
            project_name = obj.project
            apartment_number = obj.apartment_number
            area = obj.area
            price = obj.price
            floor = obj.floor
            # first_income = float(request.form.get('first_income', 0)) # will be percent value
            # # Handle first income logic - percentage or absolute value
            # if first_income < 100.0:
            #     # Treat as percentage
            #     first_income = first_income/100
            # elif first_income > 100.0:
            #     # Treat as absolute value
            #     first_income = (price/first_income)*100
                
            month_count = int(request.form.get('month_count', 0))
            gd_discount = request.form.get('gd_discount', 0, type=float)
            holding_discount = request.form.get('holding_discount', 0, type=float)
            opt_discount = request.form.get('opt_discount', 0, type=float)

            if (
                gd_discount > obj.gd or gd_discount < 0.0) or (
                holding_discount > obj.holding or holding_discount < 0.0) or (
                opt_discount > obj.opt or opt_discount < 0.0
                    ):
                flash('Превышен лимит по скидке.', 'danger')
                return render_template('calculate_installment_plan.html')
            
            

            # Get apartment data from database

            #max_discount = float(obj.max_discount)
            
            # Get property details

            discount = obj.mpp + obj.rop + obj.kd
            paid_reservation = 3000000 
            ipoteka = 420000000.0
            # Validate inputs
            if month_count <= 0 or month_count > 6:
                flash('Пожалуйста, введите корректный срок рассрочки первого платежа.', 'danger')
                return render_template('calculate_installment_plan.html')
            price-= paid_reservation #2
            full_disc_percent = discount/100 + opt_discount/100 + gd_discount/100 + holding_discount/100
            first_full_disc =  price * full_disc_percent
            if price - first_full_disc < ipoteka:
                ipoteka = price - first_full_disc
                
            initial_payment = price - first_full_disc - ipoteka
            # price_so_skidkoy = price - first_full_disc
            #pv1 
            rassrochka_baza = math.ceil(initial_payment)
            # Calculate loan amount
            # In the main function, replace the calculation part:
            # Calculate loan amount

            # Calculate monthly payment with compound interest (1.375% monthly)
            FI_monthly_payment, total_rassrochka_payment = calculate_FI_monthly_payment(initial_payment, month_count)

            # nacenka = math.ceil((1-initial_payment/total_rassrochka_payment)*100)/100
            # nacenka = 1-initial_payment/total_rassrochka_payment

            contract_price = math.ceil(total_rassrochka_payment + ipoteka)
            
            # contract_price = (price*(1) contract_price)
            real_math_discount = 1 - (total_rassrochka_payment + ipoteka)/price
            nacenka = math.ceil(((full_disc_percent - real_math_discount)*100))/100#math.floor((discount/100 + opt_discount/100 + gd_discount/100 + holding_discount/100 - nacenka)*100)/100#REALLY?!
            # total_discount = discount/100 + opt_discount/100 + gd_discount/100 + holding_discount/100 - nacenka#REALLY?!
            
            total_discount = full_disc_percent - nacenka
            # #pv2
            initial_payment = math.ceil(FI_monthly_payment*month_count) #price - price * total_discount - ipoteka

            # FI_monthly_payment = initial_payment/month_count
            
            #contract_price = math.ceil((price) * (1 - total_discount))
            price_per_sqm = math.ceil(price / area)
            contract_price_per_sqm = math.ceil(contract_price / area)
            # Total payment includes the initial payment and reservation
            """
            pv1 = rassrochka_baza
            pv2 = initial payment
            pv2+420mln = sdelka2
            pv1+420mln = sdelka1
            sdelka2/sdelka1 = real_nacenka
            """
            # Get user info for display
            full_name = user.full_name
            
            # Record calculation in history
            tz = timezone('Asia/Tashkent')
            current_datetime = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
            calculation_history = CalculationHistory(
                user_full_name=full_name,
                apartment_id=apartment_id,
                gd_discount=0,
                holding_discount=0,
                opt_discount=0
            )
            db.session.add(calculation_history)
            db.session.commit()
            contract_price = math.ceil(price*(1-total_discount))
            total_rassrochka_payment = math.ceil(contract_price - ipoteka)
            FI_monthly_payment = math.ceil(total_rassrochka_payment/month_count)
            # Create result object
            result = {
                'project_name': project_name,
                'area': area,
                'full_price': int(round(price + paid_reservation)),
                'price': int(round(price)),
                'paid_reservation': paid_reservation,
                'per_sqm_price': int(round(price_per_sqm)),
                'floor': floor,
                'apartment_number': apartment_number,
                'initial_payment': int(round(rassrochka_baza)),
                'total_rassrochka_payment': int(round(total_rassrochka_payment)),
                'FI_monthly_payment': int(round(FI_monthly_payment)),
                'installment_period': month_count,
                'contract_price': int(round(contract_price)),
                'contract_price_per_sqm': int(round(contract_price_per_sqm)),
                # 'nacenka': round(nacenka, 2),
                'total_discount': math.floor(total_discount*100),
                'full_name': full_name,
                'current_datetime': current_datetime
            }
            
            return render_template('mortgage_result.html', result=result)
            
        except Exception as e:
            flash(f'Произошла ошибка при расчете: {str(e)}', 'danger')
            return render_template('calculate_installment_plan.html')
    
    # GET request - just render the form
    return render_template('calculate_installment_plan.html', login_data=user.role)

@bp_routes.route('/update_database', methods=['POST'])
def update_database():
    try:
        from base_updates import import_banks, import_objects
        # Use absolute path with forward slashes for Docker compatibility
        # file_path = r'.\uploads\БД_клон для сайта ипотеки.xlsx'
        file_path = '/app/uploads/БД_клон для сайта ипотеки.xlsx'
        
        # Check if file exists before proceeding
        if not os.path.exists(file_path):
            # Try alternate locations
            alternate_paths = [
                './uploads/БД_клон для сайта ипотеки.xlsx',
                '/app/excel_data/БД_клон для сайта ипотеки.xlsx',
                './excel_data/БД_клон для сайта ипотеки.xlsx'
            ]
            
            for alt_path in alternate_paths:
                if os.path.exists(alt_path):
                    file_path = alt_path
                    print(f"Found file at alternate location: {file_path}")
                    break
            else:
                # No file found at any location
                error_msg = f"Excel file not found at any of these locations: {file_path} or {', '.join(alternate_paths)}"
                print(error_msg)
                flash(error_msg, 'danger')
                return redirect(get_prefix_url('/admin'))

        print(f"Using Excel file at: {file_path}")
        
        # Удаление всех данных из таблиц
        # User.query.delete()
        Bank.query.delete()
        Object.query.delete()
        db.session.commit()
        print("Данные успешно удалены")

        # # Вставка новых данных
        # import_users(file_path)
        # #socketio.emit('update_status', {'message': 'Users imported successfully.'}, namespace='/admin')
        import_banks(file_path)
        #socketio.emit('update_status', {'message': 'Banks imported successfully.'}, namespace='/admin')
        import_objects(file_path)
        #socketio.emit('update_status', {'message': 'Objects imported successfully.'}, namespace='/admin')
        flash('Database updated successfully!', 'success')
        #socketio.emit('update_status', {'message': 'Database updated successfully!'}, namespace='/admin')
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        flash(f'An error occurred: {e}', 'danger')
        #socketio.emit('update_status', {'message': f'An error occurred: {e}'}, namespace='/admin')
    return redirect(get_prefix_url('/admin'))

@bp_routes.route('/', methods=['GET', 'POST'])
def main():
    user = get_current_user()
    installment_periods = db.session.query(Bank.installment_period).distinct().all()
    interest_rates = db.session.query(Bank.interest_rate).distinct().all()
    cashback_value = request.args.get('cashback_value')
    return render_template('main.html', installment_periods=installment_periods, interest_rates=interest_rates, cashback_value=cashback_value, login_data=user.role, current_user=user)

@bp_routes.route('/admin', methods=['GET', 'POST'])
def admin():
    user = get_current_user()
    if user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(get_prefix_url('/'))
    
    # Get date filters
    date_from_str = request.form.get('date_from')
    date_to_str = request.form.get('date_to')
    
    # Convert to datetime objects if not None
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format for from date', 'danger')
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            # Set to end of day
            date_to = date_to.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Invalid date format for to date', 'danger')
    
    # Get filtered apartments
    apartments = get_apartments_history(date_from=date_from, date_to=date_to)
    calculation_history = CalculationHistory.query.order_by(desc(CalculationHistory.calculation_date)) 

    if request.form.get('apartment_ids') is not None:
        appartment_ids = request.form.get('apartment_ids').split(',')
        old_apartments = Apartment.query.filter_by(date_deleted=None).all()
        for apartment in old_apartments:
            apartment.date_deleted = datetime.now()
            db.session.commit()
        for apartment_id in appartment_ids:
            new_apartment = Apartment(apartment_id=apartment_id)
            db.session.add(new_apartment)
            db.session.commit()
        flash(f'Список квартир обновлен. Добавлено {len(appartment_ids)} квартир', 'success')

    file_updated = datetime.fromtimestamp(os.path.getmtime('./uploads/БД_клон для сайта ипотеки.xlsx')).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('admin.html', 
                          calculation_history=calculation_history, 
                          apartments=apartments,
                          date_from=date_from_str,
                          date_to=date_to_str,
                          file_updated=file_updated)

@bp_routes.route('/process_form', methods=['POST'])
def process_form():
    user = get_current_user()
    apartment_id = request.form['apartment_id']
    installment_period = int(request.form['installment_period'])
    # todo
    interest_rate = float(request.form['interest_rate'])
    gd_discount = request.form.get('gd_discount', 0, type=float)
    holding_discount = request.form.get('holding_discount', 0, type=float)
    opt_discount = request.form.get('opt_discount', 0, type=float)

    obj = Object.query.filter_by(apartment_id=apartment_id).first()
    if not obj:
        flash('Invalid apartment ID.', 'danger')
        return redirect(get_prefix_url('/'))
    bank = Bank.query.filter_by(installment_period=installment_period, interest_rate=interest_rate).first()
    if not bank:
        flash('No matching bank data found.', 'danger')
        return redirect(get_prefix_url('/'))

    if gd_discount> obj.gd or gd_discount < 0.0:
        flash('Невозможно применить такую скидку ГД.', 'danger')
        return redirect(get_prefix_url('/'))
    if holding_discount > obj.holding or holding_discount < 0.0:
        flash('Невозможно применить такую скидку Холдинга', 'danger')
        return redirect(get_prefix_url('/'))
    if opt_discount > obj.opt or opt_discount < 0.0:
        flash('Невозможно применить такую скидку ОПТ', 'danger')
        return redirect(get_prefix_url('/'))

    cashback_value = bank.cashback_value
    #todo
    max_discount = obj.mpp+ obj.rop + obj.kd
    project_name = obj.project
    apartment_number = obj.apartment_number
    area = obj.area
    price = obj.price

    paid_reservation = 3000000
    total_discount = max_discount/100 + opt_discount/100 + gd_discount/100 + holding_discount/100
    contract_price = math.ceil(((price - paid_reservation) * (1 - total_discount)) / (1 - cashback_value))
    print(total_discount)
    initial_payment = math.ceil(contract_price * (interest_rate / 100))
    monthly_payment = math.ceil((contract_price - initial_payment) / installment_period)
    contract_price_per_sqm = math.ceil(contract_price / area)

    full_name = user.full_name
    tz = timezone('Asia/Tashkent')
    current_datetime = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    calculation_history = CalculationHistory(
        user_full_name=full_name,
        apartment_id=apartment_id,
        gd_discount=gd_discount,
        holding_discount=holding_discount,
        opt_discount=opt_discount
    )
    db.session.add(calculation_history)
    db.session.commit()
    return render_template('results.html',
                           project_name=project_name,
                           apartment_number=apartment_number,
                           area=math.ceil(area),
                           contract_price=contract_price,
                           initial_payment=initial_payment,
                           monthly_payment=monthly_payment,
                           installment_period=installment_period,
                           full_name=full_name,
                           current_datetime=current_datetime,
                           contract_price_per_sqm=contract_price_per_sqm)

@bp_routes.route('/calculate_rassrochka', methods=['GET', 'POST'])
def calculate_rassrochka():
    try:
        calculator_type = request.form['calculator_type']
        apartment_id = request.form['apartment_id']
        down_payment = request.form['down_payment'].strip()  # Удаление пробелов
        installment_period = int(request.form['installment_period'])
        mpp = float(request.form.get('mpp', 0) or 0)
        rop = float(request.form.get('rop', 0) or 0)
        opt = float(request.form.get('opt', 0) or 0)
        holding = float(request.form.get('holding', 0) or 0)
        gd = float(request.form.get('gd', 0) or 0)
        action = float(request.form.get('action', 0) or 0)
    except ValueError:
        return "Неверный формат данных. Пожалуйста, введите корректные значения.", 400
    # Проверка длины строки
    print(len(down_payment))

    apartment = Object.query.filter_by(apartment_id=apartment_id).first()

    if not apartment:
        return "Квартира не найдена", 404

    apartment_dict = {
        'id': apartment.apartment_id,
        'area': apartment.area,
        'price': apartment.price,
        'floor': apartment.floor,
        'entrance': apartment.entrance,
        'apartment_number': apartment.apartment_number,
        'months_to_cadastre': apartment.months_to_cadastre, #!!!!!!
        'min_down_payment': apartment.min_down_payment,
        'project': apartment.project, #!!!!!!
        'min_down_payment_installment': apartment.min_down_payment_installment, #!!!!!!
        'max_installment_period_installment': apartment.max_installment_period_installment, #!!!!!!
        'mpp': apartment.mpp,
        'rop': apartment.rop,
        'mpp_ras': apartment.mpp_ras, #!!!!!!
        'rop_ras': apartment.rop_ras,#!!!!!!
        'holding': apartment.holding,
        "gd": apartment.gd,
        "action": apartment.action, #!!!!!!
        'opt': apartment.opt
    }
    initial_price = apartment_dict['price']
    area = apartment_dict['area']
    price_per_sqm = round(initial_price / area)

    reduced_price = initial_price - 3000000

    total_discount_percentage = mpp + rop + opt + holding + gd + action
    total_discount = reduced_price * (total_discount_percentage / 100)

    final_price = math.ceil(reduced_price - total_discount)
    if len(down_payment) > 3:
        down_payment = float(down_payment)
        down_payment_percentage = float((down_payment / (final_price))*100)
    else:
        down_payment_percentage = float(down_payment)
        down_payment=float(down_payment)# Преобразование в число
        down_payment = math.ceil(down_payment * final_price / 100)
        print("hi")

    print(down_payment_percentage)

    if calculator_type == 'mortgage' and (down_payment_percentage ) < apartment_dict['min_down_payment_installment']:
        return f"Процент первоначального взноса должен быть не менее {apartment_dict['min_down_payment_installment']}%", 400
    if calculator_type == 'mortgage' and down_payment_percentage > 90:
        return f"Процент первоначального взноса должен быть не больше 90%", 400
    if calculator_type == 'installment' and down_payment_percentage > 90:
        return f"Процент первоначального взноса должен быть не больше 90%", 400
    if calculator_type == 'installment' and (down_payment_percentage ) < apartment_dict['min_down_payment'] / 100:
        return f"Процент первоначального взноса должен быть не менее {apartment_dict['min_down_payment']}%", 400


    if calculator_type == 'mortgage' and installment_period > apartment_dict['max_installment_period_installment']:
        return f"Срок рассрочки не может быть больше {apartment_dict['max_installment_period_installment']}", 400
    if calculator_type == 'mortgage' and installment_period < 0:
        return f"Срок рассрочки не может быть меньше 0", 400
    if calculator_type == 'installment' and installment_period < 0:
        return f"Срок рассрочки не может быть меньше 0", 400
    if calculator_type == 'installment' and installment_period > apartment_dict['months_to_cadastre']:
        return f"Срок рассрочки не может быть больше {apartment_dict['months_to_cadastre']}", 400
    if calculator_type == 'installment':
        if mpp > apartment_dict['mpp']:
            return f"Максимально допустимый МПП: {apartment_dict['mpp']}%", 400
        if rop > apartment_dict['rop']:
            return f"Максимально допустимый РОП: {apartment_dict['rop']}%", 400
        if opt > apartment_dict['opt']:
            return f"Максимально допустимый ОПТ: {apartment_dict['opt']}%", 400
        if holding > apartment_dict['holding']:
            return f"Максимально допустимый Холдинг: {apartment_dict['holding']}%", 400
        if gd > apartment_dict['gd']:
            print(apartment_dict['gd'])
            return f"Максимально допустимый ГД: {apartment_dict['gd']}%", 400
        if action > apartment_dict['action']:
            return f"Максимально допустимая Акция: {apartment_dict['action']}%", 400
    else:
        if mpp > apartment_dict['mpp_ras']:
            return f"Максимально допустимый МПП: {apartment_dict['mpp_ras']}%", 400
        if rop > apartment_dict['rop_ras']:
            return f"Максимально допустимый РОП: {apartment_dict['rop_ras']}%", 400
        if opt > apartment_dict['opt']:
            return f"Максимально допустимый ОПТ: {apartment_dict['opt']}%", 400
        if holding > apartment_dict['holding']:
            return f"Максимально допустимый Холдинг: {apartment_dict['holding']}%", 400
        if gd > apartment_dict['gd']:
            return f"Максимально допустимый ГД: {apartment_dict['gd']}%", 400
        if action > apartment_dict['action']:
            return f"Максимально допустимая Акция: {apartment_dict['action']}%", 400


    if calculator_type == 'installment':
        remaining_amount = math.ceil(final_price - down_payment - 420000000)
    else:
        remaining_amount = math.ceil(final_price - down_payment)
    markup = math.ceil(remaining_amount * ((1 + (0.165 / 12)) ** installment_period))
    monthly_payment_factor = math.ceil(markup / installment_period)
    difference = math.ceil(down_payment + (420000000 if calculator_type == 'installment' else 0) + markup - final_price)
    if calculator_type == 'installment':
        final_price = down_payment + 420000000 + markup
        difference = (difference +down_payment+420000000+monthly_payment_factor*installment_period)-final_price
    else:
        final_price = down_payment + markup
        difference = (difference + down_payment + monthly_payment_factor * installment_period) - final_price
    final_price_per_sqm = round(final_price / area)

    current_date_time = time.strftime("%Y-%m-%d %H:%M:%S")
    booking_fee=3000000
    current_user = get_current_user()
    return render_template('result.html',
                           apartment=apartment_dict,
                           down_payment=f"{down_payment:,}".replace(",", " "),
                           monthly_payment_factor=f"{monthly_payment_factor:,}".replace(",", " "),
                           difference=f"{difference:,}".replace(",", " "),
                           months_to_cadastre=apartment_dict[
                               'max_installment_period_installment'] if calculator_type == 'mortgage' else
                           apartment_dict['months_to_cadastre'],
                           installment_period=installment_period,
                           mpp=mpp,
                           rop=rop,
                           opt=opt,
                           holding=holding,
                           gd=gd,
                           action=action,
                           total_discount_percentage=total_discount_percentage,
                           price_per_sqm=f"{price_per_sqm:,}".replace(",", " "),
                           final_price=f"{final_price:,}".replace(",", " "),
                           final_price_per_sqm=f"{final_price_per_sqm:,}".replace(",", " "),
                           booking_fee=f"{booking_fee:,}".replace(",", " "),  # Передача переменной в шаблон
                           math=math,
                           users_name=current_user.full_name,
                           current_date_time=current_date_time,
                           current_user = current_user)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp_routes.route('/admin/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # Проверяем, есть ли файл в запросе
        if 'xlsx_file' not in request.files:
            flash('No file part', 'error')
            return redirect(get_prefix_url('/admin')) # Возвращаемся на админ-страницу

        file = request.files['xlsx_file']

        # Если пользователь не выбрал файл, браузер может отправить
        # пустую часть без имени файла
        if file.filename == '':
            flash('No selected file', 'warning')
            return redirect(get_prefix_url('/admin'))

        # Проверяем, что файл существует и имеет разрешенное расширение
        if file and allowed_file(file.filename):
            # Используем secure_filename для безопасности имени файла
            filename = file.filename
            # Создаем папку для загрузок, если она не существует
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            # Сохраняем файл в указанную папку
            try:
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                flash(f'File "{filename}" uploaded successfully!', 'success')
                # Здесь вы можете добавить логику для обработки файла (например, чтение данных)
                # process_xlsx_file(file_path)
            except Exception as e:
                 flash(f'An error occurred while saving the file: {e}', 'error')

        return redirect(get_prefix_url('/admin')) # Возвращаемся на админ-страницу после загрузки
    return redirect(get_prefix_url('/admin'))
