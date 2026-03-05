import type { Metadata } from "next";
import { Suspense } from "react";
import { ReportContent } from "./components/ReportContent";
import { ReportSkeleton } from "./components/ReportSkeleton";

/**
 * 동적 메타데이터 생성
 * URL의 username 파라미터를 사용하여 메타데이터 동적 생성
 */
export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}): Promise<Metadata> {
  const params = await searchParams;
  const username = params.username as string | undefined;

  if (username) {
    return {
      title: `${username}님의 인스타그램 분석 리포트`,
      description: `${username}님의 인스타그램 계정 AI 분석 리포트입니다.`,
    };
  }

  return {
    title: "분석 리포트",
    description: "인스타그램 계정 분석 리포트",
  };
}

/**
 * 리포트 페이지
 * username query param을 받아 분석 결과를 표시
 */
export default async function ReportPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const username = params.username as string | undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <a
            href="/"
            className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-text text-transparent"
          >
            itsmegram
          </a>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <Suspense fallback={<ReportSkeleton />}>
          <ReportContent username={username} />
        </Suspense>
      </main>
    </div>
  );
}
