from django.urls import path

from .views import (
    PracticeMarkDetailView,
    PracticeMarkListCreateView,
    ScoreDetailView,
    ScoreListView,
    ScorePdfExtractionView,
    ScoreUploadView,
    ScorePassageListView,
    health_check,
    PassagePreviewView,
    ScorePageImageView,
    ScoreFileView,
    browser_session,
)

app_name = "scoreapi"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("session/", browser_session, name="browser-session"),
    path("scores/", ScoreListView.as_view(), name="score-list"),
    path("scores/upload/", ScoreUploadView.as_view(), name="score-upload"),
    path("scores/<int:score_id>/", ScoreDetailView.as_view(), name="score-detail"),
    path("scores/<int:score_id>/file/", ScoreFileView.as_view(), name="score-file"),
    path("scores/<int:score_id>/extract-measures/", ScorePdfExtractionView.as_view(), name="score-pdf-extraction"),
    path("scores/<int:score_id>/pages/<int:page_number>/image/", ScorePageImageView.as_view(), name="score-page-image"),
    path("passages/<int:passage_id>/preview/", PassagePreviewView.as_view(), name="passage-preview"),
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
