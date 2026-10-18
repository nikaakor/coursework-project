"""Початкові дані. Виконується лише якщо в БД ще немає товарів (дані не затираються при перезапуску)."""
from datetime import date, timedelta
import models


def P(**kw):
    kw.setdefault("image_url", "")
    return models.Product(**kw)


def seed_database(db):
    if db.query(models.Product).count() > 0:
        return

    products = [
        P(name="Нурофен форте таблетки 400 мг №12", category="Ліки", manufacturer="Реккітт Бенкізер", price=122.12,
          is_prescription=False, is_social=True, stock_quantity=14, form_type="Таблетки",
          active_ingredient="Ібупрофен (400 мг)",
          description="Симптоматичне лікування головного та зубного болю, невралгії, застуди та гарячки.",
          dosage_info="Дорослим: по 1 таблетці кожні 4-6 годин | Дітям від 12 років"),
        P(name="Трахісан таблетки для розсмоктування №20", category="Ліки", manufacturer="Alpen Pharma AG", price=204.88,
          is_prescription=False, is_social=True, stock_quantity=22, form_type="Таблетки",
          active_ingredient="Хлоргекидину біглюконат, Лідокаїну гідрохлорид",
          description="Для лікування запальних та інфекційних захворювань порожнини рота та глотки.",
          dosage_info="Дорослим: по 1 таблетці кожні 2 години | Дітям: з 4-х років"),
        P(name="Нурофен суспензія для дітей 100 мл", category="Ліки", manufacturer="Реккітт Бенкізер", price=216.82,
          is_prescription=False, is_social=True, stock_quantity=0, form_type="Суспензія",
          active_ingredient="Ібупрофен (100 мг/5 мл)",
          description="Жарознижувальний та знеболювальний засіб для дітей від 3 місяців.",
          dosage_info="Дітям: з 3 місяців до 12 років"),
        P(name="Вітамін C 1000 мг шипучі таблетки №20", category="Вітаміни", manufacturer="Швейцарія Фарма", price=185.00,
          is_prescription=False, stock_quantity=25, form_type="Таблетки",
          active_ingredient="Аскорбінова кислота (1000 мг)",
          description="Підтримка імунітету в період застуд, профілактика гіповітамінозу.",
          dosage_info="Дорослим: 1 шипуча таблетка на добу"),
        P(name="Аспірин Кардіо 100 мг №28", category="Ліки", manufacturer="Bayer", price=98.50,
          is_prescription=True, is_social=True, stock_quantity=30, form_type="Таблетки",
          active_ingredient="Ацетилсаліцилова кислота (100 мг)",
          description="Профілактика тромбозів та серцево-судинних ускладнень.",
          dosage_info="Дорослим: по 1 таблетці 1 раз на добу"),
        P(name="Тонометр автоматичний на плече Longevita", category="Медичні вироби", manufacturer="Longevita", price=899.00,
          stock_quantity=8, form_type="Прилад", active_ingredient="Медична техніка",
          description="Прилад для вимірювання артеріального тиску та пульсу з пам'яттю вимірювань.",
          dosage_info="Використовувати згідно з інструкцією приладу"),
        P(name="Термометр електронний безконтактний", category="Медичні вироби", manufacturer="Microlife", price=650.00,
          stock_quantity=0, form_type="Прилад", active_ingredient="Медична техніка",
          description="Швидке вимірювання температури тіла за 1 секунду без контакту.",
          dosage_info="Для дітей та дорослих"),
        P(name="Пластир бактерицидний набір №20", category="Медичні вироби", manufacturer="Igar", price=45.00,
          stock_quantity=50, form_type="Перев'язувальні матеріали", active_ingredient="Антисептичне покриття",
          description="Захист мозолів, порізів та невеликих ран від бруду та бактерій.",
          dosage_info="Застосовувати на чисту суху шкіру"),
    ]
    db.add_all(products)

    pharmacies = [
        models.Pharmacy(name="PharmPlus №1", address="вул. Степана Бандери, 12", lat=49.8355, lon=24.0138),
        models.Pharmacy(name="PharmPlus №2", address="пл. Ринок, 10", lat=49.8419, lon=24.0315),
        models.Pharmacy(name="PharmPlus №3", address="просп. Свободи, 28", lat=49.8441, lon=24.0262),
        models.Pharmacy(name="PharmPlus №4", address="вул. Шевченка, 100", lat=49.8477, lon=24.0580),
    ]
    db.add_all(pharmacies)
    db.flush()

    stock = [[5, 3, 0, 6], [8, 0, 7, 7], [0, 0, 0, 0], [10, 8, 0, 7],
             [10, 10, 5, 5], [0, 0, 3, 5], [0, 0, 0, 0], [20, 10, 10, 10]]
    for prod, row in zip(products, stock):
        for ph, qty in zip(pharmacies, row):
            db.add(models.PharmacyStock(pharmacy_id=ph.id, product_id=prod.id, quantity=qty))

    taras = models.User(name="Тарас Шевченко", email="taras@example.com", loyalty_type="premium", bonus_points=120.0)
    maria = models.User(name="Марія Коваль", email="maria@example.com", loyalty_type="social", bonus_points=30.0)
    db.add_all([taras, maria])
    db.flush()

    today = date.today()
    db.add(models.Prescription(user_id=taras.id, product_id=products[4].id, code="RX-2026-0001",
                               doctor="Іваненко О. П.", valid_until=today + timedelta(days=90)))
    db.add(models.Subscription(user_id=taras.id, product_id=products[3].id, kind="regular",
                               interval_days=30, last_order_date=today - timedelta(days=40)))
    db.add(models.Subscription(user_id=taras.id, product_id=products[5].id, kind="watch"))

    db.add(models.Promotion(title="Осінній імунітет", description="Усі вітаміни -20%", discount_percent=20,
                            category="Вітаміни", date_from=today - timedelta(days=1), date_to=today + timedelta(days=60)))
    db.add(models.Promotion(title="Тиждень здоров'я серця", description="Аспірин Кардіо -10%", discount_percent=10,
                            product_id=products[4].id, date_from=today - timedelta(days=1), date_to=today + timedelta(days=7)))
    db.commit()
