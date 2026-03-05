import type { Metadata } from "next";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { ReportView } from "../components/ReportView";
import { ReportSkeleton } from "../components/ReportSkeleton";
import { getReport } from "../lib/api";

/**
 * 동적 메타데이터 생성
 * 특정 리포트의 사용자명을 사용하여 메타데이터 동적 생성
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  try {
    const { id } = await params;
    const report = await getReport(id);

    return {
      title: `${report.username}님의 인스타그램 분석 리포트`,
      description: `${report.username}님의 인스타그램 계정 AI 분석 리포트입니다. 콘텐츠 성향, 라이프스타일, 성격 특징을 확인하세요.`,
      openGraph: {
        title: `${report.username}님의 인스타그램 분석 리포트 | itsmegram`,
        description: `${report.username}님의 인스타그램 계정 AI 분석 리포트입니다.`,
        type: "article",
      },
    };
  } catch {
    return {
      title: "리포트를 찾을 수 없습니다",
      description: "요청하신 리포트를 찾을 수 없습니다.",
    };
  }
}

/**
 * 특정 리포트 조회 페이지
 * URL의 id 파라미터를 사용하여 특정 리포트를 조회
 */
export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <Suspense fallback={<ReportSkeleton />}>
      <ReportView reportId={id} />
    </Suspense>
  );
}
