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
    <Suspense fallback={<ReportSkeleton />}>
      <ReportContent username={username} />
    </Suspense>
  );
}
