import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Users, Heart, MessageSquare } from "lucide-react";
import { Network } from "../types";

interface NetworkSectionProps {
  data: Network;
}

/**
 * 네트워크 분석 섹션 컴포넌트
 * 참여 품질과 커뮤니티 유형 표시
 */
export function NetworkSection({ data }: NetworkSectionProps) {
  return (
    <Card className="border-0 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-lg">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg text-gray-900">네트워크 분석</CardTitle>
            <p className="text-sm text-gray-500">팔로워와의 상호작용 패턴</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 참여 품질 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Heart className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">참여 품질</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.engagement_quality}
          </p>
        </div>

        <Separator />

        {/* 커뮤니티 유형 */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">커뮤니티 유형</span>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed bg-gray-50 p-3 rounded-lg">
            {data.community_type}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
