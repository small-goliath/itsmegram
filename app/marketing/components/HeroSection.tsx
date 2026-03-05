"use client";

import { motion } from "framer-motion";
import { ArrowRight, Instagram, Sparkles } from "lucide-react";
import Link from "next/link";

/**
 * Hero 섹션 컴포넌트
 * 풀스크린 그라데이션 배경 + 애니메이션 타이틀
 */
export function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* 배경 그라데이션 */}
      <div className="absolute inset-0 bg-gradient-to-br from-yellow-300 via-pink-500 via-purple-500 to-indigo-600" />

      {/* 애니메이션 배경 요소들 */}
      <div className="absolute inset-0 overflow-hidden">
        {/* 떠다니는 원형 요소들 */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-white/10 rounded-full blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
          animate={{
            x: [0, -40, 0],
            y: [0, 40, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1,
          }}
        />
        <motion.div
          className="absolute top-1/2 right-1/3 w-48 h-48 bg-pink-500/20 rounded-full blur-3xl"
          animate={{
            x: [0, 30, 0],
            y: [0, 50, 0],
          }}
          transition={{
            duration: 7,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2,
          }}
        />
      </div>

      {/* 메인 콘텐츠 */}
      <div className="relative z-10 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* 배지 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-md border border-white/30 mb-8"
        >
          <Sparkles className="w-4 h-4 text-yellow-300" />
          <span className="text-sm font-medium text-white">
            AI 기술로 완성하는 나만의 분석 리포트
          </span>
        </motion.div>

        {/* 로고 아이콘 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mb-6"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 sm:w-24 sm:h-24 rounded-3xl bg-white/20 backdrop-blur-sm border border-white/30 shadow-2xl">
            <Instagram className="w-10 h-10 sm:w-12 sm:h-12 text-white" />
          </div>
        </motion.div>

        {/* 타이틀 */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-white mb-6 tracking-tight"
        >
          <span className="block">itsmegram</span>
        </motion.h1>

        {/* 서브타이틀 */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="text-xl sm:text-2xl md:text-3xl text-white/90 font-medium mb-4"
        >
          AI로 분석하는 나의 인스타그램
        </motion.p>

        {/* 설명 텍스트 */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="text-base sm:text-lg text-white/80 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          인스타그램 계정을 AI가 심층 분석하여
          <br className="hidden sm:block" />
          콘텐츠 성향, 라이프스타일, 성격 특징을 발견하세요
        </motion.p>

        {/* CTA 버튼 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
        >
          <Link
            href="/"
            className="group inline-flex items-center gap-3 px-8 py-4 sm:px-10 sm:py-5 bg-white text-gray-900 rounded-full font-bold text-lg shadow-2xl hover:shadow-white/25 transition-all duration-300 hover:scale-105 min-h-[56px]"
          >
            <span>무료 분석 받아보기</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>

        {/* 신뢰 지표 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.9 }}
          className="mt-12 flex flex-wrap items-center justify-center gap-6 sm:gap-8 text-white/70"
        >
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">10,000+</span>
            <span className="text-sm">분석 완료</span>
          </div>
          <div className="w-px h-8 bg-white/30 hidden sm:block" />
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">4.9</span>
            <span className="text-sm">만족도</span>
          </div>
          <div className="w-px h-8 bg-white/30 hidden sm:block" />
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-white">30초</span>
            <span className="text-sm">분석 시간</span>
          </div>
        </motion.div>
      </div>

      {/* 스크롤 힌트 */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.2 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 rounded-full border-2 border-white/50 flex items-start justify-center p-2"
        >
          <motion.div className="w-1 h-2 bg-white/70 rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  );
}
