import type { Metadata } from "next";
import { UsernameForm } from "./components/UsernameForm";
import { FeatureCards } from "./components/FeatureCards";
import { Instagram, Sparkles } from "lucide-react";
import Link from "next/link";

/**
 * 홈 페이지 메타데이터
 */
export const metadata: Metadata = {
  title: "itsmegram - AI로 분석하는 나의 인스타그램",
  description:
    "인스타그램 계정을 AI로 분석하여 콘텐츠 성향, 라이프스타일, 성격 특징을 파악핳세요. 묣은 리포트를 생성하고 스토리로 공유할 수 있습니다.",
  keywords: ["인스타그램", "AI 분석", "인스타 분석", "itsmegram", "소셜 미디어 분석"],
  openGraph: {
    title: "itsmegram - AI로 분석하는 나의 인스타그램",
    description: "인스타그램 계정을 AI로 분석하여 나만의 특징을 발견하세요",
    type: "website",
  },
};

/**
 * 홈 페이지 컴포넌트
 * Hero 섹션, Username 입력 폼, 기능 소개 카드를 포함
 */
export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero 섹션 */}
      <section className="relative flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-16 sm:py-24 lg:py-32 bg-gradient-to-br from-yellow-400 via-pink-500 to-purple-600">
        {/* 배경 장식 */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-white/5 rounded-full blur-3xl" />
          <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-white/5 rounded-full blur-3xl" />
        </div>

        {/* 콘텐츠 */}
        <div className="relative z-10 w-full max-w-4xl mx-auto text-center">
          {/* 마케팅 페이지 링크 */}
          <div className="absolute top-4 right-4 sm:top-6 sm:right-6">
            <Link
              href="/marketing"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm border border-white/30 text-white text-sm font-medium hover:bg-white/30 transition-colors min-h-[44px]"
            >
              <Sparkles className="w-4 h-4" />
              <span className="hidden sm:inline">서비스 소개</span>
            </Link>
          </div>

          {/* 로고 아이콘 */}
          <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white/20 backdrop-blur-sm mb-6 sm:mb-8">
            <Instagram className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
          </div>

          {/* 서비스 타이틀 */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 sm:mb-6 tracking-tight">
            itsmegram
          </h1>

          {/* 서비스 설명 */}
          <p className="text-lg sm:text-xl lg:text-2xl text-white/90 mb-8 sm:mb-10 font-medium">
            AI로 분석하는 나의 인스타그램
          </p>

          {/* 서비스 상세 설명 */}
          <p className="text-base sm:text-lg text-white/80 mb-10 sm:mb-12 max-w-2xl mx-auto leading-relaxed">
            인스타그램 계정을 AI가 심층 분석하여
            <br className="hidden sm:block" />
            콘텐츠 성향과 라이프스타일을 알려드립니다
          </p>

          {/* Username 입력 폼 */}
          <UsernameForm />
        </div>

        {/* 스크롤 힌트 */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 rounded-full border-2 border-white/50 flex items-start justify-center p-2">
            <div className="w-1 h-2 bg-white/70 rounded-full" />
          </div>
        </div>
      </section>

      {/* 기능 소개 섹션 */}
      <section className="py-16 sm:py-20 lg:py-24 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          {/* 섹션 헤더 */}
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              itsmegram의 특별한 기능
            </h2>
            <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
              AI 기술을 활용한 다양한 기능으로
              <br className="hidden sm:block" />
              나의 인스타그램을 새롭게 발견하세요
            </p>
          </div>

          {/* 기능 카드 그리드 */}
          <FeatureCards />
        </div>
      </section>

      {/* 푸터 섹션 */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 bg-white border-t border-gray-100">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-sm text-gray-500">
            © 2025 itsmegram. All rights reserved.
          </p>
          <p className="text-xs text-gray-400 mt-2">
            이 서비스는 Instagram과 관련이 없는 독립적인 서비스입니다.
          </p>
        </div>
      </footer>
    </div>
  );
}
