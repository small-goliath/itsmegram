/**
 * 리포트 관련 타입 정의
 * 백엔드 Report 모델과 동일한 구조
 */

// 기본 메트릭스
export interface BasicMetrics {
  avg_likes: number;
  avg_comments: number;
  engagement_rate: number;
  post_type_ratio: {
    image: number;
    video: number;
    carousel: number;
  };
}

// 콘텐츠 성향
export interface ContentTendency {
  categories: string[];
  visual_style: string;
  text_style: string;
  hashtag_pattern: string[];
}

// 라이프스타일
export interface Lifestyle {
  interests: string[];
  activity_pattern: string;
  consumption: string[];
}

// 성격 분석
export interface Personality {
  extroversion: string;
  expression_strength: number;
  communication: string;
}

// 네트워크 분석
export interface Network {
  engagement_quality: string;
  community_type: string;
}

// 성장 잠재력
export interface GrowthPotential {
  trend: string;
  consistency: string;
  suggestions: string[];
}

// 리포트 데이터
export interface Report {
  id: string;
  username: string;
  created_at: string;
  expires_at: string;
  basic_metrics: BasicMetrics;
  content_tendency: ContentTendency;
  lifestyle: Lifestyle;
  personality: Personality;
  network: Network;
  growth_potential: GrowthPotential;
  summary: string;
  profile_image_url: string;
  collected_posts_count: number;
  status: "processing" | "completed" | "failed";
  error_message?: string;
}

// 분석 요청 응답
export interface AnalysisResponse {
  report_id: string;
  status: string;
  message: string;
}

// 분석 상태 응답
export interface AnalysisStatus {
  report_id: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  message: string;
}

// 에러 응답
export interface ApiError {
  detail: string;
}
