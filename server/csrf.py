from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi_csrf_protect import CsrfProtect
from authentication.authentications import get_current_user


def validate_csrf(request: Request, csrf_protect: CsrfProtect = Depends()):
    try:
        csrf_protect.validate_csrf_in_cookies(request)
    except Exception as e:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
