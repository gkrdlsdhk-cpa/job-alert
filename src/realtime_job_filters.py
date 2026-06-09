"""Realtime Job Alerts 공통 공고 필터."""

from __future__ import annotations


def global_excluded_title_keywords(config: dict) -> list[str]:
    cfg = config.get("realtime_job_alerts", {})
    return [str(token).strip() for token in cfg.get("exclude_title_contains", []) if str(token).strip()]


def merge_excluded_title_keywords(config: dict, *extra_lists: list[str]) -> list[str]:
    merged: list[str] = []
    for token in global_excluded_title_keywords(config):
        if token not in merged:
            merged.append(token)
    for items in extra_lists:
        for token in items:
            token = str(token).strip()
            if token and token not in merged:
                merged.append(token)
    return merged


def filter_jobs_by_excluded_titles(
    jobs: list[dict],
    excluded_keywords: list[str],
) -> tuple[list[dict], list[dict]]:
    if not excluded_keywords:
        return jobs, []

    kept: list[dict] = []
    skipped: list[dict] = []
    for job in jobs:
        title = str(job.get("title", ""))
        if any(keyword in title for keyword in excluded_keywords):
            skipped.append(job)
        else:
            kept.append(job)
    return kept, skipped
