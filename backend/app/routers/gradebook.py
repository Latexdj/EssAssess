from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role, get_current_user
from app.models.user import User
from app.services.core import gradebook_service
from app.schemas.gradebook import StudentGradeOut, ClassGradebookOut

router = APIRouter(prefix="/gradebook", tags=["gradebook"])


@router.get("/student", response_model=list[StudentGradeOut])
async def student_grades(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(require_role("student")),
) -> list[StudentGradeOut]:
    return await gradebook_service.get_student_grades(db, current_user.id)


@router.get("/class/{class_id}", response_model=ClassGradebookOut)
async def class_gradebook(
    class_id:     UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ClassGradebookOut:
    is_admin = current_user.role.value == "admin"
    if not is_admin and current_user.role.value != "teacher":
        from fastapi import HTTPException
        raise HTTPException(403, "Teacher access required")
    return await gradebook_service.get_class_gradebook(
        db, class_id, current_user.id, is_admin
    )
