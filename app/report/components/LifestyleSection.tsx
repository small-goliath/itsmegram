import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Heart, Clock, ShoppingBag, Coffee, Music, BookOpen, Camera, Plane } from "lucide-react";
import { Lifestyle } from "../types";

interface LifestyleSectionProps {
  data: Lifestyle;
}

// 관심사별 아이콘 매핑
const interestIcons: Record<string, React.ReactNode> = {
  "여행": <Plane className="w-4 h-4" />,
  "사진": <Camera className="w-4 h-4" />,
  "음식": <Coffee className="w-4 h-4" />,
  "음악": <Music className="w-4 h-4" />,
  "독서": <BookOpen className="w-4 h-4" />,
  "쇼핑": <ShoppingBag className="w-4 h-4" />,
  "울동": <Heart className="w-4 h-4" />,
};

/**
 * 라이프스타일 섹션 컴포넌트
 * 관심사, 활동 패턴, 소비 패턴 표시
 */
export function LifestyleSection({ data }: LifestyleSectionProps) {
  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-green-400 to-teal-500 rounded-lg">
            <Heart className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">라이프스타일</CardTitle>
            <p className="text-sm text-gray-500">관심사와 활동 패턴 분석</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 관심사 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Heart className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">주요 관심사</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.interests.map((interest, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-gradient-to-r from-green-100 to-teal-100 text-green-700 hover:from-green-200 hover:to-teal-200 flex items-center gap-1"
              >
                {interestIcons[interest] || <Heart className="w-3 h-3" />}
                {interest}
              </Badge>
            ))}
          </div>
        </div>

        <Separator />

        {/* 활동 패턴 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">활동 패턴</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.activity_pattern}
          </p>
        </div>

        {/* 소비 패턴 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ShoppingBag className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">소비 패턴</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.consumption.map((item, index) => (
              <Badge
                key={index}
                variant="outline"
                className="text-gray-600 border-gray-300"
              >
                {item}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
