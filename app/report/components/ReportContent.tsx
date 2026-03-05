"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, ArrowLeft, User } from "lucide-react";

interface ReportContentProps {
  username: string | undefined;
}

/**
 * 리포트 콘텐츠 컴포넌트
 * username이 없으면 에러 표시, 있으면 분석 진행
 */
export function ReportContent({ username }: ReportContentProps) {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // username이 없으면 홈으로 리다이렉트
    if (!username) {
      router.push("/");
      return;
    }

    // 분석 진행 시뮬레이션 (실제로는 API 호출)
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsAnalyzing(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [username, router]);

  // username이 없는 경우 (리다이렉트 전 잠시 표시)
  if (!username) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
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

  // 분석 중인 경우
  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative mb-8">
          <Loader2 className="w-16 h-16 text-pink-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold text-pink-600">
              {progress}%
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
        <div className="w-full max-w-md mt-8">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>데이터 수집</span>
            <span>AI 분석</span>
            <span>리포트 생성</span>
          </div>
        </div>
      </div>
    );
  }

  // 분석 완료 - 샘플 리포트 표시
  return (
    <div className="space-y-6">
      {/* 뒤로 가기 버튼 */}
      <Button
        variant="ghost"
        onClick={() => router.push("/")}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        홈으로 돌아가기
      </Button>

      {/* 프로필 헤더 */}
      <Card className="border-0 shadow-lg overflow-hidden">
        <div className="h-32 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600" />
        <CardContent className="relative pt-0">
          <div className="-mt-16 mb-4 flex justify-center">
            <div className="w-32 h-32 rounded-full bg-white p-1 shadow-lg">
              <div className="w-full h-full rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                <User className="w-12 h-12 text-gray-400" />
              </div>
            </div>
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900">@{username}</h1>
            <p className="text-gray-500 mt-1">
              AI 분석이 완료되었습니다
            </p>
          </div>
        </CardContent>
      </Card>

      {/* 샘플 리포트 내용 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">콘텐츠 성향</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              일상과 여행 콘텐츠를 주로 공유하는 계정입니다.
              비주얼 중심의 미적인 포스트가 특징입니다.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">활동 패턴</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              주 3-4회 꾸준히 포스팅하며, 주로 저녁 시간대에
              활동하는 패턴을 보입니다.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">성격 분석</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              창의적이고 개방적인 성격으로 보입니다.
              새로운 경험을 즐기고 공유하는 것을 좋아합니다.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">성장 가능성</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">
              꾸준한 활동과 양질의 콘텐츠로
              지속적인 성장이 기대되는 계정입니다.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 액션 버튼 */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
        <Button
          className="bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 text-white hover:opacity-90"
          size="lg"
        >
          이미지로 저장
        </Button>
        <Button variant="outline" size="lg">
          스토리로 공유
        </Button>
      </div>
    </div>
  );
}
