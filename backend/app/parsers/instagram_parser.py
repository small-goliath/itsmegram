"""
Instagram JSON Parser
Parses web_profile_info API responses into structured data
"""

import re
from datetime import datetime
from typing import Dict, Any, List

from app.utils.exceptions import InstagramServiceError
import structlog

logger = structlog.get_logger()


class InstagramParser:
    """
    Parser for Instagram web_profile_info API responses
    - Extracts profile information
    - Extracts post data from timeline media edges
    """

    @staticmethod
    def parse_profile(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse profile data from web_profile_info API response

        Args:
            data: Raw JSON response from Instagram API

        Returns:
            Dictionary with parsed profile fields

        Raises:
            InstagramServiceError: If user data is not found
        """
        user = data.get("data", {}).get("user", {})

        if not user:
            raise InstagramServiceError("Invalid response: user data not found")

        # Handle profile picture URL (prefer HD version)
        profile_pic_url = user.get("profile_pic_url_hd") or user.get("profile_pic_url", "")

        return {
            "username": user.get("username", ""),
            "full_name": user.get("full_name", ""),
            "biography": user.get("biography", ""),
            "followers": user.get("edge_followed_by", {}).get("count", 0),
            "following": user.get("edge_follow", {}).get("count", 0),
            "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
            "is_private": user.get("is_private", False),
            "is_verified": user.get("is_verified", False),
            "profile_pic_url": profile_pic_url,
            "external_url": user.get("external_url", ""),
        }

    @staticmethod
    def parse_posts(data: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Parse posts from web_profile_info API response

        Args:
            data: Raw JSON response from Instagram API
            limit: Maximum number of posts to parse

        Returns:
            List of parsed post dictionaries
        """
        user = data.get("data", {}).get("user", {})
        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])

        posts = []
        for edge in edges[:limit]:
            node = edge.get("node", {})

            # Extract caption
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0].get("node", {}).get("text", "") if caption_edges else ""

            # Extract hashtags and mentions
            hashtags = InstagramParser._extract_hashtags(caption)
            mentions = InstagramParser._extract_mentions(caption)

            # Determine media type and URL
            is_video = node.get("is_video", False)
            media_url = node.get("display_url", "")

            # Handle carousel posts (multiple images)
            if node.get("__typename") == "GraphSidecar":
                # Get first media from sidecar
                sidecar_edges = node.get("edge_sidecar_to_children", {}).get("edges", [])
                if sidecar_edges:
                    first_child = sidecar_edges[0].get("node", {})
                    media_url = first_child.get("display_url", media_url)

            post_data = {
                "post_id": node.get("id", ""),
                "shortcode": node.get("shortcode", ""),
                "caption": caption,
                "likes": node.get("edge_liked_by", {}).get("count", 0),
                "comments": node.get("edge_media_to_comment", {}).get("count", 0),
                "media_url": media_url,
                "timestamp": datetime.fromtimestamp(node.get("taken_at_timestamp", 0)),
                "post_type": "video" if is_video else "image",
                "hashtags": hashtags,
                "mentions": mentions,
            }
            posts.append(post_data)

        logger.debug("posts_parsed", count=len(posts), limit=limit)
        return posts

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        """Extract hashtags from text"""
        if not text:
            return []
        # Find all #hashtag patterns, lowercase them
        hashtags = re.findall(r"#(\w+)", text)
        return [tag.lower() for tag in hashtags]

    @staticmethod
    def _extract_mentions(text: str) -> List[str]:
        """Extract @mentions from text"""
        if not text:
            return []
        # Find all @mention patterns, lowercase them
        mentions = re.findall(r"@(\w+)", text)
        return [mention.lower() for mention in mentions]


# Singleton instance
parser = InstagramParser()
