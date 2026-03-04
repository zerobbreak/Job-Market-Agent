"""
Shared FastAPI dependencies.

Re-exports commonly used dependencies so routers can do::

    from app.core.dependencies import CurrentUser, SettingsDep
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.security import AuthenticatedUser, get_current_user, get_optional_user

# --- Framework Dependencies ---

SettingsDep = Annotated[Settings, Depends(get_settings)]
"""Dependency: application settings singleton."""

CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
"""Dependency: authenticated user (raises 401 if missing/invalid)."""

OptionalUser = Annotated[AuthenticatedUser | None, Depends(get_optional_user)]
"""Dependency: authenticated user or None (no error on missing token)."""


# --- Repository Dependencies ---


def get_job_repo(user: CurrentUser, settings: SettingsDep):
    from app.repositories.job_repo import JobRepository

    return JobRepository(user.client, settings)


def get_app_repo(user: CurrentUser, settings: SettingsDep):
    from app.repositories.application_repo import ApplicationRepository

    return ApplicationRepository(user.client, settings)


def get_profile_repo(user: CurrentUser, settings: SettingsDep):
    from app.repositories.profile_repo import ProfileRepository

    return ProfileRepository(user.client, settings)


def get_match_repo(user: CurrentUser, settings: SettingsDep):
    from app.repositories.match_repo import MatchRepository

    return MatchRepository(user.client, settings)


def get_storage_repo(user: CurrentUser, settings: SettingsDep):
    from app.repositories.storage_repo import StorageRepository

    return StorageRepository(user.client, settings)

JobRepo = Annotated["JobRepository", Depends(get_job_repo)]
AppRepo = Annotated["ApplicationRepository", Depends(get_app_repo)]
ProfileRepo = Annotated["ProfileRepository", Depends(get_profile_repo)]
StorageRepo = Annotated["StorageRepository", Depends(get_storage_repo)]
MatchRepo = Annotated["MatchRepository", Depends(get_match_repo)]


# --- Service Dependencies ---


def get_job_service(
    settings: SettingsDep, job_repo: JobRepo, profile_repo: ProfileRepo
):
    from app.services.job_service import JobService

    return JobService(settings, job_repo, profile_repo)


def get_profile_service(
    settings: SettingsDep, profile_repo: ProfileRepo, storage_repo: StorageRepo
):
    from app.services.profile_service import ProfileService

    return ProfileService(settings, profile_repo, storage_repo)


def get_cv_service(
    settings: SettingsDep, job_repo: JobRepo, storage_repo: StorageRepo
):
    from app.services.cv_service import CVService

    return CVService(settings, job_repo, storage_repo)


def get_app_service(settings: SettingsDep, app_repo: AppRepo):
    from app.services.application_service import ApplicationService

    return ApplicationService(settings, app_repo)


def get_interview_service():
    from app.services.interview_service import InterviewService

    return InterviewService()


def get_tailoring_service():
    from app.services.tailoring_service import TailoringService

    return TailoringService()


def get_app_package_service(
    tailoring_service: Annotated["TailoringService", Depends(get_tailoring_service)],
    app_repo: AppRepo,
    storage_repo: StorageRepo,
    settings: SettingsDep,
):
    from app.services.application_package_service import ApplicationPackageService

    return ApplicationPackageService(tailoring_service, app_repo, storage_repo, settings)


JobServiceDep = Annotated["JobService", Depends(get_job_service)]
ProfileServiceDep = Annotated["ProfileService", Depends(get_profile_service)]
CVServiceDep = Annotated["CVService", Depends(get_cv_service)]
AppServiceDep = Annotated["ApplicationService", Depends(get_app_service)]
InterviewServiceDep = Annotated["InterviewService", Depends(get_interview_service)]
TailoringServiceDep = Annotated["TailoringService", Depends(get_tailoring_service)]
AppPackageServiceDep = Annotated["ApplicationPackageService", Depends(get_app_package_service)]
