import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * 리포트 로딩 스켈레톤
 * 리포트 로딩 중 표시되는 플레이스홀더 UI
 * shimmer 효과 적용
 */
export function ReportSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* 프로필 헤더 스켈레톤 */}
      <Card className="border-0 shadow-lg overflow-hidden">
        {/* 그라데이션 배경 스켈레톤 */}
        <Skeleton className="h-40 w-full" />
        <CardContent className="relative pt-0 pb-8">
          {/* 프로필 이미지 */}
          <div className="-mt-16 mb-4 flex justify-center">
            <Skeleton className="w-32 h-32 rounded-full" />
          </div>
          {/* 사용자명 */}
          <div className="text-center space-y-2 mb-6">
            <Skeleton className="h-8 w-32 mx-auto" />
            <Skeleton className="h-4 w-24 mx-auto" />
          </div>
          {/* 핵심 지표 */}
          <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="text-center p-4 bg-gray-50 rounded-xl">
                <Skeleton className="h-4 w-16 mx-auto mb-2" />
                <Skeleton className="h-6 w-12 mx-auto" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 요약 섹션 스켈레톤 */}
      <Card className="border-0 shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div>
              <Skeleton className="h-6 w-32 mb-1" />
              <Skeleton className="h-4 w-48" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-24 w-full rounded-xl" />
        </CardContent>
      </Card>

      {/* 섹션 그리드 스켈레톤 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="border-0 shadow-md">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Skeleton className="w-10 h-10 rounded-lg" />
                <div>
                  <Skeleton className="h-6 w-24 mb-1" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex flex-wrap gap-2 pt-2">
                {[...Array(3)].map((_, j) => (
                  <Skeleton key={j} className="h-6 w-16 rounded-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 성장 잠재력 섹션 스켈레톤 */}
      <Card className="border-0 shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div>
              <Skeleton className="h-6 w-24 mb-1" />
              <Skeleton className="h-4 w-32" />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <div className="space-y-2 pt-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 버튼 스켈레톤 */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center pt-6">
        <Skeleton className="h-12 w-full sm:w-40" />
        <Skeleton className="h-12 w-full sm:w-40" />
        <Skeleton className="h-12 w-full sm:w-40" />
      </div>
    </div>
  );
}
