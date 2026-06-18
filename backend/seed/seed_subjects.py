"""
Seed GES SHS core and elective subjects.
Run: python -m seed.seed_subjects
"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import AsyncSessionLocal
from app.models.subject import Subject

SUBJECTS = [
    # Core subjects (compulsory for all programmes)
    {"name": "English Language",        "code": "ENG",   "area": "Languages"},
    {"name": "Social Studies",          "code": "SS",    "area": "Social Sciences"},
    {"name": "Integrated Science",      "code": "ISCI",  "area": "Sciences"},
    {"name": "Mathematics (Core)",      "code": "MATH",  "area": "Mathematics"},
    # Sciences
    {"name": "Biology",                 "code": "BIOL",  "area": "Sciences"},
    {"name": "Chemistry",               "code": "CHEM",  "area": "Sciences"},
    {"name": "Physics",                 "code": "PHYS",  "area": "Sciences"},
    {"name": "Elective Mathematics",    "code": "EMATH", "area": "Mathematics"},
    # Humanities / Social Sciences
    {"name": "Economics",               "code": "ECONS", "area": "Social Sciences"},
    {"name": "Government",              "code": "GOVT",  "area": "Social Sciences"},
    {"name": "History",                 "code": "HIST",  "area": "Social Sciences"},
    {"name": "Geography",               "code": "GEOG",  "area": "Social Sciences"},
    {"name": "Literature in English",   "code": "LIT",   "area": "Languages"},
    # Business / Technical
    {"name": "Business Management",     "code": "BMGT",  "area": "Business"},
    {"name": "Financial Accounting",    "code": "FACCT", "area": "Business"},
    {"name": "Cost Accounting",         "code": "CACCT", "area": "Business"},
    {"name": "Technical Drawing",       "code": "TDRAW", "area": "Technical"},
    {"name": "Building Construction",   "code": "BCON",  "area": "Technical"},
    {"name": "Auto Mechanics",          "code": "AMECH", "area": "Technical"},
    # TVET
    {"name": "Hospitality Management",  "code": "HOSP",  "area": "TVET"},
    {"name": "Information Technology",  "code": "IT",    "area": "TVET"},
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        inserted = 0
        for s in SUBJECTS:
            from sqlalchemy import select
            existing = (await db.execute(select(Subject).where(Subject.code == s["code"]))).scalar_one_or_none()
            if not existing:
                db.add(Subject(name=s["name"], code=s["code"], ges_curriculum_area=s["area"]))
                inserted += 1
        await db.commit()
        print(f"Inserted {inserted} subjects ({len(SUBJECTS) - inserted} already existed)")


if __name__ == "__main__":
    asyncio.run(main())
