import { ThemeToggle } from "@/components/theme-toggle";
import Image from "next/image";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      {/* Theme toggle in corner */}
      <div className="fixed top-4 right-4">
        <ThemeToggle />
      </div>

      {/* 8-bit T-Rex SVG */}
      <div className="mb-10">
        <Image
          src="/dino.svg"
          alt="Fraudasaurus"
          width={400}
          height={240}
          className="w-64 h-40 sm:w-80 sm:h-48 md:w-[400px] md:h-60"
          style={{ imageRendering: "pixelated" }}
          priority
        />
      </div>

      {/* Title */}
      <h1 className="text-2xl sm:text-4xl md:text-5xl pixel-text text-primary mb-6 text-center leading-relaxed">
        FRAUDASAURUS
      </h1>

      {/* Tagline */}
      <p className="text-[10px] sm:text-sm md:text-base text-secondary mb-12 text-center leading-relaxed">
        Hunting fraud in the digital age
      </p>

      {/* Decorative pixel line */}
      <div className="flex gap-2 sm:gap-3 mb-12">
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-accent" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-primary" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-secondary" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-dino-green" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-secondary" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-primary" />
        <div className="w-4 h-4 sm:w-6 sm:h-6 bg-accent" />
      </div>

      {/* Coming Soon */}
      <div className="pixel-btn px-6 sm:px-8 py-4">
        <span className="text-foreground text-[10px] sm:text-sm retro-blink">
          COMING SOON
        </span>
      </div>

      {/* Footer */}
      <footer className="fixed bottom-6 text-center text-[10px] sm:text-xs text-secondary">
        <p>© 2025 FRAUDASAURUS</p>
      </footer>
    </main>
  );
}
