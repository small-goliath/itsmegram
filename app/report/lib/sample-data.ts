/**
 * 샘플 리포트 데이터
 * UI 테스트 및 개발용
 */

import { Report } from "../types";

export const sampleReport: Report = {
  id: "sample-report-123",
  username: "traveler_kim",
  created_at: new Date().toISOString(),
  expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  profile_image_url: "",
  collected_posts_count: 24,
  status: "completed",
  error_message: undefined,

  basic_metrics: {
    avg_likes: 128.5,
    engagement_rate: 4.8,
    post_type_ratio: {
      image: 0.6,
      video: 0.25,
      carousel: 0.15,
    },
  },

  content_tendency: {
    categories: ["여행", "일상", "음식", "사진"],
    visual_style:
      "밝고 선명한 색감을 사용하며, 자연광을 활용한 따뜻한 분위기의 사진이 특징입니다. 구도가 안정적이며 미적인 감각이 뛰어납니다.",
    text_style:
      "친근하고 자연스러운 문체를 사용하며, 팔로워와의 소통을 중시하는 것으로 보입니다. 이모지를 적절히 활용하여 가독성이 좋습니다.",
    hashtag_pattern: [
      "여행스타그램",
      "일상기록",
      "맛집탐방",
      "사진일기",
      "주말나들이",
    ],
  },

  lifestyle: {
    interests: ["여행", "사진", "음식", "울동", "독서"],
    activity_pattern:
      "주말에 활동이 집중되며, 특히 토요일 오후부터 일요일 저녁까지 게시물 업로드가 많습니다. 평일에는 저녁 시간대에 간헐적으로 활동합니다.",
    consumption: [
      "체험 중심 소비",
      "가성비 중시",
      "브랜드보다는 실용성 우선",
      "여행 및 문화생활 투자",
    ],
  },

  personality: {
    extroversion:
      "외향적인 성향으로 보이며, 새로운 경험을 즐기고 타인과의 교류를 선호합니다. 적극적으로 자신의 경험을 공유하는 편입니다.",
    expression_strength: 78,
    communication:
      "친근하고 개방적인 커뮤니케이션 스타일로 보입니다. 팔로워의 댓글에 적극적으로 반응하며 소통을 중시합니다.",
  },

  network: {
    engagement_quality:
      "높은 참여 품질을 보이며, 팔로워들과의 상호작용이 활발합니다. 댓글과 좋아요 비율이 균형 잡혀 있어 건전한 커뮤니티를 형성하고 있습니다.",
    community_type:
      "관심사 기반 커뮤니티로 보이며, 특히 여행과 일상 콘텐츠에 관심 있는 팔로워들이 주를 이룹니다.",
  },

  growth_potential: {
    trend: "안정적인 성장 추세로 보이며, 꾸준한 콘텐츠 업로드로 팔로워가 증가하고 있습니다.",
    consistency:
      "주 2-3회 꾸준한 게시물 업로드를 유지하고 있어 일관성이 높습니다. 콘텐츠 품질도 안정적입니다.",
    suggestions: [
      "릴스 콘텐츠 비율을 늘려 알고리즘 노출 증가",
      "스토리를 활용한 일상 소통 강화",
      "게시 시간대를 저녁 7-9시로 최적화",
      "여행 관련 해시태그 다양화",
    ],
  },

  summary:
    "이 계정은 여행과 일상 콘텐츠를 중심으로 활동하는 외향적인 성향의 사용자입니다. 밝고 따뜻한 시각적 스타일과 친근한 문체로 팔로워와의 소통을 중시하며, 꾸준한 활동으로 안정적인 성장을 보이고 있습니다. 릴스 콘텐츠 강화와 게시 시간 최적화를 통해 더 큰 성장이 기대됩니다.",
};

/**
 * 만료된 리포트 샘플 데이터
 */
export const expiredSampleReport: Report = {
  ...sampleReport,
  id: "expired-report-456",
  expires_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
};

/**
 * 분석 실패 샘플 데이터
 */
export const failedSampleReport: Report = {
  ...sampleReport,
  id: "failed-report-789",
  status: "failed",
  error_message: "인스타그램 데이터 수집 중 오류가 발생했습니다. 계정이 비공개이거나 존재하지 않는 것으로 보입니다.",
};

/**
 * 분석 중 샘플 데이터
 */
export const processingSampleReport: Report = {
  ...sampleReport,
  id: "processing-report-000",
  status: "processing",
};
