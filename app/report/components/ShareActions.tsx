"use client";

import { Button } from "@/components/ui/button";
import { Download, Share2, Link2, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface ShareActionsProps {
  reportId: string;
  username: string;
}

/**
 * 공유/다운로드 액션 컴포넌트
 * 리포트 공유, 다운로드, 링크 복사 기능 제공
 */
export function ShareActions({ reportId, username }: ShareActionsProps) {
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // 링크 복사
  const handleCopyLink = async () => {
    const url = `${window.location.origin}/report/${reportId}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success("링크가 복사되었습니다!");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("링크 복사 실패:", err);
      toast.error("링크 복사에 실패했습니다.");
    }
  };

  // 이미지 다운로드
  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(
        `/api/v1/report/${reportId}/download?format=png`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("리포트를 찾을 수 없습니다.");
        } else if (response.status === 400) {
          throw new Error("리포트가 아직 생성 중입니다. 잠시 후 다시 시도해주세요.");
        } else {
          throw new Error("이미지 생성에 실패했습니다.");
        }
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);

      // Content-Disposition 헤더에서 파일명 추출
      const contentDisposition = response.headers.get("content-disposition");
      let filename = `itsmegram_${username}_report.png`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);

      toast.success("이미지가 저장되었습니다!");
    } catch (error) {
      console.error("다운로드 실패:", error);
      toast.error(error instanceof Error ? error.message : "다운로드에 실패했습니다.");
    } finally {
      setIsDownloading(false);
    }
  };

  // 공유하기 (Web Share API)
  const handleShare = async () => {
    const shareData = {
      title: `@${username}님의 인스타그램 분석 리포트`,
      text: `itsmegram에서 @${username}님의 인스타그램 계정을 분석했어요!`,
      url: `${window.location.origin}/report/${reportId}`,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
        toast.success("공유되었습니다!");
      } catch (err) {
        // 사용자가 취소한 경우
        if (err instanceof Error && err.name !== "AbortError") {
          console.error("공유 실패:", err);
          toast.error("공유에 실패했습니다.");
        }
      }
    } else {
      // Web Share API 미지원 시 링크 복사
      handleCopyLink();
    }
  };

  return (
    <div className="flex flex-col sm:flex-row gap-3 justify-center pt-6">
      {/* 이미지로 저장 버튼 */}
      <Button
        onClick={handleDownload}
        disabled={isDownloading}
        className="bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
        size="lg"
      >
        {isDownloading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            저장 중...
          </>
        ) : (
          <>
            <Download className="mr-2 h-4 w-4" />
            이미지로 저장
          </>
        )}
      </Button>

      {/* 공유하기 버튼 */}
      <Button
        onClick={handleShare}
        variant="outline"
        size="lg"
        className="border-gray-300"
      >
        <Share2 className="mr-2 h-4 w-4" />
        공유하기
      </Button>

      {/* 링크 복사 버튼 */}
      <Button
        onClick={handleCopyLink}
        variant="outline"
        size="lg"
        className="border-gray-300"
      >
        {copied ? (
          <>
            <Check className="mr-2 h-4 w-4 text-green-500" />
            복사됨
          </>
        ) : (
          <>
            <Link2 className="mr-2 h-4 w-4" />
            링크 복사
          </>
        )}
      </Button>
    </div>
  );
}
