import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.class_ import EnrolmentOut, BulkEnrolRequest, BulkEnrolResponse
from app.services.core import enrolment_service

router = APIRouter(prefix="/classes", tags=["enrolments"])


@router.post("/{class_id}/enrolments", response_model=BulkEnrolResponse, status_code=201)
async def bulk_enrol(
    class_id: uuid.UUID,
    body: BulkEnrolRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return await enrolment_service.bulk_enrol(db, class_id, body.student_ids)


@router.get("/{class_id}/enrolments", response_model=list[EnrolmentOut])
async def list_enrolments(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    enrolments = await enrolment_service.get_class_roster(db, class_id)
    return [
        EnrolmentOut(
            id=e.id,
            student_id=e.student_id,
            class_id=e.class_id,
            enrolled_at=e.enrolled_at,
            is_active=e.is_active,
            student_name=f"{e.student.first_name} {e.student.last_name}",
            email=e.student.email,
        )
        for e in enrolments
    ]


@router.delete("/{class_id}/enrolments/{student_id}", status_code=204)
async def remove_enrolment(
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    await enrolment_service.remove_enrolment(db, class_id, student_id)
