import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * 리포트 로딩 스켈레톤
 * 리포트 로딩 중 표시되는 플레이스홀더 UI
 */
export function ReportSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* 프로필 헤더 스켈레톤 */}
      <Card className="border-0 shadow-lg overflow-hidden">
        <Skeleton className="h-32 w-full" />
        <CardContent className="relative pt-0">
          <div className="-mt-16 mb-4 flex justify-center">
            <Skeleton className="w-32 h-32 rounded-full" />
          </div>
          <div className="text-center space-y-2">
            <Skeleton className="h-8 w-32 mx-auto" />
            <Skeleton className="h-4 w-48 mx-auto" />
          </div>
        </CardContent>
      </Card>

      {/* 카드 그리드 스켈레톤 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-3/4" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 버튼 스켈레톤 */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
        <Skeleton className="h-12 w-full sm:w-40" />
        <Skeleton className="h-12 w-full sm:w-40" />
      </div>
    </div>
  );
}
