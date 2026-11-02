#!/usr/bin/env python3
"""
Расчёт витрины «артикул × день» из выгрузки заказов sales.csv.

Вход:  sales.csv  (order_id, order_date, sku, quantity, price, status)
Выход: daily_by_sku.csv  (sku, order_date, orders, revenue)

Правила обработки данных описаны в README.md.
"""

import csv
from collections import defaultdict
from datetime import datetime

# Словари для нормализации статусов
DELIVERED_ALIASES = {"delivered", "delivred", "deliverd", "deliver", "dlivered", "доставлен", "выкуплен"}
CANCELLED_ALIASES = {"cancelled", "canceled", "canceld", "cancel", "отменен", "отменён"}

def normalize_status(value):
    s = value.strip().lower()
    if s in DELIVERED_ALIASES:
        return "delivered"
    if s in CANCELLED_ALIASES:
        return "cancelled"
    return None

def main():
    # Храним уникальные заказы в множестве, чтобы избежать дублей
    unique_orders = set()
    # Данные для агрегации: (sku, date) -> данные
    aggregated_data = defaultdict(lambda: {"order_ids": set(), "revenue": 0.0})

    with open("sales.csv", mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # Проверка обязательных колонок
        required = ["order_id", "order_date", "sku", "quantity", "price", "status"]
        if not all(col in reader.fieldnames for col in required):
            print("Ошибка: в файле отсутствуют необходимые колонки.")
            return

        for row in reader:
            # 1. Очистка и валидация
            order_id = row.get("order_id", "").strip()
            sku = row.get("sku", "").strip()
            date_str = row.get("order_date", "").strip()
            status_raw = row.get("status", "").strip()

            # Пропуск пустых ключевых полей
            if not order_id or not sku or not date_str:
                continue

            # Нормализация статуса
            status = normalize_status(status_raw)
            if status is None:
                continue  # Пропускаем неизвестные статусы

            # Валидация даты
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue

            # Валидация и преобразование чисел
            try:
                quantity = float(row.get("quantity", "0").replace(",", ".").replace(" ", "").replace("\u00a0", ""))
                price = float(row.get("price", "0").replace(",", ".").replace(" ", "").replace("\u00a0", ""))
                if quantity <= 0 or price < 0 or quantity % 1 != 0:
                    continue
                quantity = int(quantity)
            except (ValueError, TypeError):
                continue

            # 2. Дедупликация: используем кортеж (order_id, sku, date) как уникальный ключ
            order_key = (order_id, sku, date_str)
            if order_key in unique_orders:
                continue
            unique_orders.add(order_key)

            # 3. Агрегация
            group_key = (sku, date_str)
            aggregated_data[group_key]["order_ids"].add(order_id)
            if status == "delivered":
                aggregated_data[group_key]["revenue"] += quantity * price

    # 4. Формирование и запись результата
    result_rows = []
    for (sku, date_str), data in aggregated_data.items():
        result_rows.append({
            "sku": sku,
            "order_date": date_str,
            "orders": len(data["order_ids"]),
            "revenue": data["revenue"]
        })

    # Сортировка
    result_rows.sort(key=lambda x: (x["sku"], x["order_date"]))

    # Запись в CSV
    with open("daily_by_sku.csv", mode="w", encoding="utf-8", newline="") as f:
        fieldnames = ["sku", "order_date", "orders", "revenue"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in result_rows:
            # Форматирование revenue: убираем .0, если число целое
            revenue = row["revenue"]
            if revenue == int(revenue):
                revenue = int(revenue)
            writer.writerow({**row, "revenue": revenue})

    print(f"Готово! Обработано уникальных заказов: {len(unique_orders)}")
    print(f"Строк в результате: {len(result_rows)}")

if __name__ == "__main__":
    main()