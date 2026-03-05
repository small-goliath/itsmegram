import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { TrendingUp, Target, Lightbulb, CheckCircle } from "lucide-react";
import { GrowthPotential } from "../types";

interface GrowthPotentialSectionProps {
  data: GrowthPotential;
}

/**
 * 성장 잠재력 섹션 컴포넌트
 * 추세, 일관성, 개선 제안 표시
 */
export function GrowthPotentialSection({ data }: GrowthPotentialSectionProps) {
  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">성장 잠재력</CardTitle>
            <p className="text-sm text-gray-500">계정의 성장 가능성 분석</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 성장 추세 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">성장 추세</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.trend}
          </p>
        </div>

        <Separator />

        {/* 일관성 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">활동 일관성</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.consistency}
          </p>
        </div>

        <Separator />

        {/* 개선 제안 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">성장을 위한 제안</span>
          </div>
          <div className="space-y-2">
            {data.suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="flex items-start gap-2 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg"
              >
                <CheckCircle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-gray-700">{suggestion}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
