import type { Metadata, Viewport } from "next";
import { Manrope, Noto_Sans } from "next/font/google";

import { SwRegister } from "@/components/pwa/sw-register";
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
  applicationName: "CNFund",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "CNFund",
    statusBarStyle: "default",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
    shortcut: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0a5c8f" },
    { media: "(prefers-color-scheme: dark)", color: "#11385a" },
  ],
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
        <SwRegister />
        <AppQueryProvider>{children}</AppQueryProvider>
      </body>
    </html>
  );
}
