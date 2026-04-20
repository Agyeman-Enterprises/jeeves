from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)


@dataclass
class SocialPost:
    platform: str  # LinkedIn, Twitter/X, Instagram, Facebook, TikTok
    business: str
    content: str
    scheduled_time: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, published
    engagement_metrics: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, str]:
        return {
            "platform": self.platform,
            "business": self.business,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else "",
            "status": self.status,
            "engagement": str(self.engagement_metrics or {}),
        }


class SocialMediaManagerAgent(BaseAgent):
    """Handles social content creation, scheduling, and engagement tracking."""

    data_path = Path("data") / "sample_social_media.json"
    description = "Manages social media content, scheduling, and engagement across platforms."
    capabilities = [
        "Create social media posts",
        "Schedule content",
        "Track engagement metrics",
        "Respond to comments/messages",
        "Analyze performance",
        "Suggest content ideas",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.posts = self._load_posts()

    def supports(self, query: str) -> bool:
        keywords = [
            "social media",
            "linkedin",
            "twitter",
            "instagram",
            "facebook",
            "tiktok",
            "post",
            "engagement",
            "schedule",
            "social",
        ]
        return any(keyword in query.lower() for keyword in keywords)

    def handle(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        query_lower = query.lower()

        if "schedule" in query_lower or "scheduled" in query_lower:
            return self._handle_scheduled_posts()
        elif "engagement" in query_lower or "metrics" in query_lower:
            return self._handle_engagement_analysis()
        elif "draft" in query_lower or "create" in query_lower or "post" in query_lower:
            return self._handle_create_post(query, context)
        elif "respond" in query_lower or "reply" in query_lower:
            return self._handle_engagement_response(query, context)
        else:
            return self._handle_overview()

    def _handle_scheduled_posts(self) -> AgentResponse:
        scheduled = [p for p in self.posts if p.status == "scheduled" and p.scheduled_time]
        if not scheduled:
            return AgentResponse(
                agent=self.name,
                content="No posts scheduled.",
                data={"scheduled": []},
            )

        scheduled.sort(key=lambda p: p.scheduled_time or datetime.min.replace(tzinfo=timezone.utc))
        lines = [f"Scheduled Posts: {len(scheduled)}"]
        for post in scheduled[:5]:
            time_str = post.scheduled_time.strftime("%Y-%m-%d %I:%M %p") if post.scheduled_time else "TBD"
            lines.append(f"- {post.platform} for {post.business} at {time_str}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"scheduled": [p.to_dict() for p in scheduled]},
        )

    def _handle_engagement_analysis(self) -> AgentResponse:
        published = [p for p in self.posts if p.status == "published" and p.engagement_metrics]
        if not published:
            return AgentResponse(
                agent=self.name,
                content="No engagement data available yet.",
                data={"engagement": []},
            )

        lines = ["Engagement Analysis"]
        by_platform: Dict[str, List[SocialPost]] = {}
        for post in published:
            by_platform.setdefault(post.platform, []).append(post)

        for platform, posts in by_platform.items():
            total_engagement = sum(
                sum(p.engagement_metrics.values()) if p.engagement_metrics else 0 for p in posts
            )
            lines.append(f"\n{platform}: {len(posts)} posts, {total_engagement} total engagement")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"engagement": [p.to_dict() for p in published]},
        )

    def _handle_create_post(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Social Media Post Creation",
            "",
            "I can create posts for:",
            "- LinkedIn (professional, thought leadership)",
            "- Twitter/X (quick updates, engagement)",
            "- Instagram (visual content, stories)",
            "- Facebook (community engagement)",
            "- TikTok (short-form video scripts)",
            "",
            "Specify: platform, business, topic, and tone.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_engagement_response(self, query: str, context: Dict[str, str] | None = None) -> AgentResponse:
        lines = [
            "Engagement Response",
            "",
            "I can help you:",
            "- Draft responses to comments",
            "- Reply to DMs professionally",
            "- Handle customer inquiries",
            "- Manage reputation",
            "",
            "Share the comment/message and I'll draft a response.",
        ]
        return AgentResponse(agent=self.name, content="\n".join(lines))

    def _handle_overview(self) -> AgentResponse:
        by_status: Dict[str, int] = {}
        by_platform: Dict[str, int] = {}
        for post in self.posts:
            by_status[post.status] = by_status.get(post.status, 0) + 1
            by_platform[post.platform] = by_platform.get(post.platform, 0) + 1

        lines = [f"Social Media Overview: {len(self.posts)} total posts"]
        lines.append(f"\nBy status: {', '.join(f'{k}: {v}' for k, v in by_status.items())}")
        lines.append(f"By platform: {', '.join(f'{k}: {v}' for k, v in by_platform.items())}")

        return AgentResponse(
            agent=self.name,
            content="\n".join(lines),
            data={"posts": [p.to_dict() for p in self.posts]},
        )

    def _load_posts(self) -> List[SocialPost]:
        if not self.data_path.exists():
            return []
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            posts: List[SocialPost] = []
            for entry in data:
                try:
                    scheduled_time = None
                    if entry.get("scheduled_time"):
                        scheduled_time = datetime.fromisoformat(entry["scheduled_time"])
                        if scheduled_time.tzinfo is None:
                            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)

                    posts.append(
                        SocialPost(
                            platform=entry.get("platform", ""),
                            business=entry.get("business", ""),
                            content=entry.get("content", ""),
                            scheduled_time=scheduled_time,
                            status=entry.get("status", "draft"),
                            engagement_metrics=entry.get("engagement_metrics"),
                        )
                    )
                except Exception as exc:
                    LOGGER.debug("Skipping malformed social post: %s", exc)
            return posts
        except json.JSONDecodeError:
            LOGGER.warning("Invalid JSON in %s", self.data_path)
            return []

