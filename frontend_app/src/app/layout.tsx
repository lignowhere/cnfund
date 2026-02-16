import type { Metadata } from "next";
import { Manrope, Noto_Sans } from "next/font/google";
import "./globals.css";
import { AppQueryProvider } from "@/providers/query-provider";

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
  description: "Giao diện CNFund tối ưu mobile cho lộ trình thay thế Streamlit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className={`${headingFont.variable} ${bodyFont.variable} antialiased`}>
        <AppQueryProvider>{children}</AppQueryProvider>
      </body>
    </html>
  );
}
