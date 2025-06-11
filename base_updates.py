import pandas as pd
from models import db, User, Bank, Object
from app import app

def import_banks(file_path):
    df = pd.read_excel(file_path, sheet_name='условия банка')
    banks = Bank.query.all()
    for _, row in df.iterrows():
        bank = Bank(installment_period=row['срок рассрочки'], interest_rate=row['процент ПВ'], cashback_value=row['кэшбек банка'])
        if bank not in banks:
            db.session.add(bank)
    db.session.commit()
    pass

def import_objects(file_path):
    xls = pd.ExcelFile(file_path)
    print(f"Available sheets in {file_path}: {xls.sheet_names}")
    df = pd.read_excel(file_path, sheet_name='Объекты')
    objects = Object.query.all()
    for _, row in df.iterrows():
        obj = Object(
            area=row['Площадь'],
            price=row['Стоимость по прайсу'],
            floor=row['Этаж'],
            entrance=row['Подьезд'],
            apartment_number=row['№ квартиры'],
            min_down_payment=row['Минимальный ПВ'],
            max_down_payment=row['Максимальный ПВ'],
            opt=row['ОПТ'],
            holding=row['Холдинг'],
            gd=row['ГД'],
            max_discount=row['Макс скидка'],
            project=row['Настоящий проект'],
            apartment_id=row['ID'],
            kd=row['КД'],
            mpp=row['МПП'],rop=row['РОП'],
            months_to_cadastre=row['Кадастр'],
            min_down_payment_installment=row['Минимальный ПВ'],
            max_installment_period_installment=row['Срок рассрочки'],
            mpp_ras=row['МПП_рас'],
            rop_ras=row['РОП_рас'],
            action=row['Акция']
        )

        if obj not in objects:
            db.session.add(obj)
    db.session.commit()
if __name__ == '__main__':
    with app.app_context():
        import_banks(r'Z:\GoldenHouse\Коммерческий департамент\!Автоматические отчеты\План-фактный отчет\temp\БД_клон для сайта ипотеки.xlsx')
        import_objects(r'Z:\GoldenHouse\Коммерческий департамент\!Автоматические отчеты\План-фактный отчет\temp\БД_клон для сайта ипотеки.xlsx')