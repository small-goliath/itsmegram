"""
itsmegram - AI 분석 서비스 (Moonshot AI 연동)
인스타그램 계정 데이터를 AI로 분석하여 인사이트 제공
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
import structlog

from app.models.schemas import (
    AIInsight,
    AnalysisMetrics,
    InstagramData,
    PostData,
    ProfileData,
    ReportData,
)
from app.services.cache_service import cache_service
from app.utils.exceptions import (
    AIServiceError,
    MoonshotAPIError,
    AnalysisParsingError,
    AnalysisTimeoutError,
)

logger = structlog.get_logger()


class AIService:
    """
    AI 분석 서비스
    - Moonshot AI API를 사용한 인스타그램 계정 분석
    - 분석 결과 후처리 및 정규화
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        AI 서비스 초기화

        Args:
            api_key: Moonshot API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY", "")
        if not self.api_key:
            logger.warning("moonshot_api_key_not_set")

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.model = "moonshot-v1-8k"
        self.timeout_seconds = 30
        self.max_retries = 2

        logger.info("ai_service_initialized", model=self.model)

    def _format_posts(self, posts: List[PostData]) -> str:
        """
        게시물 목록을 프롬프트용 문자열로 포맷팅
        """
        formatted = []
        for idx, post in enumerate(posts[:12], 1):  # 최대 12개 게시물만 포함
            post_info = f"""
게시물 {idx}:
- 캡션: {post.caption[:200] if post.caption else '(없음)'}...
- 좋아요: {post.likes}
- 댓글: {post.comments}
- 타입: {post.post_type}
- 해시태그: {', '.join(post.hashtags[:10]) if post.hashtags else '(없음)'}
- 게시일: {post.timestamp.strftime('%Y-%m-%d') if post.timestamp else '알 수 없음'}
"""
            formatted.append(post_info)
        return "\n".join(formatted)

    def _build_analysis_prompt(self, data: InstagramData) -> str:
        """
        AI 분석을 위한 프롬프트 생성

        Args:
            data: 인스타그램 데이터 (프로필 + 게시물)

        Returns:
            str: 분석 프롬프트
        """
        profile = data.profile
        posts = data.posts

        # 기본 메트릭스 계산
        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        avg_likes = total_likes / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0
        engagement_rate = ((total_likes + total_comments) / (profile.followers * len(posts)) * 100) if profile.followers and posts else 0

        # 모든 해시태그 수집
        all_hashtags = []
        for post in posts:
            all_hashtags.extend(post.hashtags)
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return f"""다음 인스타그램 계정 데이터를 분석하여 JSON 형식으로 리포트를 생성해주세요:

## 프로필 정보
- 사용자명: {profile.username}
- 전체 이름: {profile.full_name or '(없음)'}
- 팔로워: {profile.followers:,}
- 팔로잉: {profile.following:,}
- 게시물 수: {profile.posts_count}
- 소개: {profile.biography or '(없음)'}
- 인증 계정: {'예' if profile.is_verified else '아니오'}

## 기본 통계 (참고용)
- 평균 좋아요: {avg_likes:.1f}
- 평균 댓글: {avg_comments:.1f}
- 참여율: {engagement_rate:.2f}%
- 주요 해시태그: {', '.join([f'#{tag}({count}회)' for tag, count in top_hashtags]) if top_hashtags else '(없음)'}

## 최근 게시물 {len(posts)}개
{self._format_posts(posts)}

## 출력 형식
다음 JSON 구조로 분석 결과를 출력해주세요. 모든 값은 추정(~로 보입니다) 표현을 사용하고 객관적으로 작성해주세요:

{{
    "basic_metrics": {{
        "avg_likes": 숫자(0-100 범위로 정규화된 값),
        "engagement_rate": 숫자(0-100 범위로 정규화된 값),
        "post_type_ratio": {{"image": 비율, "video": 비율, "carousel": 비율}}
    }},
    "content_tendency": {{
        "categories": ["카테고리1", "카테고리2"],
        "visual_style": "시각적 스타일 설명 (~스타일로 보입니다)",
        "text_style": "텍스트 스타일 설명 (~한 것으로 추정됩니다)",
        "hashtag_pattern": ["주요 패턴1", "주요 패턴2"]
    }},
    "lifestyle": {{
        "interests": ["관심사1", "관심사2"],
        "activity_pattern": "활동 패턴 (~할 것으로 보입니다)",
        "consumption": ["소비 성향1", "소비 성향2"]
    }},
    "personality": {{
        "extroversion": "외향성 수준 (~한 것으로 추정됩니다)",
        "expression_strength": 숫자(0-100),
        "communication": "커뮤니케이션 스타일 (~스타일로 보입니다)"
    }},
    "network": {{
        "engagement_quality": "참여 품질 (~한 것으로 추정됩니다)",
        "community_type": "커뮤니티 유형 (~유형으로 보입니다)"
    }},
    "growth_potential": {{
        "trend": "성장 추세 (~추세로 보입니다)",
        "consistency": "일관성 수준 (~한 것으로 추정됩니다)",
        "suggestions": ["개선 제안1", "개선 제안2", "개선 제안3"]
    }},
    "summary": "5-7줄의 요약 (각 문장은 ~로 보입니다, ~할 것으로 추정됩니다 등의 표현 사용)"
}}

## 주의사항
1. 모든 분석은 추정 표현(~로 보입니다, ~할 것으로 추정됩니다, ~것으로 판단됩니다)을 사용하세요.
2. 객관적이고 중립적인 시각에서 분석하세요.
3. 수치는 0-100 범위로 정규화하여 제공하세요.
4. summary는 5-7줄로 구성하고, 각 문장은 추정 표현을 포함하세요.
5. JSON 형식만 출력하고, 다른 설명은 포함하지 마세요."""

    def _normalize_value(self, value: float, min_val: float = 0, max_val: float = 100) -> float:
        """
        값을 0-100 범위로 정규화
        """
        if max_val == min_val:
            return 50.0
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0.0, min(100.0, normalized))

    def _add_estimation_phrases(self, text: str) -> str:
        """
        텍스트에 추정 표현 추가
        """
        if not text:
            return text

        # 이미 추정 표현이 있는지 확인
        estimation_patterns = [
            r'~로 보입니다',
            r'~할 것으로 추정됩니다',
            r'~것으로 판단됩니다',
            r'~것으로 예상됩니다',
            r'~한 것으로 보입니다',
        ]

        for pattern in estimation_patterns:
            if re.search(pattern, text):
                return text

        # 추정 표현 추가
        if text.endswith('.'):
            text = text[:-1]

        return f"{text} 것으로 추정됩니다."

    def _post_process_analysis(self, analysis: Dict[str, Any], instagram_data: InstagramData) -> Dict[str, Any]:
        """
        AI 분석 결과 후처리

        Args:
            analysis: AI가 생성한 분석 결과
            instagram_data: 원본 인스타그램 데이터

        Returns:
            Dict: 후처리된 분석 결과
        """
        # basic_metrics 정규화
        if "basic_metrics" in analysis:
            metrics = analysis["basic_metrics"]

            # avg_likes 정규화 (0-10000 범위를 0-100으로)
            if "avg_likes" in metrics:
                metrics["avg_likes"] = self._normalize_value(
                    float(metrics["avg_likes"]), 0, 10000
                )

            # engagement_rate 정규화 (0-10% 범위를 0-100으로)
            if "engagement_rate" in metrics:
                metrics["engagement_rate"] = self._normalize_value(
                    float(metrics["engagement_rate"]), 0, 10
                )

        # personality.expression_strength 정규화
        if "personality" in analysis and "expression_strength" in analysis["personality"]:
            analysis["personality"]["expression_strength"] = self._normalize_value(
                float(analysis["personality"]["expression_strength"]), 0, 100
            )

        # summary 길이 확인 및 조정
        if "summary" in analysis:
            summary = analysis["summary"]
            sentences = re.split(r'[.!?。]+', summary)
            sentences = [s.strip() for s in sentences if s.strip()]

            # 5-7줄로 조정
            if len(sentences) < 5:
                # 문장이 부족하면 추정 표현 추가
                summary = self._add_estimation_phrases(summary)
            elif len(sentences) > 7:
                # 문장이 너무 많으면 처음 7개만 사용
                summary = '. '.join(sentences[:7]) + '.'

            analysis["summary"] = summary

        # 모든 텍스트 필드에 추정 표현 확인
        text_fields = [
            ("content_tendency", "visual_style"),
            ("content_tendency", "text_style"),
            ("lifestyle", "activity_pattern"),
            ("personality", "extroversion"),
            ("personality", "communication"),
            ("network", "engagement_quality"),
            ("network", "community_type"),
            ("growth_potential", "trend"),
            ("growth_potential", "consistency"),
        ]

        for section, field in text_fields:
            if section in analysis and field in analysis[section]:
                text = analysis[section][field]
                if text and not any(pattern in text for pattern in ['보입니다', '추정됩니다', '판단됩니다', '예상됩니다']):
                    analysis[section][field] = self._add_estimation_phrases(text)

        return analysis

    async def analyze_profile(self, instagram_data: InstagramData) -> Dict[str, Any]:
        """
        인스타그램 프로필 AI 분석 수행

        Args:
            instagram_data: 인스타그램 데이터 (프로필 + 게시물)

        Returns:
            Dict: AI 분석 결과

        Raises:
            MoonshotAPIError: API 호출 오류
            AnalysisParsingError: 결과 파싱 오류
            AnalysisTimeoutError: 타임아웃
        """
        if not self.api_key:
            raise MoonshotAPIError("MOONSHOT_API_KEY is not set")

        prompt = self._build_analysis_prompt(instagram_data)

        try:
            logger.info(
                "starting_ai_analysis",
                username=instagram_data.profile.username,
                posts_count=len(instagram_data.posts),
            )

            # 동기식 OpenAI 클라이언트를 비동기로 실행
            import asyncio
            loop = asyncio.get_event_loop()

            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "당신은 인스타그램 계정 분석 전문가입니다. 데이터를 객관적으로 분석하고 추정 표현을 사용하여 의견을 제시해주세요."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"},
                        timeout=self.timeout_seconds,
                    )
                ),
                timeout=self.timeout_seconds + 5  # 추가 여유 시간
            )

            content = response.choices[0].message.content

            if not content:
                raise AnalysisParsingError("Empty response from AI")

            # JSON 파싱
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error", content=content[:500], error=str(e))
                raise AnalysisParsingError(
                    f"Failed to parse AI response as JSON: {str(e)}",
                    raw_content=content
                )

            # 후처리
            analysis = self._post_process_analysis(analysis, instagram_data)

            logger.info(
                "ai_analysis_completed",
                username=instagram_data.profile.username,
                has_summary="summary" in analysis,
            )

            return analysis

        except asyncio.TimeoutError:
            logger.error("analysis_timeout", username=instagram_data.profile.username)
            raise AnalysisTimeoutError(self.timeout_seconds)

        except openai.APIError as e:
            logger.error("moonshot_api_error", error=str(e))
            raise MoonshotAPIError(f"Moonshot API error: {str(e)}", original_error=e)

        except openai.AuthenticationError as e:
            logger.error("moonshot_auth_error", error=str(e))
            raise MoonshotAPIError("Invalid Moonshot API key", original_error=e)

        except Exception as e:
            if isinstance(e, AIServiceError):
                raise
            logger.error("unexpected_analysis_error", error=str(e))
            raise AIServiceError(f"Unexpected error during analysis: {str(e)}")

    def _convert_to_ai_insights(self, analysis: Dict[str, Any]) -> List[AIInsight]:
        """
        AI 분석 결과를 AIInsight 모델 리스트로 변환
        """
        insights = []

        # 기본 메트릭스 인사이트
        if "basic_metrics" in analysis:
            metrics = analysis["basic_metrics"]
            insights.append(AIInsight(
                category="engagement",
                title="참여도 분석",
                description=f"게시물 평균 좋아요 점수: {metrics.get('avg_likes', 0):.1f}/100, 참여율 점수: {metrics.get('engagement_rate', 0):.1f}/100",
                score=int(metrics.get('engagement_rate', 0) / 10),
                recommendations=["참여율을 높이기 위한 콘텐츠 개선"],
            ))

        # 콘텐츠 성향 인사이트
        if "content_tendency" in analysis:
            content = analysis["content_tendency"]
            insights.append(AIInsight(
                category="content",
                title="콘텐츠 성향",
                description=f"주요 카테고리: {', '.join(content.get('categories', []))}. 시각적 스타일: {content.get('visual_style', '분석 불가')}",
                score=7,
                recommendations=["일관된 브랜드 아이덴티티 유지"],
            ))

        # 라이프스타일 인사이트
        if "lifestyle" in analysis:
            lifestyle = analysis["lifestyle"]
            insights.append(AIInsight(
                category="lifestyle",
                title="라이프스타일 분석",
                description=f"관심사: {', '.join(lifestyle.get('interests', []))}. 활동 패턴: {lifestyle.get('activity_pattern', '분석 불가')}",
                score=6,
                recommendations=["관심사 기반 콘텐츠 강화"],
            ))

        # 성격 인사이트
        if "personality" in analysis:
            personality = analysis["personality"]
            insights.append(AIInsight(
                category="personality",
                title="성격 특성",
                description=f"외향성: {personality.get('extroversion', '분석 불가')}. 표현력 점수: {personality.get('expression_strength', 0):.0f}/100",
                score=int(personality.get('expression_strength', 50) / 10),
                recommendations=["개인적인 브랜딩 강화"],
            ))

        # 네트워크 인사이트
        if "network" in analysis:
            network = analysis["network"]
            insights.append(AIInsight(
                category="network",
                title="네트워크 분석",
                description=f"참여 품질: {network.get('engagement_quality', '분석 불가')}. 커뮤니티 유형: {network.get('community_type', '분석 불가')}",
                score=6,
                recommendations=["커뮤니티 참여 강화"],
            ))

        # 성장 잠재력 인사이트
        if "growth_potential" in analysis:
            growth = analysis["growth_potential"]
            insights.append(AIInsight(
                category="growth",
                title="성장 잠재력",
                description=f"성장 추세: {growth.get('trend', '분석 불가')}. 일관성: {growth.get('consistency', '분석 불가')}",
                score=7,
                recommendations=growth.get('suggestions', ["꾸준한 콘텐츠 게시"]),
            ))

        return insights

    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> int:
        """
        종합 점수 계산
        """
        scores = []

        # 기본 메트릭스 점수
        if "basic_metrics" in analysis:
            metrics = analysis["basic_metrics"]
            scores.append(metrics.get("engagement_rate", 50))

        # 표현력 점수
        if "personality" in analysis:
            scores.append(analysis["personality"].get("expression_strength", 50))

        # 기본값
        if not scores:
            return 50

        return int(sum(scores) / len(scores))

    def _build_report_from_cache(
        self,
        instagram_data: InstagramData,
        cached_analysis: Dict[str, Any]
    ) -> ReportData:
        """
        캐시된 분석 결과로 ReportData 생성

        Args:
            instagram_data: 인스타그램 데이터
            cached_analysis: 캐시된 분석 결과

        Returns:
            ReportData: 완성된 리포트
        """
        posts = instagram_data.posts
        profile = instagram_data.profile

        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        avg_likes = total_likes / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0

        # 모든 해시태그 수집
        all_hashtags = []
        for post in posts:
            all_hashtags.extend(post.hashtags)
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        top_hashtags = [tag for tag, _ in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

        # 게시 빈도 분석
        posting_frequency = "weekly"
        if len(posts) >= 2 and posts[0].timestamp and posts[-1].timestamp:
            date_range = (posts[0].timestamp - posts[-1].timestamp).days
            if date_range > 0:
                posts_per_day = len(posts) / date_range
                if posts_per_day >= 1:
                    posting_frequency = "daily"
                elif posts_per_day >= 0.3:
                    posting_frequency = "weekly"
                else:
                    posting_frequency = "monthly"

        metrics = AnalysisMetrics(
            engagement_rate=cached_analysis.get("basic_metrics", {}).get("engagement_rate", 0),
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            posting_frequency=posting_frequency,
            top_hashtags=top_hashtags,
            content_themes=cached_analysis.get("content_tendency", {}).get("categories", []),
        )

        # AI 인사이트 변환
        ai_insights = self._convert_to_ai_insights(cached_analysis)

        # 종합 점수
        overall_score = self._calculate_overall_score(cached_analysis)

        return ReportData(
            profile=profile,
            metrics=metrics,
            recent_posts=posts,
            ai_insights=ai_insights,
            overall_score=overall_score,
            generated_at=datetime.utcnow(),
        )

    async def generate_report(
        self,
        instagram_data: InstagramData,
        use_cache: bool = True
    ) -> ReportData:
        """
        인스타그램 데이터로부터 완전한 리포트 생성

        Args:
            instagram_data: 인스타그램 데이터
            use_cache: 캐시 사용 여부 (기본 True)

        Returns:
            ReportData: 완성된 리포트
        """
        username = instagram_data.profile.username

        # 캐시 확인
        if use_cache:
            cached_analysis = await cache_service.get_cached_analysis(username)
            if cached_analysis:
                logger.info("analysis_cache_hit", username=username)
                # 캐시된 데이터로 ReportData 생성
                return self._build_report_from_cache(
                    instagram_data,
                    cached_analysis
                )

        # AI 분석 수행
        analysis = await self.analyze_profile(instagram_data)

        # 분석 결과 캐싱 (1시간)
        if use_cache:
            await cache_service.cache_analysis(username, analysis, ttl=3600)
            logger.info("analysis_cached", username=username, ttl=3600)

        # 기본 메트릭스 계산
        posts = instagram_data.posts
        profile = instagram_data.profile

        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        avg_likes = total_likes / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0

        # 모든 해시태그 수집
        all_hashtags = []
        for post in posts:
            all_hashtags.extend(post.hashtags)
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        top_hashtags = [tag for tag, _ in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

        # 게시 빈도 분석
        posting_frequency = "weekly"  # 기본값
        if len(posts) >= 2 and posts[0].timestamp and posts[-1].timestamp:
            date_range = (posts[0].timestamp - posts[-1].timestamp).days
            if date_range > 0:
                posts_per_day = len(posts) / date_range
                if posts_per_day >= 1:
                    posting_frequency = "daily"
                elif posts_per_day >= 0.3:
                    posting_frequency = "weekly"
                else:
                    posting_frequency = "monthly"

        metrics = AnalysisMetrics(
            engagement_rate=analysis.get("basic_metrics", {}).get("engagement_rate", 0),
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            posting_frequency=posting_frequency,
            top_hashtags=top_hashtags,
            content_themes=analysis.get("content_tendency", {}).get("categories", []),
        )

        # AI 인사이트 변환
        ai_insights = self._convert_to_ai_insights(analysis)

        # 종합 점수
        overall_score = self._calculate_overall_score(analysis)

        return ReportData(
            profile=profile,  # ProfileData 타입 확인 필요
            metrics=metrics,
            recent_posts=posts,
            ai_insights=ai_insights,
            overall_score=overall_score,
            generated_at=datetime.utcnow(),
        )


# 싱글톤 인스턴스
ai_service = AIService()