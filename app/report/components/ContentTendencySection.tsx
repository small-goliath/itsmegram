import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Palette, Type, Hash, Image as ImageIcon } from "lucide-react";
import { ContentTendency } from "../types";

interface ContentTendencySectionProps {
  data: ContentTendency;
}

/**
 * 콘텐츠 성향 섹션 컴포넌트
 * 카테고리, 시각적 스타일, 텍스트 스타일, 해시태그 패턴 표시
 */
export function ContentTendencySection({ data }: ContentTendencySectionProps) {
  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-orange-400 to-pink-500 rounded-lg">
            <Palette className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">콘텐츠 성향</CardTitle>
            <p className="text-sm text-gray-500">게시물의 주제와 스타일 분석</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 카테고리 태그 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ImageIcon className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">주요 카테고리</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.categories.map((category, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-gradient-to-r from-pink-100 to-purple-100 text-pink-700 hover:from-pink-200 hover:to-purple-200"
              >
                {category}
              </Badge>
            ))}
          </div>
        </div>

        <Separator />

        {/* 시각적 스타일 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Palette className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">시각적 스타일</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.visual_style}
          </p>
        </div>

        {/* 텍스트 스타일 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Type className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">텍스트 스타일</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.text_style}
          </p>
        </div>

        {/* 해시태그 패턴 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Hash className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">해시태그 패턴</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.hashtag_pattern.map((pattern, index) => (
              <Badge
                key={index}
                variant="outline"
                className="text-gray-600 border-gray-300"
              >
                #{pattern}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
