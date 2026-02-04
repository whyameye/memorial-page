from django.urls import path, re_path

from .views import (
    submission, submission_password, SubmissionListView,
    SubmissionUpdateView, ImageCreateView, delete_image, delete_submission
)
from django.views.decorators.cache import cache_page


urlpatterns = [
    path("", cache_page(60)(SubmissionListView.as_view()), name='home'),  # 1 minute cache
    path("submit/", submission, name='submit'),
    path("submit/password/", submission_password, name='submission-password'),
    path("edit/<int:pk>/", SubmissionUpdateView.as_view(), name='submission-edit'),
    path("edit/<int:pk>/upload_image/", ImageCreateView.as_view(), name='jfu-upload'),
    path("edit/<int:pk>/delete_image/", delete_image, name='jfu-delete'),
    path("edit/<int:pk>/delete/", delete_submission, name='submission-delete'),
    path("edit/<int:pk>/links/", delete_image, name='link-inlines'),
]
