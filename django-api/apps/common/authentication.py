from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Autenticação JWT via cookie httpOnly, com fallback para Authorization header.

    Ordem de leitura:
      1. Header `Authorization: Bearer <token>` (mantém compatibilidade com testes
         que usam force_authenticate ou enviam o header diretamente).
      2. Cookie `access_token` (fluxo normal do browser via withCredentials).

    Isso garante que nenhum teste existente quebre, e que em produção o token
    nunca precise ser exposto em localStorage ou query string.
    """

    def authenticate(self, request):
        # 1. Tenta o header padrão primeiro
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated = self.get_validated_token(raw_token)
                return self.get_user(validated), validated

        # 2. Tenta o cookie httpOnly
        cookie_name = settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token")
        raw_token = request.COOKIES.get(cookie_name)
        if not raw_token:
            return None

        validated = self.get_validated_token(raw_token)
        return self.get_user(validated), validated
