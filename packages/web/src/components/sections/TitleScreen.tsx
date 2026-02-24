"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import { ScrollIndicator } from "@/components/ui/ScrollIndicator";
import { MISSION_BRIEFING } from "@/data/fraud-data";

export function TitleScreen() {
  return (
    <section className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-8 relative">
      {/* Scanlines overlay */}
      <div className="scanlines fixed inset-0 pointer-events-none" />

      {/* Dino */}
      <motion.div
        className="mb-6 sm:mb-10"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <Image
          src="/dino.svg"
          alt="Fraudasaurus"
          width={400}
          height={240}
          className="w-48 h-28 sm:w-64 sm:h-40 md:w-80 md:h-48 lg:w-[400px] lg:h-60"
          style={{ imageRendering: "pixelated" }}
          priority
        />
      </motion.div>

      {/* Title */}
      <motion.h1
        className="text-xl sm:text-3xl md:text-4xl lg:text-5xl pixel-text text-primary mb-4 sm:mb-6 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.3 }}
      >
        FRAUDASAURUS
      </motion.h1>

      {/* Tagline */}
      <motion.p
        className="text-[10px] sm:text-sm text-secondary mb-6 sm:mb-8 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.35, duration: 0.3 }}
      >
        FRAUD DETECTION FOR THE DIGITAL AGE
      </motion.p>

      {/* Press Start */}
      <motion.div
        className="pixel-btn px-6 sm:px-8 py-3 sm:py-4 mb-8 sm:mb-12 cursor-pointer"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        onClick={() => document.getElementById("level-1")?.scrollIntoView({ behavior: "smooth" })}
      >
        <span className="text-foreground text-[10px] sm:text-sm press-start-blink">
          SCROLL TO START
        </span>
      </motion.div>

      {/* Mission Briefing Terminal */}
      <motion.div
        className="max-w-2xl w-full bg-dino-dark p-4 sm:p-6 pixel-border mb-8"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 bg-primary" />
          <div className="w-3 h-3 bg-accent" />
          <div className="w-3 h-3 bg-dino-green" />
          <span className="text-[8px] sm:text-[10px] text-dino-green ml-2">
            MISSION BRIEFING
          </span>
        </div>
        <pre className="text-[8px] sm:text-[10px] text-dino-green whitespace-pre-wrap leading-relaxed font-mono">
          {MISSION_BRIEFING}
        </pre>
        <div className="mt-4 h-4 border-r-4 border-dino-green w-fit animate-pulse">
          <span className="text-dino-green text-[10px]">_</span>
        </div>
      </motion.div>

      {/* Decorative pixel line */}
      <motion.div
        className="flex gap-2 sm:gap-3 mb-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4 }}
      >
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-accent" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-primary" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-secondary" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-dino-green" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-secondary" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-primary" />
        <div className="w-3 h-3 sm:w-4 sm:h-4 bg-accent" />
      </motion.div>

      <ScrollIndicator text="BEGIN INVESTIGATION" targetId="level-1" />
    </section>
  );
}
