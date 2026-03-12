import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "e-Flow Enterprise",
  description: "Enterprise BPM / workflow automation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
