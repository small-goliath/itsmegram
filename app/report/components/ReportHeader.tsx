import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Heart, MessageCircle, Image as ImageIcon, TrendingUp, Users } from "lucide-react";
import Image from "next/image";
import { BasicMetrics } from "../types";

interface ReportHeaderProps {
  username: string;
  profileImageUrl?: string;
  collectedPostsCount: number;
  basicMetrics: BasicMetrics;
}

/**
 * 리포트 헤더 컴포넌트
 * 프로필 정보와 핵심 지표를 표시
 * Instagram 그라데이션 배경 적용
 */
export function ReportHeader({
  username,
  profileImageUrl,
  collectedPostsCount,
  basicMetrics,
}: ReportHeaderProps) {
  // 기본값 설정
  const metrics = basicMetrics || {
    engagement_rate: 0,
    avg_likes: 0,
    avg_comments: 0,
    followers: 0,
    following: 0,
    posts: 0,
  };

  // 참여율에 따른 배지 색상 결정
  const getEngagementBadge = (rate: number) => {
    if (rate >= 5) return { label: "높음", variant: "default" as const };
    if (rate >= 3) return { label: "보통", variant: "secondary" as const };
    return { label: "낮음", variant: "outline" as const };
  };

  const engagementBadge = getEngagementBadge(metrics.engagement_rate);

  return (
    <Card className="border-0 shadow-lg overflow-hidden">
      {/* Instagram 그라데이션 배경 */}
      <div className="h-40 bg-gradient-to-r from-yellow-400 via-pink-500 via-purple-600 to-blue-500 relative">
        <div className="absolute inset-0 bg-black/10" />
        {/* 장식용 원형 패턴 */}
        <div className="absolute top-4 right-4 w-24 h-24 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute bottom-4 left-4 w-16 h-16 rounded-full bg-white/10 blur-xl" />
      </div>

      <CardContent className="relative pt-0 pb-8">
        {/* 프로필 이미지 */}
        <div className="-mt-16 mb-4 flex justify-center">
          <div className="relative">
            {/* Instagram 스타일 그라데이션 테두리 */}
            <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 p-1">
              <div className="w-full h-full rounded-full bg-white p-1">
                {profileImageUrl ? (
                  <Image
                    src={profileImageUrl}
                    alt={`@${username} 프로필`}
                    width={120}
                    height={120}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                    <Users className="w-12 h-12 text-gray-400" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 사용자 정보 */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">@{username}</h1>
          <p className="text-gray-500 mt-1">AI 분석 리포트</p>
          <Badge variant="outline" className="mt-2">
            {collectedPostsCount}개 게시물 분석
          </Badge>
        </div>

        {/* 핵심 지표 그리드 */}
        <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
          {/* 평균 좋아요 */}
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Heart className="w-4 h-4 text-pink-500" />
              <span className="text-xs text-gray-500">평균 좋아요</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {Math.round(metrics.avg_likes).toLocaleString()}
            </div>
          </div>

          {/* 참여율 */}
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center justify-center gap-1 mb-1">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-gray-500">참여율</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {metrics.engagement_rate.toFixed(1)}%
            </div>
            <Badge
              variant={engagementBadge.variant}
              className="text-[10px] mt-1"
            >
              {engagementBadge.label}
            </Badge>
          </div>

          {/* 게시물 수 */}
          <div className="text-center p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center justify-center gap-1 mb-1">
              <ImageIcon className="w-4 h-4 text-green-500" />
              <span className="text-xs text-gray-500">분석 게시물</span>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {collectedPostsCount}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
