"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Loader2, AlertCircle, ArrowLeft, RefreshCw } from "lucide-react";
import { ReportView } from "./ReportView";
import { requestAnalysis, checkAnalysisStatus } from "../lib/api";
import { AnalysisResponse, AnalysisStatus } from "../types";

interface ReportContentProps {
  username: string | undefined;
}

/**
 * 리포트 콘텐츠 컴포넌트
 * username이 없으면 에러 표시, 있으면 분석 진행
 * 분석 완료 후 ReportView로 전환
 */
export function ReportContent({ username }: ReportContentProps) {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [progress, setProgress] = useState(0);
  const [reportId, setReportId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState("데이터 수집 중...");

  // 분석 요청 및 폴리
  const startAnalysis = useCallback(async () => {
    if (!username) return;

    try {
      setIsAnalyzing(true);
      setError(null);
      setProgress(10);
      setStatusMessage("인스타그램 데이터 수집 중...");

      // 분석 요청
      const response: AnalysisResponse = await requestAnalysis(username);
      setReportId(response.report_id);
      setProgress(30);

      // 상태 폴리
      const pollStatus = async () => {
        try {
          const status: AnalysisStatus = await checkAnalysisStatus(
            response.report_id
          );

          setProgress(status.progress);
          setStatusMessage(status.message);

          if (status.status === "completed") {
            setIsAnalyzing(false);
            setProgress(100);
          } else if (status.status === "failed") {
            setError(status.message || "분석에 실패했습니다.");
            setIsAnalyzing(false);
          } else {
            // 계속 처리 중, 2초 후 다시 확인
            setTimeout(pollStatus, 2000);
          }
        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : "상태 확인 중 오류가 발생했습니다."
          );
          setIsAnalyzing(false);
        }
      };

      pollStatus();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "분석 요청에 실패했습니다."
      );
      setIsAnalyzing(false);
    }
  }, [username]);

  useEffect(() => {
    // username이 없으면 홈으로 리다이렉트
    if (!username) {
      router.push("/");
      return;
    }

    // 분석 시작
    startAnalysis();
  }, [username, router, startAnalysis]);

  // username이 없는 경우 (리다이렉트 전 잠시 표시)
  if (!username) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          아이디가 필요합니다
        </h2>
        <p className="text-gray-600 mb-6">인스타그램 아이디를 입력해주세요.</p>
        <Button onClick={() => router.push("/")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          홈으로 돌아가기
        </Button>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          분석 중 오류가 발생했습니다
        </h2>
        <p className="text-gray-600 text-center max-w-md mb-6">{error}</p>
        <div className="flex gap-3">
          <Button onClick={() => router.push("/")} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            홈으로 돌아가기
          </Button>
          <Button onClick={startAnalysis}>
            <RefreshCw className="mr-2 h-4 w-4" />
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  // 분석 중인 경우
  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-8">
          <Loader2 className="w-16 h-16 text-pink-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold text-pink-600">
              {Math.round(progress)}%
            </span>
          </div>
        </div>

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          @{username}님의 계정을 분석중입니다
        </h2>
        <p className="text-gray-600 text-center max-w-md">
          AI가 인스타그램 계정을 심층 분석하고 있습니다.
          <br />
          잠시만 기다려주세요...
        </p>

        {/* 진행 상태 표시 */}
        <div className="w-full max-w-md mt-8 space-y-4">
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-gray-500 text-center">{statusMessage}</p>
          <div className="flex justify-between text-xs text-gray-400">
            <span>데이터 수집</span>
            <span>AI 분석</span>
            <span>리포트 생성</span>
          </div>
        </div>
      </div>
    );
  }

  // 분석 완료 - ReportView로 전환
  if (reportId) {
    return <ReportView reportId={reportId} />;
  }

  // 기본 상태 (fallback)
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      <p className="text-gray-600 mt-4">준비 중...</p>
    </div>
  );
}
