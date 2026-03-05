import type { Metadata } from "next";
import { CTASection } from "./components/CTASection";
import { FeaturesSection } from "./components/FeaturesSection";
import { HeroSection } from "./components/HeroSection";
import { HowItWorksSection } from "./components/HowItWorksSection";
import { MarketingNav } from "./components/MarketingNav";
import { PreviewSection } from "./components/PreviewSection";

/**
 * 마케팅 페이지 메타데이터
 * SEO 최적화를 위한 메타 태그 설정
 */
export const metadata: Metadata = {
  title: "itsmegram - AI 인스타그램 분석 서비스",
  description:
    "AI로 나의 인스타그램을 분석하고 콘텐츠 성향, 라이프스타일, 성격 특징을 발견하세요. 무료 리포트를 생성하고 친구들과 공유하세요.",
  keywords: [
    "인스타그램 분석",
    "AI 분석",
    "인스타 분석",
    "itsmegram",
    "소셜 미디어 분석",
    "인스타그램 리포트",
    "AI 인사이트",
  ],
  openGraph: {
    title: "itsmegram - AI로 분석하는 나의 인스타그램",
    description:
      "AI가 분석하는 나만의 인스타그램 성향. 콘텐츠 스타일, 라이프스타일, 성격 특징을 한눈에 확인하세요.",
    type: "website",
    locale: "ko_KR",
    siteName: "itsmegram",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "itsmegram - AI 인스타그램 분석",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "itsmegram - AI 인스타그램 분석",
    description: "AI로 나의 인스타그램을 분석하고 특별한 인사이트를 받아보세요",
  },
  alternates: {
    canonical: "/marketing",
  },
};

/**
 * 마케팅 랜딩 페이지
 * 고객 유입용 획기적인 랜딩 페이지
 *
 * 구성 섹션:
 * 1. Hero 섹션 - 풀스크린 그라데이션 배경 + 애니메이션 타이틀
 * 2. 기능 소개 섹션 - 3열 그리드 카드 레이아웃
 * 3. 리포트 미리보기 섹션 - 캐러셀 형태 샘플 리포트
 * 4. 사용 방법 섹션 - 3단계 프로세스 시각화
 * 5. CTA 섹션 - 하단 강력한 콜투액션
 */
export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* 네비게이션 */}
      <MarketingNav />

      {/* Hero 섹션 */}
      <HeroSection />

      {/* 기능 소개 섹션 */}
      <FeaturesSection />

      {/* 리포트 미리보기 섹션 */}
      <PreviewSection />

      {/* 사용 방법 섹션 */}
      <HowItWorksSection />

      {/* CTA 섹션 */}
      <CTASection />

      {/* 푸터 */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-text text-transparent">
                itsmegram
              </span>
            </div>
            <p className="text-sm text-gray-400">
              © 2026 itsmegram. All rights reserved.
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-4 text-center sm:text-left">
            이 서비스는 Instagram과 관련이 없는 독립적인 서비스입니다.
          </p>
        </div>
      </footer>
    </main>
  );
}
