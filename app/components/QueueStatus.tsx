"use client";

import { useEffect, useState, useCallback } from "react";

interface QueueStatusProps {
  jobId: string;
  onComplete: (reportId: string) => void;
  onError?: (error: string) => void;
}

interface QueueStatusData {
  status: "pending" | "processing" | "completed" | "failed";
  queue_position?: number;
  estimated_wait_seconds?: number;
  result?: { report_id: string };
  error?: string;
}

export function QueueStatus({ jobId, onComplete, onError }: QueueStatusProps) {
  const [status, setStatus] = useState<QueueStatusData | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/queue/${jobId}/status`);

      if (!response.ok) {
        if (response.status === 404) {
          setError("작업을 찾을 수 없습니다.");
          onError?.("Job not found");
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: QueueStatusData = await response.json();
      setStatus(data);

      // Update progress based on status
      if (data.status === "pending") {
        setProgress(10);
      } else if (data.status === "processing") {
        setProgress(50);
      } else if (data.status === "completed") {
        setProgress(100);
      }

      if (data.status === "completed" && data.result?.report_id) {
        onComplete(data.result.report_id);
      } else if (data.status === "failed") {
        const errorMsg = data.error || "분석 중 오류가 발생했습니다.";
        setError(errorMsg);
        onError?.(errorMsg);
      }
    } catch (err) {
      console.error("Failed to fetch queue status:", err);
      setError("상태 조회 중 오류가 발생했습니다.");
    }
  }, [jobId, onComplete, onError]);

  useEffect(() => {
    // Initial fetch
    pollStatus();

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [pollStatus]);

  const getStatusMessage = () => {
    if (!status) {
      return "상태를 불러오는 중...";
    }

    switch (status.status) {
      case "pending":
        return `대기열에서 대기 중... ${status.queue_position ? `(${status.queue_position}번째)` : ""}`;
      case "processing":
        return "데이터 수집 및 분석 중... (최대 1분 소요)";
      case "completed":
        return "분석 완료! 리포트를 불러오는 중...";
      case "failed":
        return `오류 발생: ${status.error || "알 수 없는 오류"}`;
      default:
        return "처리 중...";
    }
  };

  const getStatusColor = () => {
    if (!status) return "bg-gray-500";

    switch (status.status) {
      case "pending":
        return "bg-yellow-500";
      case "processing":
        return "bg-blue-500";
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const formatWaitTime = (seconds?: number) => {
    if (!seconds) return null;

    const minutes = Math.ceil(seconds / 60);
    if (minutes < 1) {
      return "1분 이내";
    }
    return `약 ${minutes}분`;
  };

  if (error) {
    return (
      <div className="w-full max-w-md mx-auto p-6 bg-red-50 rounded-lg shadow-lg">
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
            <svg
              className="w-6 h-6 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
        </div>
        <p className="text-center text-red-700 font-medium">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-4">
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getStatusColor()} transition-all duration-500 ease-out`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-center mb-3">
        {status?.status === "pending" && (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-500 mr-2" />
        )}
        {status?.status === "processing" && (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mr-2" />
        )}
        {status?.status === "completed" && (
          <svg
            className="w-5 h-5 text-green-500 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
        <p className="text-center text-gray-700 font-medium">
          {getStatusMessage()}
        </p>
      </div>

      {status?.estimated_wait_seconds && status.status === "pending" && (
        <p className="text-center text-sm text-gray-500 mt-2">
          예상 대기 시간: {formatWaitTime(status.estimated_wait_seconds)}
        </p>
      )}

      {status?.queue_position && status.status === "pending" && (
        <p className="text-center text-xs text-gray-400 mt-1">
          현재 {status.queue_position}명의 사용자가 대기 중입니다
        </p>
      )}

      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-400 text-center">
          작업 ID: <span className="font-mono">{jobId}</span>
        </p>
      </div>
    </div>
  );
}
