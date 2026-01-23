"""
CV Analysis Service – AI-powered match readiness and skill-gap analysis.
Uses Google Gemini to assess how well a candidate's CV fits target roles
and identify critical skill gaps with actionable suggestions.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SkillGap(BaseModel):
    """A single skill gap with impact and suggestion."""

    title: str = Field(..., description="Short name of the skill gap (e.g. LLM Orchestration)")
    impact: str = Field(..., description="One of: High, Medium, Low")
    description: str = Field(..., description="Actionable suggestion to address the gap")


class CVAnalysisResult(BaseModel):
    """Structured AI analysis result for CV match readiness and skill gaps."""

    match_readiness_score: int = Field(..., ge=0, le=100, description="0-100 percentage")
    match_readiness_message: str = Field(
        ...,
        description="1-2 sentence assessment of competitiveness for target roles",
    )
    skill_gaps: List[SkillGap] = Field(
        default_factory=list,
        description="Critical skill gaps with impact and suggestions",
    )


def generate_ai_analysis(
    profile: Dict[str, Any],
    matches_sample: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Generate AI analysis (match readiness %, assessment, skill gaps) from profile
    and optional job matches. Returns None if Gemini is unavailable or fails.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY / GOOGLE_API_KEY not set; skipping AI analysis")
        return None

    try:
        import google.genai as genai

        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to init Gemini client: {e}")
        return None

    name = profile.get("name") or "Candidate"
    skills = profile.get("skills") or []
    experience_level = profile.get("experience_level") or "Not specified"
    career_goals = profile.get("career_goals") or ""
    strengths = profile.get("strengths") or []
    education = profile.get("education")
    if isinstance(education, list):
        parts = []
        for e in education[:5]:
            if isinstance(e, str):
                parts.append(e)
            elif isinstance(e, dict):
                parts.append(
                    (e.get("degree") or e.get("institution") or "").strip() or str(e)
                )
            else:
                parts.append(str(e))
        education = ", ".join(p for p in parts if p)
    elif not isinstance(education, str):
        education = str(education) if education else ""

    target_roles_context = ""
    if matches_sample:
        titles = []
        for j in matches_sample[:8]:
            if not j:
                continue
            t = (j.get("job") or {}).get("title") or j.get("title") or j.get("job_title") or ""
            if t:
                titles.append(t)
        if titles:
            target_roles_context = (
                "\n\nTarget roles (from user's job feed): " + ", ".join(titles)
            )

    prompt = f"""You are an expert career coach and CV reviewer. Analyze this candidate profile and provide:
1. A **match readiness score** (0-100): how competitive they are for their target roles overall.
2. A **match readiness message**: 1-2 sentences, e.g. "Your profile is highly competitive for 70% of your target roles. Improving certain niche skills could reach 95%+."
3. **Critical skill gaps**: 0-4 specific gaps that would most improve their match rate. For each give:
   - title: short name (e.g. "LLM Orchestration", "FinOps & Budgeting")
   - impact: "High", "Medium", or "Low"
   - description: one concrete, actionable suggestion (1-2 sentences)

Profile:
- Name: {name}
- Experience level: {experience_level}
- Skills: {", ".join(skills[:40]) if skills else "Not specified"}
- Career goals / summary: {career_goals[:800] if career_goals else "Not specified"}
- Strengths: {", ".join(strengths[:20]) if strengths else "None"}
- Education: {education[:500] if education else "Not specified"}
{target_roles_context}

Be specific and actionable. Base skill gaps on common demands in their target roles and modern job market trends. Use "High" impact for skills that appear in many target roles; "Medium" or "Low" for niche or nice-to-have improvements.
Output valid JSON only."""

    contents = [prompt]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "response_schema": CVAnalysisResult,
            },
        )
    except Exception as e:
        logger.warning(f"Gemini generate_content failed: {e}")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
            )
            text = (response.text or "").strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            data = json.loads(text)
            result = CVAnalysisResult(**data)
            return {
                "match_readiness_score": result.match_readiness_score,
                "match_readiness_message": result.match_readiness_message,
                "skill_gaps": [
                    {"title": g.title, "impact": g.impact, "description": g.description}
                    for g in result.skill_gaps
                ],
            }
        except Exception as fallback_err:
            logger.warning(f"Fallback parse failed: {fallback_err}")
            return None

    try:
        if hasattr(response, "parsed") and response.parsed:
            result = response.parsed
        else:
            text = (response.text or "").strip()
            if "```" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            data = json.loads(text)
            result = CVAnalysisResult(**data)

        return {
            "match_readiness_score": result.match_readiness_score,
            "match_readiness_message": result.match_readiness_message,
            "skill_gaps": [
                {
                    "title": g.title,
                    "impact": g.impact,
                    "description": g.description,
                }
                for g in result.skill_gaps
            ],
        }
    except Exception as e:
        logger.warning(f"Failed to parse CVAnalysisResult: {e}")
        return None
