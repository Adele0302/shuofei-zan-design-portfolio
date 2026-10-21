"""Small explicitly configured API-key RBAC for the local FDE demo.

NOT a production identity provider. Use a reverse proxy/OIDC and TLS before
remote deployment. Secrets must be set via environment variables.
"""
from __future__ import annotations
import hmac
import json
import os
from dataclasses import dataclass
from fastapi import Header,HTTPException
from app.core import workspace_id

@dataclass(frozen=True)
class Identity:
    workspace:str
    role:str
    name:str

_ROLES={'reader','editor','reviewer','admin'}


def get_identity(x_api_key:str|None=Header(default=None,alias='X-API-Key')) -> Identity:
    try:
        settings=json.loads(os.getenv('APP_API_KEYS','{}'))
        if not isinstance(settings,dict): raise ValueError('invalid APP_API_KEYS')
    except (ValueError,TypeError):
        raise HTTPException(status_code=503,detail='server authentication is not configured correctly')
    if not settings:
        raise HTTPException(status_code=503,detail='set APP_API_KEYS before using the API')
    candidate=x_api_key or ''
    selected=None
    # Compare all entries to avoid signaling which prefix matches.
    for secret,config in settings.items():
        if not isinstance(config,dict) or len(secret)<16:
            raise HTTPException(status_code=503,detail='invalid server API-key configuration')
        matched=hmac.compare_digest(candidate,secret)
        if matched: selected=config
    if selected is None:
        raise HTTPException(status_code=401,detail='invalid or missing X-API-Key',
                            headers={'WWW-Authenticate':'ApiKey'})
    role=selected.get('role','reader')
    if role not in _ROLES:
        raise HTTPException(status_code=503,detail='unknown role in APP_API_KEYS')
    try:workspace=workspace_id(selected.get('workspace'))
    except ValueError:
        raise HTTPException(status_code=503,detail='invalid workspace config')
    name=selected.get('name','API reviewer')
    if not isinstance(name,str) or len(name)>100 or len(name)<2:
        raise HTTPException(status_code=503,detail='invalid auth principal name')
    return Identity(workspace=workspace,role=role,name=name)


def need(identity:Identity,*roles:str) -> None:
    if identity.role!='admin' and identity.role not in roles:
        raise HTTPException(status_code=403,detail='permission denied for this role')
