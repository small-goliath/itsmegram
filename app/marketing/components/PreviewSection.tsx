"use client";

import { motion } from "framer-motion";
import useEmblaCarousel from "embla-carousel-react";
import Autoplay from "embla-carousel-autoplay";
import {
  BarChart3,
  Heart,
  MessageCircle,
  TrendingUp,
  Users,
  Camera,
} from "lucide-react";

/**
 * 샘플 리포트 데이터
 */
const sampleReports = [
  {
    id: 1,
    username: "traveler_k",
    title: "여행 크리에이터 분석",
    stats: [
      { label: "참여율", value: "8.5%", icon: TrendingUp },
      { label: "평균 좋아요", value: "2.4K", icon: Heart },
      { label: "팔로워", value: "28.5K", icon: Users },
    ],
    tags: ["여행", "사진", "일상"],
    personality: "외향적 탐험가",
    contentStyle: "감성적 여행기",
    color: "from-blue-500 to-cyan-400",
  },
  {
    id: 2,
    username: "foodie_momo",
    title: "푸드 크리에이터 분석",
    stats: [
      { label: "참여율", value: "12.3%", icon: TrendingUp },
      { label: "평균 좋아요", value: "5.1K", icon: Heart },
      { label: "팔로워", value: "42.1K", icon: Users },
    ],
    tags: ["맛집", "요리", "리뷰"],
    personality: "열정적인 공유자",
    contentStyle: "생생한 푸드스타그램",
    color: "from-orange-500 to-red-400",
  },
  {
    id: 3,
    username: "dev_jay",
    title: "개발자 분석",
    stats: [
      { label: "참여율", value: "6.8%", icon: TrendingUp },
      { label: "평균 좋아요", value: "1.2K", icon: Heart },
      { label: "팔로워", value: "15.3K", icon: Users },
    ],
    tags: ["개발", "기술", "커리어"],
    personality: "분석적 학습자",
    contentStyle: "정보형 콘텐츠",
    color: "from-purple-500 to-pink-400",
  },
  {
    id: 4,
    username: "fashion_luna",
    title: "패션 인플루언서 분석",
    stats: [
      { label: "참여율", value: "15.2%", icon: TrendingUp },
      { label: "평균 좋아요", value: "8.7K", icon: Heart },
      { label: "팔로워", value: "125K", icon: Users },
    ],
    tags: ["패션", "뷰티", "스타일"],
    personality: "트렌드 세터",
    contentStyle: "비주얼 중심",
    color: "from-pink-500 to-rose-400",
  },
];

/**
 * 리포트 미리보기 섹션 컴포넌트
 * 캐러셀 형태로 샘플 리포트 표시
 */
export function PreviewSection() {
  const [emblaRef] = useEmblaCarousel({ loop: true, align: "start" }, [
    Autoplay({ delay: 4000, stopOnInteraction: false }),
  ]);

  return (
    <section id="preview" className="py-20 sm:py-28 lg:py-32 px-4 sm:px-6 lg:px-8 bg-white overflow-hidden">
      <div className="max-w-6xl mx-auto">
        {/* 섹션 헤더 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12 sm:mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-500/10 to-pink-500/10 text-purple-600 text-sm font-medium mb-4">
            Sample Reports
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            이런 리포트가 생성돼요
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            AI가 분석한 다양한 유형의 인스타그램 리포트를 미리 확인핳세요
          </p>
        </motion.div>

        {/* 캐러셀 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="overflow-hidden"
          ref={emblaRef}
        >
          <div className="flex gap-6">
            {sampleReports.map((report) => (
              <div
                key={report.id}
                className="flex-[0_0_100%] min-w-0 sm:flex-[0_0_calc(50%-12px)] lg:flex-[0_0_calc(33.333%-16px)]"
              >
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  {/* 리포트 헤더 */}
                  <div
                    className={`bg-gradient-to-r ${report.color} p-6 text-white`}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <Camera className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="font-bold text-lg">@{report.username}</p>
                        <p className="text-white/80 text-sm">{report.title}</p>
                      </div>
                    </div>
                  </div>

                  {/* 리포트 콘텐츠 */}
                  <div className="p-6">
                    {/* 통계 */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      {report.stats.map((stat, idx) => (
                        <div key={idx} className="text-center">
                          <stat.icon className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                          <p className="text-lg font-bold text-gray-900">
                            {stat.value}
                          </p>
                          <p className="text-xs text-gray-500">{stat.label}</p>
                        </div>
                      ))}
                    </div>

                    {/* 분석 결과 */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-pink-500" />
                        <span className="text-sm text-gray-600">
                          성격: {" "}
                          <span className="font-semibold text-gray-900">
                            {report.personality}
                          </span>
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-4 h-4 text-purple-500" />
                        <span className="text-sm text-gray-600">
                          스타일: {" "}
                          <span className="font-semibold text-gray-900">
                            {report.contentStyle}
                          </span>
                        </span>
                      </div>
                    </div>

                    {/* 태그 */}
                    <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                      {report.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* 캐러셀 인디케이터 힌트 */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex justify-center gap-2 mt-8"
        >
          {sampleReports.map((_, idx) => (
            <div
              key={idx}
              className="w-2 h-2 rounded-full bg-gray-300"
            />
          ))}
        </motion.div>
      </div>
    </section>
  );
}
