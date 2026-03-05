/**
 * 리포트 API 클라이언트
 * 백엔드 API와 통신하는 함수들
 */

import { AnalysisResponse, AnalysisStatus, Report, ApiError } from "../types";

// API 기본 URL - 클라이언트/서버 모두에서 작동하도록 상대 경로 사용
const API_BASE_URL = "/api/v1";

/**
 * 분석 요청 API
 * @param username 인스타그램 사용자명
 * @returns 분석 응답 (report_id 포함)
 */
export async function requestAnalysis(username: string): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || "분석 요청에 실패했습니다");
  }

  return response.json();
}

/**
 * 분석 상태 확인 API (폴리)
 * @param report_id 리포트 ID
 * @returns 분석 상태
 */
export async function checkAnalysisStatus(report_id: string): Promise<AnalysisStatus> {
  const response = await fetch(`${API_BASE_URL}/analyze/status/${report_id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || "상태 확인에 실패했습니다");
  }

  return response.json();
}

/**
 * 리포트 조회 API
 * @param report_id 리포트 ID
 * @returns 리포트 데이터
 */
export async function getReport(report_id: string): Promise<Report> {
  const response = await fetch(`${API_BASE_URL}/report/${report_id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || "리포트 조회에 실패했습니다");
  }

  return response.json();
}

/**
 * 리포트가 만료되었는지 확인
 * @param expires_at 만료 시간 (ISO 문자열)
 * @returns 만료 여부
 */
export function isReportExpired(expires_at: string): boolean {
  return new Date() > new Date(expires_at);
}
