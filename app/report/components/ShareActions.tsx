"use client";

import { Button } from "@/components/ui/button";
import { Download, Share2, Link2, Check } from "lucide-react";
import { useState } from "react";

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

  // 링크 복사
  const handleCopyLink = async () => {
    const url = `${window.location.origin}/report/${reportId}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("링크 복사 실패:", err);
    }
  };

  // 이미지로 저장 (실제 구현은 html2canvas 등 필요)
  const handleSaveAsImage = () => {
    // TODO: html2canvas 등을 사용하여 이미지로 저장
    alert("이미지 저장 기능은 준비 중입니다");
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
      } catch (err) {
        console.error("공유 실패:", err);
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
        onClick={handleSaveAsImage}
        className="bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 text-white hover:opacity-90 transition-opacity"
        size="lg"
      >
        <Download className="mr-2 h-4 w-4" />
        이미지로 저장
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
