"""
Development seed: creates one school + three users (admin, teacher, student).
Run: python -m seed.seed_dev
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.school import School, SchoolType
from app.models.user import User, UserRole
from app.services.core.auth_service import hash_password


async def main() -> None:
    async with AsyncSessionLocal() as db:
        # School
        school = School(
            name="Tamale Senior High Technical School",
            region="Northern Region",
            type=SchoolType.SHTS,
        )
        db.add(school)
        await db.flush()

        # Users
        users = [
            User(school_id=school.id, email="admin@essassess.dev",   password_hash=hash_password("Admin1234!"),   first_name="Adwoa",   last_name="Mensah",  role=UserRole.admin),
            User(school_id=school.id, email="teacher@essassess.dev", password_hash=hash_password("Teacher1234!"), first_name="Kwabena", last_name="Asante",  role=UserRole.teacher),
            User(school_id=school.id, email="student@essassess.dev", password_hash=hash_password("Student1234!"), first_name="Akosua",  last_name="Boateng", role=UserRole.student),
        ]
        for u in users:
            db.add(u)

        await db.commit()
        print(f"Seeded school: {school.name} ({school.id})")
        for u in users:
            print(f"  {u.role.value}: {u.email}")


if __name__ == "__main__":
    asyncio.run(main())
