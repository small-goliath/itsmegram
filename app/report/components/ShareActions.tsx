"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Download,
  Share2,
  Link2,
  Check,
  Loader2,
  Instagram,
  Smartphone,
  Monitor,
  ChevronRight,
  ImageIcon,
  Upload,
} from "lucide-react";
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
  const [isSharing, setIsSharing] = useState(false);
  const [showGuideDialog, setShowGuideDialog] = useState(false);

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
          throw new Error(
            "리포트가 아직 생성 중입니다. 잠시 후 다시 시도해주세요."
          );
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
      toast.error(
        error instanceof Error ? error.message : "다운로드에 실패했습니다."
      );
    } finally {
      setIsDownloading(false);
    }
  };

  // 공유 이벤트 트래킹
  const trackShare = async (platform: string) => {
    try {
      await fetch(`/api/v1/report/${reportId}/share`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ platform }),
      });
    } catch (error) {
      // 트래킹 실패는 사용자에게 보여주지 않음
      console.error("공유 트래킹 실패:", error);
    }
  };

  // Instagram 딥링크 열기 (모바일)
  const openInstagramStory = () => {
    const instagramUrl = "instagram-stories://share?source_application=itsmegram";
    window.location.href = instagramUrl;

    // 앱이 설치되지 않은 경우를 위한 폰백
    setTimeout(() => {
      toast.info(
        "Instagram 앱이 설치되어 있지 않은 것 같습니다. 수동으로 업로드해주세요!"
      );
      setShowGuideDialog(true);
    }, 2000);
  };

  // Web Share API를 사용한 공유 (파일 포함)
  const handleShareWithFile = async () => {
    setIsSharing(true);
    try {
      // 이미지를 Blob으로 가져오기
      const response = await fetch(`/api/v1/report/${reportId}/image`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("리포트를 찾을 수 없습니다.");
        } else if (response.status === 400) {
          throw new Error(
            "리포트가 아직 생성 중입니다. 잠시 후 다시 시도해주세요."
          );
        } else {
          throw new Error("이미지 생성에 실패했습니다.");
        }
      }

      const blob = await response.blob();
      const file = new File([blob], "itsmegram-report.png", {
        type: "image/png",
      });

      // Web Share API 사용
      if (navigator.share && navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: "My Instagram Analysis",
          text: "itsmegram으로 분석한 나의 인스타그램 리포트!",
        });
        toast.success("공유되었습니다!");
        trackShare("native");
      } else {
        // 폰백: 다운로드 후 안내
        handleDownload();
        setShowGuideDialog(true);
        trackShare("download");
      }
    } catch (error) {
      console.error("공유 실패:", error);
      if (error instanceof Error && error.name !== "AbortError") {
        toast.error(error.message || "공유에 실패했습니다.");
      }
    } finally {
      setIsSharing(false);
    }
  };

  // 기본 공유하기 (Web Share API)
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
        trackShare("native");
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

  // Instagram 스토리 공유
  const handleInstagramShare = async () => {
    setIsSharing(true);
    try {
      // 먼저 이미지 다운로드
      const response = await fetch(`/api/v1/report/${reportId}/image`);

      if (!response.ok) {
        throw new Error("이미지를 가져올 수 없습니다.");
      }

      const blob = await response.blob();
      const file = new File([blob], "itsmegram-report.png", {
        type: "image/png",
      });

      // 모바일 기기 확인
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

      if (isMobile && navigator.share && navigator.canShare({ files: [file] })) {
        // 모바일에서 Web Share API로 파일 공유
        try {
          await navigator.share({
            files: [file],
            title: "Instagram Story Share",
            text: "itsmegram 리포트를 Instagram 스토리에 공유하세요!",
          });
          toast.success("공유되었습니다! Instagram에서 스토리를 완성해주세요.");
          trackShare("instagram_mobile");
        } catch (err) {
          if (err instanceof Error && err.name !== "AbortError") {
            // 공유 실패 시 가이드 모달 표시
            await handleDownload();
            setShowGuideDialog(true);
            trackShare("instagram_fallback");
          }
        }
      } else {
        // 데스크톱 또는 Web Share API 미지원: 다운로드 후 가이드
        await handleDownload();
        setShowGuideDialog(true);
        trackShare("instagram_desktop");
      }
    } catch (error) {
      console.error("Instagram 공유 실패:", error);
      toast.error("공유에 실패했습니다.");
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* 메인 액션 버튼들 */}
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

        {/* Instagram 스토리 공유 버튼 */}
        <Button
          onClick={handleInstagramShare}
          disabled={isSharing}
          className="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 text-white hover:opacity-90 transition-opacity disabled:opacity-50"
          size="lg"
        >
          {isSharing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              공유 중...
            </>
          ) : (
            <>
              <Instagram className="mr-2 h-4 w-4" />
              스토리 공유
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

      {/* 공유 가이드 모달 */}
      <Dialog open={showGuideDialog} onOpenChange={setShowGuideDialog}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Instagram className="h-5 w-5 text-pink-500" />
              Instagram 스토리 공유 가이드
            </DialogTitle>
            <DialogDescription>
              리포트 이미지를 Instagram 스토리에 공유하는 방법을 안내해드립니다.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* 모바일 가이드 */}
            <div className="space-y-3">
              <h3 className="font-semibold flex items-center gap-2 text-sm">
                <Smartphone className="h-4 w-4 text-blue-500" />
                모바일에서 공유하기
              </h3>
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center text-xs font-medium">
                    1
                  </span>
                  <span>Instagram 앱을 열고 홈 화면에서 스토리 추가 (+) 버튼을 탭하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center text-xs font-medium">
                    2
                  </span>
                  <span>왼쪽 하단의 갤러리 아이콘을 탭하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center text-xs font-medium">
                    3
                  </span>
                  <span>방금 저장한 itsmegram 리포트 이미지를 선택하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center text-xs font-medium">
                    4
                  </span>
                  <span>스티커, 텍스트, 해시태그를 추가하고 공유하세요!</span>
                </li>
              </ol>
            </div>

            {/* 데스크톱 가이드 */}
            <div className="space-y-3">
              <h3 className="font-semibold flex items-center gap-2 text-sm">
                <Monitor className="h-4 w-4 text-green-500" />
                데스크톱에서 공유하기
              </h3>
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-medium">
                    1
                  </span>
                  <span>Instagram 웹사이트(instagram.com)에 접속하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-medium">
                    2
                  </span>
                  <span>왼쪽 사이드바에서 &quot;스토리 만들기&quot;를 클릭하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-medium">
                    3
                  </span>
                  <span>다운로드한 리포트 이미지를 드래그앤드롭 또는 선택하세요.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-medium">
                    4
                  </span>
                  <span>편집 후 &quot;스토리 공유&quot;를 클릭하세요!</span>
                </li>
              </ol>
            </div>

            {/* 팁 섹션 */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 space-y-2">
              <h4 className="font-medium text-sm text-yellow-800 flex items-center gap-2">
                <ImageIcon className="h-4 w-4" />
                공유 팁
              </h4>
              <ul className="text-xs text-yellow-700 space-y-1">
                <li className="flex items-start gap-1">
                  <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  <span>@itsmegram을 태그하면 저희 팀이 확인할 수 있어요!</span>
                </li>
                <li className="flex items-start gap-1">
                  <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  <span>#itsmegram #인스타분석 해시태그를 추가해보세요.</span>
                </li>
                <li className="flex items-start gap-1">
                  <ChevronRight className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  <span>스티커나 투표를 추가하면 더 많은 참여를 얻을 수 있어요.</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Button
              onClick={() => {
                setShowGuideDialog(false);
                openInstagramStory();
              }}
              className="w-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 text-white"
            >
              <Upload className="mr-2 h-4 w-4" />
              Instagram 앱 열기
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowGuideDialog(false)}
              className="w-full"
            >
              닫기
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
