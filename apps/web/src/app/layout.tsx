import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "e-Flow Enterprise",
  description: "Enterprise BPM & Workflow Automation Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
