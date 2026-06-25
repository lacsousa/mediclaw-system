from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.services.log import record
from apps.common.exceptions import AppError
from apps.common.permissions import IsAdminRole

from .serializers import (
    AdminCreateUserSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# Helpers de cookie
# ---------------------------------------------------------------------------

def _jwt_settings():
    return settings.SIMPLE_JWT


def _set_auth_cookies(response, refresh: RefreshToken):
    """Seta access_token e refresh_token como cookies httpOnly."""
    s = _jwt_settings()
    secure = s.get("AUTH_COOKIE_SECURE", False)
    httponly = s.get("AUTH_COOKIE_HTTP_ONLY", True)
    samesite = s.get("AUTH_COOKIE_SAMESITE", "Lax")
    path = s.get("AUTH_COOKIE_PATH", "/")

    response.set_cookie(
        s.get("AUTH_COOKIE", "access_token"),
        str(refresh.access_token),
        max_age=int(s["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=httponly,
        secure=secure,
        samesite=samesite,
        path=path,
    )
    response.set_cookie(
        s.get("AUTH_COOKIE_REFRESH", "refresh_token"),
        str(refresh),
        max_age=int(s["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=httponly,
        secure=secure,
        samesite=samesite,
        path=path,
    )


def _clear_auth_cookies(response):
    """Remove os cookies de autenticação."""
    s = _jwt_settings()
    path = s.get("AUTH_COOKIE_PATH", "/")
    response.delete_cookie(s.get("AUTH_COOKIE", "access_token"), path=path)
    response.delete_cookie(s.get("AUTH_COOKIE_REFRESH", "refresh_token"), path=path)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    refresh = RefreshToken.for_user(user)
    record("USER_REGISTERED", user=user)

    response = Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=201,
    )
    _set_auth_cookies(response, refresh)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = (request.data.get("email") or "").lower()
    password = request.data.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if not user or not user.is_active:
        raise AppError("INVALID_CREDENTIALS", "E-mail ou senha incorretos.", 401)

    refresh = RefreshToken.for_user(user)
    record("LOGIN", user=user)

    response = Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }
    )
    _set_auth_cookies(response, refresh)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    """
    Rotaciona o refresh token:
      - Lê o refresh_token do cookie httpOnly.
      - Blacklista o token antigo (BLACKLIST_AFTER_ROTATION=True).
      - Emite novo par access+refresh como cookies.
    """
    s = _jwt_settings()
    cookie_name = s.get("AUTH_COOKIE_REFRESH", "refresh_token")
    refresh_token_str = request.COOKIES.get(cookie_name) or request.data.get("refresh")

    if not refresh_token_str:
        raise AppError("NO_REFRESH_TOKEN", "Refresh token ausente.", 401)

    try:
        old_token = RefreshToken(refresh_token_str)

        # Blacklist do token antigo
        if s.get("BLACKLIST_AFTER_ROTATION", False):
            try:
                old_token.blacklist()
            except Exception:
                pass  # token já na blacklist ou blacklist não habilitada

        # Emite novo par
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=old_token["user_id"])
        new_refresh = RefreshToken.for_user(user)

    except TokenError as e:
        raise AppError("INVALID_TOKEN", str(e), 401)

    response = Response({"access": str(new_refresh.access_token)})
    _set_auth_cookies(response, new_refresh)
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Blacklista o refresh token atual e limpa os cookies de autenticação.
    """
    s = _jwt_settings()
    cookie_name = s.get("AUTH_COOKIE_REFRESH", "refresh_token")
    refresh_token_str = request.COOKIES.get(cookie_name)

    if refresh_token_str:
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except Exception:
            pass  # token já inválido; logout prossegue normalmente

    record("LOGOUT", user=request.user)
    response = Response(status=204)
    _clear_auth_cookies(response)
    return response


@api_view(["POST"])
@permission_classes([IsAdminRole])
def admin_create_user(request):
    s = AdminCreateUserSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    record("ADMIN_CREATED_USER", user=request.user)
    return Response(UserSerializer(user).data, status=201)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user

    if request.method == "GET":
        return Response(UserSerializer(user).data)

    if request.method == "PATCH":
        s = MeUpdateSerializer(data=request.data, context={"user": user}, partial=True)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        update_fields = []
        if "name" in data:
            user.first_name = data["name"]
            update_fields.append("first_name")
        if "email" in data:
            user.email = data["email"]
            update_fields.append("email")
        if update_fields:
            user.save(update_fields=update_fields)

        return Response(UserSerializer(user).data)

    if request.method == "DELETE":
        user.delete()
        return Response(status=204)
