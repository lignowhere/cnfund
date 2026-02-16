import type { Metadata } from "next";
import { Manrope, Noto_Sans } from "next/font/google";

import { AppQueryProvider } from "@/providers/query-provider";
import { getThemeBootScript } from "@/lib/theme";

import "./globals.css";

const headingFont = Manrope({
  variable: "--font-heading",
  subsets: ["latin", "vietnamese"],
  weight: ["500", "600", "700"],
});

const bodyFont = Noto_Sans({
  variable: "--font-body",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "CNFund Web",
  description: "Giao diện CNFund tối ưu mobile và desktop cho vận hành quỹ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: getThemeBootScript() }} />
      </head>
      <body className={`${headingFont.variable} ${bodyFont.variable} antialiased`}>
        <AppQueryProvider>{children}</AppQueryProvider>
      </body>
    </html>
  );
}
