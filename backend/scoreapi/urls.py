from django.urls import path

from .views import (
    PracticeMarkDetailView,
    PracticeMarkListCreateView,
    ScoreDetailView,
    ScoreListView,
    ScorePassageListView,
    health_check,
)

app_name = "scoreapi"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("scores/", ScoreListView.as_view(), name="score-list"),
    path("scores/<int:score_id>/", ScoreDetailView.as_view(), name="score-detail"),
    path(
        "scores/<int:score_id>/passages/",
        ScorePassageListView.as_view(),
        name="score-passages",
    ),
    path(
        "practice-marks/",
        PracticeMarkListCreateView.as_view(),
        name="practice-mark-list-create",
    ),
    path(
        "practice-marks/<int:mark_id>/",
        PracticeMarkDetailView.as_view(),
        name="practice-mark-detail",
    ),
]
