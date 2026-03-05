import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { User, MessageCircle, Zap } from "lucide-react";
import { Personality } from "../types";

interface PersonalitySectionProps {
  data: Personality;
}

/**
 * 성격 분석 섹션 컴포넌트
 * 외향성, 표현력, 커뮤니케이션 스타일 표시
 */
export function PersonalitySection({ data }: PersonalitySectionProps) {
  // 표현력에 따른 레이블과 색상
  const getExpressionLabel = (strength: number) => {
    if (strength >= 80) return { label: "매우 높음", color: "bg-green-500" };
    if (strength >= 60) return { label: "높음", color: "bg-blue-500" };
    if (strength >= 40) return { label: "보통", color: "bg-yellow-500" };
    return { label: "낮음", color: "bg-gray-400" };
  };

  const expressionInfo = getExpressionLabel(data.expression_strength);

  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg">
            <User className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">성격 분석</CardTitle>
            <p className="text-sm text-gray-500">계정 운영자의 성격 특징</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 외향성 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <User className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">외향성</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.extroversion}
          </p>
        </div>

        <Separator />

        {/* 표현력 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">표현력</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {expressionInfo.label}
            </Badge>
          </div>
          <div className="space-y-2">
            <Progress value={data.expression_strength} className="h-2" />
            <div className="flex justify-between text-xs text-gray-400">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>
          <p className="text-gray-500 text-xs mt-2">
            콘텐츠에서 드러나는 표현의 강도와 개성의 정도
          </p>
        </div>

        {/* 커뮤니케이션 스타일 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <MessageCircle className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">커뮤니케이션 스타일</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.communication}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
