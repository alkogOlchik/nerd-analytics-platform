"""
Создание учётки сотрудника (аналог Django createsuperuser).

Запуск из корня репозитория:

  python -m backend.scripts.create_employee

  python -m backend.scripts.create_employee --username admin --password admin123 --full-name "Админ"
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import Employee
from backend.app.services.auth_service import hash_password


async def _create(
    username: str,
    password: str,
    full_name: str,
    role: str,
    sec_level: int,
) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Employee).where(Employee.username == username))
        if existing.scalar_one_or_none():
            print(f"Сотрудник с username={username!r} уже существует.", file=sys.stderr)
            raise SystemExit(1)

        employee = Employee(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            status="active",
            role=role,
            sec_level=sec_level,
        )
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        print(f"Сотрудник создан: id={employee.id}, username={employee.username}, role={employee.role}")
        print("Вход на фронте: /login → раздел «Аналитика» (/analytics)")


def _prompt() -> argparse.Namespace:
    print("Создание учётки сотрудника (employee) для админки /analytics\n")
    username = input("Username: ").strip()
    if not username:
        raise SystemExit("Username не может быть пустым.")
    full_name = input("ФИО [Администратор]: ").strip() or "Администратор"
    role = input("Роль [analyst]: ").strip() or "analyst"
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Password (again): ")
    if not password or password != password2:
        raise SystemExit("Пароли не совпадают или пустые.")
    return argparse.Namespace(
        username=username,
        password=password,
        full_name=full_name,
        role=role,
        sec_level=1,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать сотрудника (employee) в таблице employees")
    parser.add_argument("--username", help="Логин")
    parser.add_argument("--password", help="Пароль (лучше не передавать в CLI на проде)")
    parser.add_argument("--full-name", default="Администратор", help="ФИО")
    parser.add_argument(
        "--role",
        default="analyst",
        help="analyst (аналитика) | operator (тикеты) | product_owner | super_admin",
    )
    parser.add_argument("--sec-level", type=int, default=1, help="Уровень доступа (число)")
    args = parser.parse_args()

    if args.username and args.password:
        ns = args
    elif args.username or args.password:
        print("Укажите оба --username и --password или запустите без аргументов (интерактивно).")
        raise SystemExit(1)
    else:
        ns = _prompt()

    asyncio.run(
        _create(
            username=ns.username,
            password=ns.password,
            full_name=ns.full_name,
            role=ns.role,
            sec_level=ns.sec_level,
        )
    )


if __name__ == "__main__":
    main()
