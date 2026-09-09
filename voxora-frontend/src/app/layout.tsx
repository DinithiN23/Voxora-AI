import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Voxora AI — Conversational Business Intelligence",
  description:
    "Ask questions about your business data using natural language. Get instant answers, insights, charts, and dashboards powered by AI.",
  keywords: [
    "business intelligence",
    "AI",
    "conversational analytics",
    "data analytics",
    "voice BI",
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
