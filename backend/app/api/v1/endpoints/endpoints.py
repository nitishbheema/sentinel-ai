from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.models import Endpoint, User
from app.schemas.schemas import EndpointOut

router = APIRouter()


@router.get("", response_model=List[EndpointOut])
def list_endpoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    endpoints = db.query(Endpoint).all()
    if not endpoints:
        # Seed initial lab endpoints if empty
        seed_eps = [
            Endpoint(hostname="sec-lab-srv01", ip_address="192.168.1.10", os_type="linux", os_version="Ubuntu 22.04 LTS", status="ACTIVE", agent_version="1.0.0"),
            Endpoint(hostname="corp-dc-01", ip_address="192.168.1.5", os_type="windows", os_version="Windows Server 2022", status="ACTIVE", agent_version="1.0.0"),
            Endpoint(hostname="fin-ws-analyst", ip_address="192.168.1.104", os_type="linux", os_version="Debian 12", status="ACTIVE", agent_version="1.0.0"),
            Endpoint(hostname="dmz-web-proxy", ip_address="10.0.0.1", os_type="linux", os_version="Alpine Linux 3.19", status="ACTIVE", agent_version="1.0.0")
        ]
        db.add_all(seed_eps)
        db.commit()
        endpoints = db.query(Endpoint).all()

    return endpoints


@router.get("/{endpoint_id}", response_model=EndpointOut)
def get_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ep = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return ep
