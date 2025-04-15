from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import CurrentAdmin
from app.infra.database.models import Admin
from app.schemas.admin import AdminMe, AdminSignIn, AdminSignInResponse, AdminSignUp
from app.services import AdminService
from app.utils.security import create_jwt_token, verify_password

router = APIRouter(tags=["Аутентификация"])


@router.post(
    "/auth/sign-up",
    summary="Регистрация админа",
    description="Регистрирует нового администратора в системе. При успешной регистрации возвращается JWT токен для авторизации.",
    response_model=AdminSignInResponse,
    status_code=200
)
async def admin_sign_up(
    data: AdminSignUp, service: AdminService = Depends(AdminService)
):
    if await service.repo.find_one(login=data.login):
        raise HTTPException(status_code=409, detail="Такой login уже зарегистрирован.")

    admin: Admin = await service.create_admin(
        **dict(login=data.login, password=data.password)
    )
    auth_token = create_jwt_token({"admin_id": admin.id})

    return dict(token=auth_token)


@router.post(
    "/auth/sign-in",
    summary="Аутентификация админа",
    response_model=AdminSignInResponse,
    status_code=200
)
async def admin_sign_in(
    data: AdminSignIn, service: AdminService = Depends(AdminService)
):
    admin = await service.repo.find_one(login=data.login)
    if admin is None or not verify_password(data.password, admin.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль.")

    auth_token = create_jwt_token(data={"admin_id": admin.id})
    return dict(token=auth_token)


@router.get(
    "/me",
    summary="Получение аккаунта админа",
    response_model=AdminMe,
    status_code=200
)
async def admin_me(admin: CurrentAdmin):
    return admin.to_dict()
