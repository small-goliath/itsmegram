"use client";

import { motion } from "framer-motion";
import { UserSearch, Brain, FileCheck, ArrowRight } from "lucide-react";

/**
 * 사용 방법 단계 데이터
 */
const steps = [
  {
    number: "01",
    icon: UserSearch,
    title: "아이디 입력",
    description:
      "분석하고 싶은 인스타그램 계정의 사용자 이름을 입력하세요. 공개 계정만 분석 가능합니다.",
    color: "from-yellow-400 to-orange-500",
  },
  {
    number: "02",
    icon: Brain,
    title: "AI 분석",
    description:
      "AI가 게시물, 해시태그, 참여율 등 다양한 데이터를 분석하여 나만의 특징을 파악합니다.",
    color: "from-pink-500 to-purple-600",
  },
  {
    number: "03",
    icon: FileCheck,
    title: "리포트 확인",
    description:
      "완성된 분석 리포트를 확인하고 인스타그램 스토리로 공유하거나 저장하세요.",
    color: "from-purple-600 to-indigo-600",
  },
];

/**
 * 사용 방법 섹션 컴포넌트
 * 3단계 프로세스 시각화 (Stepper)
 */
export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20 sm:py-28 lg:py-32 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-6xl mx-auto">
        {/* 섹션 헤더 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16 sm:mb-20"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-600 text-sm font-medium mb-4">
            How It Works
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            간단한 3단계로 완성
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            복잡한 과정 없이 30초면 충분합니다
            <br className="hidden sm:block" />
            지금 바로 나의 인스타그램을 분석핳세요
          </p>
        </motion.div>

        {/* 스텝 카드들 */}
        <div className="relative">
          {/* 연결선 - 데스크톱에서만 표시 */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 -translate-y-1/2">
            <div className="max-w-4xl mx-auto px-20">
              <div className="flex items-center justify-between">
                {steps.slice(0, -1).map((_, idx) => (
                  <div key={idx} className="flex-1 flex items-center">
                    <div className="h-0.5 flex-1 bg-gradient-to-r from-gray-200 to-gray-300" />
                    <ArrowRight className="w-5 h-5 text-gray-300 mx-2" />
                    <div className="h-0.5 flex-1 bg-gradient-to-r from-gray-300 to-gray-200" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 스텝 카드 그리드 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
                className="relative"
              >
                <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-lg border border-gray-100 h-full hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                  {/* 스텝 넘버 */}
                  <div
                    className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} text-white font-bold text-lg mb-6 shadow-lg`}
                  >
                    {step.number}
                  </div>

                  {/* 아이콘 */}
                  <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <step.icon className="w-8 h-8 text-gray-700" />
                  </div>

                  {/* 제목 */}
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    {step.title}
                  </h3>

                  {/* 설명 */}
                  <p className="text-gray-600 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {/* 모바일 화살표 */}
                {index < steps.length - 1 && (
                  <div className="flex justify-center my-6 md:hidden">
                    <ArrowRight className="w-6 h-6 text-gray-300 rotate-90" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* 타임라인 인디케이터 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-16 flex justify-center"
        >
          <div className="inline-flex items-center gap-4 px-6 py-3 bg-white rounded-full shadow-md border border-gray-100">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-gray-600">30초 분석</span>
            </div>
            <div className="w-px h-4 bg-gray-200" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-sm text-gray-600">AI 기반</span>
            </div>
            <div className="w-px h-4 bg-gray-200" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="text-sm text-gray-600">즉시 공유</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
