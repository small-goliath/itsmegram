import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

/**
 * 기본 메타데이터
 * 각 페이지에서 override 가능
 */
export const metadata: Metadata = {
  title: {
    default: "itsmegram - AI로 분석하는 나의 인스타그램",
    template: "%s | itsmegram",
  },
  description:
    "인스타그램 계정을 AI로 분석하여 콘텐츠 성향, 라이프스타일, 성격 특징을 파악하세요.",
  keywords: ["인스타그램", "AI 분석", "인스타 분석", "itsmegram"],
  authors: [{ name: "itsmegram" }],
  creator: "itsmegram",
  metadataBase: new URL("http://localhost:3000"),
  openGraph: {
    type: "website",
    locale: "ko_KR",
    siteName: "itsmegram",
  },
  twitter: {
    card: "summary_large_image",
  },
};

/**
 * 루트 레이아웃
 * 전체 앱의 기본 구조를 정의
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          forcedTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          {children}
          <Toaster position="bottom-center" />
        </ThemeProvider>
      </body>
    </html>
  );
}
