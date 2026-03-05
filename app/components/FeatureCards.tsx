import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, FileText, Share2, Shield } from "lucide-react";

/**
 * 기능 소개 카드 데이터
 */
const features = [
  {
    icon: Sparkles,
    title: "AI 분석",
    description: "최신 AI 기술로 인스타그램 계정을 심층 분석하여 콘텐츠 성향과 라이프스타일을 파악합니다.",
  },
  {
    icon: FileText,
    title: "리포트 생성",
    description: "상세한 분석 리포트를 즉시 생성하여 나만의 인스타그램 특징을 한눈에 확인하세요.",
  },
  {
    icon: Share2,
    title: "스토리 공유",
    description: "분석 결과를 멋진 이미지로 만들어 인스타그램 스토리에 바로 공유할 수 있습니다.",
  },
  {
    icon: Shield,
    title: "개인정보 보호",
    description: "분석 데이터는 24시간 후 자동으로 삭제되어 안전하게 이용할 수 있습니다.",
  },
];

/**
 * 기능 소개 카드 그리드 컴포넌트
 * 4개의 주요 기능을 카드 형태로 소개
 */
export function FeatureCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
      {features.map((feature, index) => (
        <Card
          key={index}
          className="group bg-white/95 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
        >
          <CardContent className="p-6 sm:p-8">
            {/* 아이콘 */}
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <feature.icon className="w-6 h-6 text-white" />
            </div>

            {/* 제목 */}
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              {feature.title}
            </h3>

            {/* 설명 */}
            <p className="text-sm text-gray-600 leading-relaxed">
              {feature.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
