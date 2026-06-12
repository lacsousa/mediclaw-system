from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityLogViewSet,
    NutritionNoteViewSet,
    SleepLogViewSet,
    WeightLogViewSet,
    health_summary,
)

router = DefaultRouter()
router.register("weight", WeightLogViewSet, basename="weight")
router.register("sleep", SleepLogViewSet, basename="sleep")
router.register("activity", ActivityLogViewSet, basename="activity")
router.register("nutrition", NutritionNoteViewSet, basename="nutrition")

urlpatterns = [
    path("summary/", health_summary),
    path("", include(router.urls)),
]
