from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def _vector_store_status() -> str:
    try:
        from apps.rag.vector_store import get_collection

        get_collection().count()
        return "ok"
    except Exception:
        return "error"


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    db_ok = True
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        db_ok = False

    vs_status = _vector_store_status()
    overall_ok = db_ok and vs_status == "ok"

    return Response(
        {
            "status": "ok" if overall_ok else "degraded",
            "db": "ok" if db_ok else "error",
            "vector_store": vs_status,
            "version": "0.1.0",
        },
        status=200 if overall_ok else 503,
    )
