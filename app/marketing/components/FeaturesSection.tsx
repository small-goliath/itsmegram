"use client";

import { motion } from "framer-motion";
import {
  Brain,
  FileText,
  Share2,
  Shield,
  Zap,
  BarChart3,
} from "lucide-react";

/**
 * 기능 소개 데이터
 */
const features = [
  {
    icon: Brain,
    title: "AI 심층 분석",
    description:
      "최신 AI 기술로 인스타그램 계정을 심층 분석하여 콘텐츠 성향과 라이프스타일을 정확하게 파악합니다.",
    color: "from-pink-500 to-rose-500",
  },
  {
    icon: FileText,
    title: "상세 리포트",
    description:
      "콘텐츠 스타일, 성격 특징, 라이프스타일까지 한눈에 볼 수 있는 멋진 리포트를 생성합니다.",
    color: "from-purple-500 to-indigo-500",
  },
  {
    icon: Share2,
    title: "스토리 공유",
    description:
      "분석 결과를 인스타그램 스토리에 바로 공유할 수 있는 최적화된 이미지를 제공합니다.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Zap,
    title: "30초 완성",
    description:
      "복잡한 과정 없이 30초 만에 AI 분석이 완료됩니다. 빠르고 간편하게 결과를 받아보세요.",
    color: "from-yellow-500 to-orange-500",
  },
  {
    icon: BarChart3,
    title: "데이터 기반 인사이트",
    description:
      "게시물 패턴, 해시태그 분석, 참여율 등 다양한 데이터를 기반으로 한 정확한 인사이트를 제공합니다.",
    color: "from-green-500 to-emerald-500",
  },
  {
    icon: Shield,
    title: "개인정보 보호",
    description:
      "분석 데이터는 24시간 후 자동 삭제됩니다. 안심하고 서비스를 이용할 수 있습니다.",
    color: "from-red-500 to-pink-500",
  },
];

/**
 * 기능 소개 섹션 컴포넌트
 * 3열 그리드 카드 레이아웃 + 호버 애니메이션
 */
export function FeaturesSection() {
  return (
    <section id="features" className="py-20 sm:py-28 lg:py-32 px-4 sm:px-6 lg:px-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        {/* 섹션 헤더 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16 sm:mb-20"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-gradient-to-r from-pink-500/10 to-purple-500/10 text-pink-600 text-sm font-medium mb-4">
            Powerful Features
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            itsmegram의 특별한 기능
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI 기술을 활용한 다양한 기능으로
            <br className="hidden sm:block" />
            나의 인스타그램을 새롭게 발견하세요
          </p>
        </motion.div>

        {/* 기능 카드 그리드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="group h-full bg-white rounded-2xl p-6 sm:p-8 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                {/* 아이콘 */}
                <div
                  className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-5 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg`}
                >
                  <feature.icon className="w-7 h-7 text-white" />
                </div>

                {/* 제목 */}
                <h3 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-pink-600 transition-colors">
                  {feature.title}
                </h3>

                {/* 설명 */}
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
