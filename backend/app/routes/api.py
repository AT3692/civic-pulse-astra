from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from app.schemas import (
    Category,
    Complaint,
    ComplaintCreate,
    ComplaintPage,
    Priority,
    ProviderMeta,
    Stats,
    Status,
    StatusUpdate,
)
from app.services.complaints import ComplaintService

router = APIRouter(prefix="/api")


def service(request: Request) -> ComplaintService:
    return request.app.state.service


Service = Annotated[ComplaintService, Depends(service)]


@router.post("/complaints", response_model=Complaint, status_code=201)
async def create(data: ComplaintCreate, request: Request, svc: Service):
    return await svc.create(data, request.state.client_ip)


@router.get("/complaints", response_model=ComplaintPage)
async def list_complaints(
    svc: Service,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
):
    return await svc.list_complaints(page, page_size, category, priority, status)


@router.get("/complaints/{complaint_id}", response_model=Complaint)
async def get(complaint_id: UUID, svc: Service):
    return await svc.get(complaint_id)


@router.patch("/complaints/{complaint_id}/status", response_model=Complaint)
async def transition(complaint_id: UUID, data: StatusUpdate, svc: Service, x_operator_key: str = Header(default="")):
    svc.authorize_operator(x_operator_key)
    return await svc.transition(complaint_id, data.status)


@router.get("/stats", response_model=Stats)
async def stats(response: Response, svc: Service):
    result, cache = await svc.stats()
    response.headers["X-Cache"] = cache
    return result


@router.get("/meta/providers", response_model=ProviderMeta)
async def providers(svc: Service):
    return await svc.triage.meta()
