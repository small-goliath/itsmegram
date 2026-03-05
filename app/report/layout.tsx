import type { Metadata } from "next";

/**
 * 리포트 페이지 레이아웃
 * 리포트 관련 페이지들의 공통 구조 정의
 */
export const metadata: Metadata = {
  title: "분석 리포트",
  description: "인스타그램 계정 분석 리포트",
};

export default function ReportLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <a
            href="/"
            className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-text text-transparent"
          >
            itsmegram
          </a>
          <nav className="flex items-center gap-4">
            <a
              href="/marketing"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              서비스 소개
            </a>
            <a
              href="/"
              className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              새로 분석하기
            </a>
          </nav>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {children}
      </main>

      {/* 푸터 */}
      <footer className="border-t border-gray-200 mt-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2024 itsmegram. AI 기반 인스타그램 계정 분석 서비스
          </p>
        </div>
      </footer>
    </div>
  );
}
