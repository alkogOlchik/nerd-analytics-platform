"""
Загрузка CSV из папки data_to_csv в PostgreSQL (nerd_db).
Порядок: employees → clients → tickets → остальные.
"""

import csv
from pathlib import Path

import psycopg2

DSN = "host=localhost port=5436 dbname=nerd_db user=postgres password=password"
DATA_DIR = Path(__file__).parent


def clean_value(v: str, bool_default=None):
    """Преобразует строку CSV в Python-значение."""
    v = v.strip()
    if v == "" or v.upper() == "NULL":
        return bool_default  # None если не задан дефолт
    if v.upper() in ("TRUE", "FALSE"):
        return v.upper() == "TRUE"
    return v


def load_csv(conn, table: str, csv_path: Path,
             extra_cols: dict | None = None,
             bool_defaults: dict | None = None):
    """
    extra_cols   — колонки, которых нет в CSV, но нужны в таблице (значение по умолчанию)
    bool_defaults — колонки, которые есть в CSV, но могут быть пустыми; fallback-значение
    """
    extra_cols = extra_cols or {}
    bool_defaults = bool_defaults or {}

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"  {table}: пусто, пропускаем")
        return 0

    csv_cols = list(rows[0].keys())
    all_cols = csv_cols + [k for k in extra_cols if k not in csv_cols]
    ph = ", ".join(["%s"] * len(all_cols))
    col_names = ", ".join(all_cols)
    sql = f"INSERT INTO {table} ({col_names}) VALUES ({ph}) ON CONFLICT DO NOTHING"

    count = 0
    errors = 0
    with conn.cursor() as cur:
        for row in rows:
            values = []
            for c in csv_cols:
                raw = row.get(c, "")
                bd = bool_defaults.get(c)  # None if not a bool-default col
                values.append(clean_value(raw, bool_default=bd))
            for k in extra_cols:
                if k not in csv_cols:
                    values.append(extra_cols[k])
            try:
                cur.execute(sql, values)
                count += 1
            except Exception as e:
                conn.rollback()
                errors += 1
                if errors <= 3:
                    print(f"  WARN row {row.get('id', '?')}: {e}")
                elif errors == 4:
                    print(f"  ... (дальнейшие ошибки скрыты)")
        conn.commit()

    if errors:
        print(f"  {table}: {errors} строк пропущено из-за ошибок")
    return count


def main():
    print(f"Подключаюсь: {DSN}")
    conn = psycopg2.connect(DSN)

    tasks = [
        # (table, file, extra_cols, bool_defaults)
        ("employees",    "employees.csv",    {"role": "support"}, {}),
        ("clients",      "clients.csv",      {"notify_email": True, "notify_push": True}, {}),
        ("tickets",      "tickets.csv",      {}, {"is_admin_changed": False}),
        ("reviews",      "reviews.csv",      {}, {"is_admin_changed": False}),
        ("chat_history", "chat_history.csv", {}, {"resolved_by_ai": False}),
        ("notifications","notifications.csv",{}, {}),
        ("attachments",  "attachments.csv",  {}, {}),
    ]

    total = 0
    for table, fname, extra, bool_def in tasks:
        path = DATA_DIR / fname
        if not path.exists():
            print(f"  {fname}: файл не найден, пропускаем")
            continue
        n = load_csv(conn, table, path, extra_cols=extra, bool_defaults=bool_def)
        print(f"  {table}: вставлено {n} строк")
        total += n

    conn.close()
    print(f"\nИтого: {total} строк загружено")


if __name__ == "__main__":
    main()
