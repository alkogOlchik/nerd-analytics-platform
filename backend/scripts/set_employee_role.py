"""Назначить роль сотруднику (для доступа к /analytics нужен analyst).

  python -m backend.scripts.set_employee_role admin analyst
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import Employee


async def main(username: str, role: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Employee).where(Employee.username == username))
        employee = result.scalar_one_or_none()
        if not employee:
            print(f"Сотрудник {username!r} не найден.", file=sys.stderr)
            raise SystemExit(1)
        old = employee.role
        employee.role = role
        await db.commit()
        print(f"OK: {username}: {old} -> {role}")
        if role == "analyst":
            print("Перелогиньтесь на фронте и обновите /analytics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("role", choices=["analyst", "operator", "product_owner", "super_admin"])
    args = parser.parse_args()
    asyncio.run(main(args.username, args.role))
