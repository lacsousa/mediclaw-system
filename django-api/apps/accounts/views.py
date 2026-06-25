from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
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


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    refresh = RefreshToken.for_user(user)
    record("USER_REGISTERED", user=user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=201,
    )


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
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }
    )


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
