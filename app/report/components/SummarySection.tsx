import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Quote } from "lucide-react";

interface SummarySectionProps {
  summary: string;
}

/**
 * 핵심 요약 섹션 컴포넌트
 * AI가 생성한 종합 요약을 강조하여 표시
 */
export function SummarySection({ summary }: SummarySectionProps) {
  return (
    <Card className="border-0 shadow-md bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-pink-500 to-purple-600 rounded-lg">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">AI 종합 분석</CardTitle>
            <p className="text-sm text-gray-500">인스타그램 계정의 핵심 특징</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative bg-white/70 backdrop-blur-sm rounded-xl p-6">
          <Quote className="absolute top-4 left-4 w-8 h-8 text-pink-200" />
          <p className="text-gray-700 leading-relaxed pl-8">
            {summary}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
