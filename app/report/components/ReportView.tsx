"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { AlertCircle, ArrowLeft, RefreshCw } from "lucide-react";
import { ReportHeader } from "./ReportHeader";
import { SummarySection } from "./SummarySection";
import { ContentTendencySection } from "./ContentTendencySection";
import { LifestyleSection } from "./LifestyleSection";
import { PersonalitySection } from "./PersonalitySection";
import { NetworkSection } from "./NetworkSection";
import { GrowthPotentialSection } from "./GrowthPotentialSection";
import { ShareActions } from "./ShareActions";
import { ReportSkeleton } from "./ReportSkeleton";
import { getReport, isReportExpired, checkAnalysisStatus } from "../lib/api";
import { Report } from "../types";

interface ReportViewProps {
  reportId: string;
}

/**
 * 리포트 뷰 컴포넌트
 * 리포트 데이터를 조회하고 각 섹션을 렌더링
 */
export function ReportView({ reportId }: ReportViewProps) {
  const router = useRouter();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getReport(reportId);

        // 만료된 리포트 확인
        if (isReportExpired(data.expires_at)) {
          setError("이 리포트는 만료되었습니다. 새로 분석해주세요.");
          setLoading(false);
          return;
        }

        // 분석 중인 경우 상태 확인
        if (data.status === "processing") {
          // 폴리로 상태 확인
          const checkStatus = async () => {
            try {
              const status = await checkAnalysisStatus(reportId);
              if (status.status === "completed") {
                const updatedReport = await getReport(reportId);
                setReport(updatedReport);
                setLoading(false);
              } else if (status.status === "failed") {
                setError(status.message || "분석에 실패했습니다.");
                setLoading(false);
              } else {
                // 계속 처리 중, 2초 후 다시 확인
                setTimeout(checkStatus, 2000);
              }
            } catch (err) {
              setError("상태 확인 중 오류가 발생했습니다.");
              setLoading(false);
            }
          };

          checkStatus();
          return;
        }

        // 분석 실패한 경우
        if (data.status === "failed") {
          setError(data.error_message || "분석에 실패했습니다.");
          setLoading(false);
          return;
        }

        setReport(data);
        setLoading(false);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "리포트를 불러오는데 실패했습니다."
        );
        setLoading(false);
      }
    };

    fetchReport();
  }, [reportId]);

  // 로딩 중
  if (loading) {
    return <ReportSkeleton />;
  }

  // 에러 상태
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          리포트를 불러올 수 없습니다
        </h2>
        <p className="text-gray-600 text-center max-w-md mb-6">{error}</p>
        <div className="flex gap-3">
          <Button onClick={() => router.push("/")} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            홈으로 돌아가기
          </Button>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  // 리포트가 없는 경우
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          리포트를 찾을 수 없습니다
        </h2>
        <p className="text-gray-600 text-center max-w-md mb-6">
          요청하신 리포트가 존재하지 않거나 삭제되었습니다.
        </p>
        <Button onClick={() => router.push("/")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          홈으로 돌아가기
        </Button>
      </div>
    );
  }

  // 리포트 표시
  return (
    <div className="space-y-6">
      {/* 뒤로 가기 버튼 */}
      <Button
        variant="ghost"
        onClick={() => router.push("/")}
        className="mb-4 -ml-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        홈으로 돌아가기
      </Button>

      {/* 리포트 헤더 */}
      <ReportHeader
        username={report.username}
        profileImageUrl={report.profile_image_url}
        collectedPostsCount={report.collected_posts_count}
        basicMetrics={report.basic_metrics || {
          engagement_rate: 0,
          avg_likes: 0,
          avg_comments: 0,
          followers: 0,
          following: 0,
          posts: 0,
        }}
      />

      {/* 핵심 요약 */}
      <SummarySection summary={report.summary} />

      {/* 섹션 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ContentTendencySection data={report.content_tendency || {
          categories: [],
          visual_style: "",
          text_style: "",
          hashtag_pattern: [],
          posting_frequency: "",
        }} />
        <LifestyleSection data={report.lifestyle || {
          interests: [],
          activity_pattern: "",
          consumption: [],
        }} />
        <PersonalitySection data={report.personality || {
          expression_strength: 0,
          extroversion: "",
          communication: "",
        }} />
        <NetworkSection data={report.network || {
          engagement_quality: "",
          community_type: "",
        }} />
      </div>

      {/* 성장 잠재력 (전체 너비) */}
      <GrowthPotentialSection data={report.growth_potential || {
        trend: "",
        consistency: "",
        suggestions: [],
      }} />

      {/* 공유 액션 */}
      <ShareActions reportId={(report as any).report_id || report.id} username={report.username} />

      {/* 생성 시간 정보 */}
      <div className="text-center text-xs text-gray-400 pt-4">
        <p>
          생성: {new Date(report.created_at).toLocaleString("ko-KR")}
          {" "}| 만료: {new Date(report.expires_at).toLocaleString("ko-KR")}
        </p>
      </div>
    </div>
  );
}
