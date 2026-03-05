"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, ArrowLeft, RefreshCw } from "lucide-react";
import { ReportSkeleton } from "../components/ReportSkeleton";
import { sampleReport } from "../lib/sample-data";
import { ReportHeader } from "../components/ReportHeader";
import { SummarySection } from "../components/SummarySection";
import { ContentTendencySection } from "../components/ContentTendencySection";
import { LifestyleSection } from "../components/LifestyleSection";
import { PersonalitySection } from "../components/PersonalitySection";
import { NetworkSection } from "../components/NetworkSection";
import { GrowthPotentialSection } from "../components/GrowthPotentialSection";
import { ShareActions } from "../components/ShareActions";
import { Report } from "../types";

/**
 * 리포트 UI 테스트 페이지
 * 개발 및 테스트용 - 다양한 상태의 리포트 UI 확인 가능
 */
export default function ReportTestPage() {
  const [activeView, setActiveView] = useState<
    "sample" | "expired" | "failed" | "loading" | null
  >(null);

  return (
    <div className="space-y-8">
      {/* 테스트 페이지 헤더 */}
      <div className="text-center py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          리포트 UI 테스트
        </h1>
        <p className="text-gray-600">
          다양한 상태의 리포트 UI를 미리 확인할 수 있습니다
        </p>
      </div>

      {/* 테스트 옵션 카드 */}
      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>테스트 시나리오 선택</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              onClick={() => setActiveView("sample")}
              variant={activeView === "sample" ? "default" : "outline"}
              className="h-auto py-4 flex flex-col items-center gap-2"
            >
              <span className="text-2xl">✅</span>
              <span className="text-sm">정상 리포트</span>
            </Button>

            <Button
              onClick={() => setActiveView("loading")}
              variant={activeView === "loading" ? "default" : "outline"}
              className="h-auto py-4 flex flex-col items-center gap-2"
            >
              <span className="text-2xl">⏳</span>
              <span className="text-sm">로딩 상태</span>
            </Button>

            <Button
              onClick={() => setActiveView("expired")}
              variant={activeView === "expired" ? "default" : "outline"}
              className="h-auto py-4 flex flex-col items-center gap-2"
            >
              <span className="text-2xl">⏰</span>
              <span className="text-sm">만료된 리포트</span>
            </Button>

            <Button
              onClick={() => setActiveView("failed")}
              variant={activeView === "failed" ? "default" : "outline"}
              className="h-auto py-4 flex flex-col items-center gap-2"
            >
              <span className="text-2xl">❌</span>
              <span className="text-sm">분석 실패</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 선택된 뷰 렌더링 */}
      {activeView === "sample" && <MockReportView report={sampleReport} />}
      {activeView === "loading" && <ReportSkeleton />}
      {activeView === "expired" && (
        <MockErrorView
          title="리포트가 만료되었습니다"
          message="이 리포트는 만료되었습니다. 새로 분석해주세요."
        />
      )}
      {activeView === "failed" && (
        <MockErrorView
          title="분석에 실패했습니다"
          message="인스타그램 데이터 수집 중 오류가 발생했습니다. 계정이 비공개이거나 존재하지 않는 것으로 보입니다."
        />
      )}

      {!activeView && (
        <div className="text-center py-12 text-gray-400">
          <p>위 버튼을 클릭하여 테스트할 UI를 선택하세요</p>
        </div>
      )}
    </div>
  );
}

/**
 * Mock 리포트 뷰 - 샘플 데이터로 렌더링
 */
function MockReportView({ report }: { report: Report }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">샘플 리포트 미리보기</h2>
        <Badge variant="outline">테스트 모드</Badge>
      </div>

      <ReportHeader
        username={report.username}
        profileImageUrl={report.profile_image_url}
        collectedPostsCount={report.collected_posts_count}
        basicMetrics={report.basic_metrics}
      />

      <SummarySection summary={report.summary} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ContentTendencySection data={report.content_tendency} />
        <LifestyleSection data={report.lifestyle} />
        <PersonalitySection data={report.personality} />
        <NetworkSection data={report.network} />
      </div>

      <GrowthPotentialSection data={report.growth_potential} />

      <ShareActions reportId={report.id} username={report.username} />

      <div className="text-center text-xs text-gray-400 pt-4">
        <p>
          생성: {new Date(report.created_at).toLocaleString("ko-KR")}| 만료:{" "}
          {new Date(report.expires_at).toLocaleString("ko-KR")}
        </p>
      </div>
    </div>
  );
}

/**
 * Mock 에러 뷰
 */
function MockErrorView({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-red-500" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
      <p className="text-gray-600 text-center max-w-md mb-6">{message}</p>
      <div className="flex gap-3">
        <Button variant="outline">
          <ArrowLeft className="mr-2 h-4 w-4" />
          홈으로 돌아가기
        </Button>
        <Button>
          <RefreshCw className="mr-2 h-4 w-4" />
          다시 시도
        </Button>
      </div>
    </div>
  );
}
