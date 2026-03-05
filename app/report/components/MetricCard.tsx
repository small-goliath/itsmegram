import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
}

/**
 * 개별 지표 카드 컴포넌트
 * 리포트의 각종 수치를 카드 형태로 표시
 */
export function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  trend = "neutral",
}: MetricCardProps) {
  const trendColors = {
    up: "text-green-500",
    down: "text-red-500",
    neutral: "text-gray-500",
  };

  return (
    <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
        <div className="p-2 bg-gradient-to-br from-pink-100 to-purple-100 rounded-lg">
          <Icon className="w-4 h-4 text-pink-600" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        {description && (
          <p className={`text-xs mt-1 ${trendColors[trend]}`}>{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
