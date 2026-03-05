"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Instagram, Menu, X, ArrowRight } from "lucide-react";
import Link from "next/link";

/**
 * 마케팅 페이지 네비게이션 컴포넌트
 * 스크롤 시 배경 변경 및 모바일 메뉴 지원
 */
export function MarketingNav() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { href: "#features", label: "기능" },
    { href: "#preview", label: "미리보기" },
    { href: "#how-it-works", label: "사용방법" },
  ];

  return (
    <>
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? "bg-white/95 backdrop-blur-md shadow-sm"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            {/* 로고 */}
            <Link
              href="/marketing"
              className="flex items-center gap-2 group"
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                  isScrolled
                    ? "bg-gradient-to-br from-yellow-400 via-pink-500 to-purple-600"
                    : "bg-white/20 backdrop-blur-sm"
                }`}
              >
                <Instagram className="w-4 h-4 text-white" />
              </div>
              <span
                className={`text-xl font-bold transition-colors ${
                  isScrolled
                    ? "bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-text text-transparent"
                    : "text-white"
                }`}
              >
                itsmegram
              </span>
            </Link>

            {/* 데스크톱 네비게이션 */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium transition-colors hover:opacity-80 ${
                    isScrolled ? "text-gray-700" : "text-white/90"
                  }`}
                >
                  {link.label}
                </a>
              ))}
            </nav>

            {/* CTA 버튼 */}
            <div className="hidden md:block">
              <Link
                href="/"
                className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-medium text-sm transition-all duration-300 min-h-[44px] ${
                  isScrolled
                    ? "bg-gradient-to-r from-pink-500 to-purple-600 text-white hover:shadow-lg"
                    : "bg-white text-gray-900 hover:bg-white/90"
                }`}
              >
                <span>분석 시작하기</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* 모바일 메뉴 버튼 */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className={`md:hidden p-2 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center ${
                isScrolled
                  ? "text-gray-700 hover:bg-gray-100"
                  : "text-white hover:bg-white/10"
              }`}
              aria-label="메뉴 열기"
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </motion.header>

      {/* 모바일 메뉴 */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-x-0 top-16 sm:top-20 z-40 md:hidden"
          >
            <div className="bg-white shadow-lg border-t border-gray-100">
              <nav className="flex flex-col p-4">
                {navLinks.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="px-4 py-3 text-gray-700 font-medium hover:bg-gray-50 rounded-lg transition-colors min-h-[44px] flex items-center"
                  >
                    {link.label}
                  </a>
                ))}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <Link
                    href="/"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center justify-center gap-2 w-full px-5 py-3 bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-full font-medium min-h-[48px]"
                  >
                    <span>분석 시작하기</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </nav>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
