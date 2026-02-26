import type { Metadata } from "next";
import { Press_Start_2P } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import "./globals.css";

const pressStart = Press_Start_2P({
  weight: "400",
  variable: "--font-pixel",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Fraudasaurus",
  description: "Fraud detection for the digital age",
  manifest: "/manifest.webmanifest",
  themeColor: "#222034",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Fraudasaurus",
  },
  openGraph: {
    title: "Fraudasaurus",
    description: "Fraud detection for the digital age",
  },
  twitter: {
    card: "summary_large_image",
    title: "Fraudasaurus",
    description: "Fraud detection for the digital age",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${pressStart.variable}`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
