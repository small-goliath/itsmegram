"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Loader2 } from "lucide-react";

/**
 * Username 입력 폼 컴포넌트
 * 인스타그램 아이디를 입력받아 분석 페이지로 이동
 */
export function UsernameForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // 인스타그램 username 유효성 검증 패턴
  const USERNAME_PATTERN = /^[a-zA-Z0-9._]{1,30}$/;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // 유효성 검증
    if (!username.trim()) {
      setError("아이디를 입력해주세요");
      return;
    }

    if (!USERNAME_PATTERN.test(username)) {
      setError("올바른 인스타그램 아이디 형식이 아닙니다");
      return;
    }

    setIsLoading(true);

    // /report 페이지로 이동 (username을 query param으로 전달)
    router.push(`/report?username=${encodeURIComponent(username.trim())}`);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md mx-auto">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Input
            type="text"
            placeholder="인스타그램 아이디를 입력하세요"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              setError("");
            }}
            pattern="^[a-zA-Z0-9._]{1,30}$"
            maxLength={30}
            disabled={isLoading}
            className="h-14 px-5 text-base bg-white/95 backdrop-blur-sm border-0 shadow-lg focus-visible:ring-2 focus-visible:ring-white/50 placeholder:text-gray-400"
            aria-label="인스타그램 아이디"
            aria-invalid={error ? "true" : "false"}
          />
        </div>
        <Button
          type="submit"
          disabled={isLoading}
          className="h-14 px-8 bg-white text-pink-600 hover:bg-white/90 font-semibold text-base shadow-lg transition-all duration-200 hover:scale-105 disabled:opacity-70 disabled:hover:scale-100"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              분석중...
            </>
          ) : (
            <>
              <Search className="mr-2 h-5 w-5" />
              분석하기
            </>
          )}
        </Button>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <p className="mt-3 text-sm text-white/90 text-center" role="alert">
          {error}
        </p>
      )}

      {/* 입력 힌트 */}
      <p className="mt-3 text-xs text-white/70 text-center">
        @ 없이 아이디만 입력해주세요 (예: itsme_gram)
      </p>
    </form>
  );
}
