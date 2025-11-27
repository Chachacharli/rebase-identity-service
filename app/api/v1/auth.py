from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.core.db import get_session
from app.core.store import authorization_code_store
from app.repositories.app_settings_repository import AppSettingRepository
from app.repositories.client_application_repository import ClientApplicationRepository
from app.services.user_service import UserService

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


# GET: mostrar login
@router.get("/authorize")
def authorize_get(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    session: Session = Depends(get_session),
):
    repository = ClientApplicationRepository(session)
    client = repository.get_by_client_id(client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    if redirect_uri not in client.redirect_uris:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": scope,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "error": None,  # sin error al inicio
        },
    )


# POST: procesar login y generar authorization code
@router.post("/authorize")
def authorize_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...),
    scope: str = Form(...),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(...),
    session: Session = Depends(get_session),
):
    # repo = UserRepository(session)
    service = UserService(session=session)
    try:
        user = service.authenticate_user_by_email_or_username(username, password)
    except Exception as e:
        error_msg = getattr(e, "message", str(e))
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": scope,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "error": error_msg,
            },
        )
    app_settings_repository = AppSettingRepository(session)

    ttl_expiration_code = int(app_settings_repository.get("ttl_access_token"))

    # Generar authorization code (asociado al user_id)
    auth_code = str(uuid4())
    authorization_code_store.save(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code=auth_code,
        user_id=user.id,
        scope=scope.split(" "),
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_expiration_code),
    )

    # Redirigir con code + state
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
    return RedirectResponse(redirect_url, status_code=302)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@router.post("/forgot-password")
def process_forgot_password(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session),
):
    user_service = UserService(session)
    user = user_service.user_repo.get_by_email(email)
    if not user:
        return templates.TemplateResponse(
            "forgot_password.html",
            {
                "request": request,
                "error": "The email does not exist. Please check and try again.",
            },
        )

    # Aquí se generaría y enviaría el enlace de restablecimiento de contraseña

    response = user_service.send_mail_reset_password(email)

    if not response:
        return templates.TemplateResponse(
            "forgot_password.html",
            {
                "request": request,
                "error": "There was an error sending the reset email. Please try again later.",
            },
        )
    else:
        # Por simplicidad, solo mostramos un mensaje
        return templates.TemplateResponse(
            "forgot_password.html",
            {
                "request": request,
                "message": "A reset link has been sent.",
            },
        )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    email = True
    if not email:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Invalid or expired token."},
        )
    return templates.TemplateResponse(
        "reset_password.html", {"request": request, "token": token}
    )


@router.post("/reset-password")
def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session),
):
    user_service = UserService(session)
    response = user_service.reset_password(new_password=password, token=token)

    if not response:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "error": "Invalid or expired token."},
        )

    return RedirectResponse("/login", status_code=303)


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email(request: Request, token: str, session: Session = Depends(get_session)):
    """Verify token and activate the user's email, rendering the appropriate template."""
    user_service = UserService(session)
    success = user_service.verify_email(token)
    if not success:
        return templates.TemplateResponse(
            "verify_resend.html",
            {"request": request, "error": "Invalid or expired token."},
        )

    return templates.TemplateResponse(
        "verify_result.html",
        {"request": request, "message": "Email verified successfully."},
    )


@router.get("/resend-verification", response_class=HTMLResponse)
def resend_verification_page(request: Request):
    return templates.TemplateResponse("verify_resend.html", {"request": request})


@router.post("/resend-verification")
def resend_verification_submit(
    request: Request, email: str = Form(...), session: Session = Depends(get_session)
):
    user_service = UserService(session)
    success = user_service.resend_verification(email)
    if not success:
        return templates.TemplateResponse(
            "verify_resend.html",
            {
                "request": request,
                "error": "Could not resend verification. Please check the email or try later.",
            },
        )

    return templates.TemplateResponse(
        "verify_resend.html",
        {
            "request": request,
            "message": "A verification email has been sent if the account exists.",
        },
    )
