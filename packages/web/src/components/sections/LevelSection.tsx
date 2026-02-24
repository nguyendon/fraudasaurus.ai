"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { LevelBanner } from "@/components/ui/LevelBanner";
import { StatBlock } from "@/components/ui/StatBlock";
import { ScrollIndicator } from "@/components/ui/ScrollIndicator";

interface LevelSectionProps {
  level: number;
  title: string;
  subtitle: string;
  description: string;
  stats: Array<{
    label: string;
    value: string | number;
    color?: "primary" | "secondary" | "accent" | "dino-green" | "danger";
  }>;
  children: ReactNode;
  detection: {
    title: string;
    method: string;
  };
}

export function LevelSection({
  level,
  title,
  subtitle,
  description,
  stats,
  children,
  detection,
}: LevelSectionProps) {
  return (
    <section className="min-h-screen py-12 sm:py-20 px-4 sm:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Level Banner */}
        <LevelBanner level={level} title={title} subtitle={subtitle} />

        {/* Description */}
        <motion.div
          className="text-center mb-8 sm:mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-[10px] sm:text-sm text-foreground/80 max-w-2xl mx-auto">
            {description}
          </p>
        </motion.div>

        {/* Stats */}
        <StatBlock stats={stats} title="THREAT ANALYSIS" className="mb-8" />

        {/* Evidence Table / Content */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-4 uppercase">
            Evidence Collected:
          </div>
          {children}
        </motion.div>

        {/* Detection Method */}
        <motion.div
          className="pixel-border bg-dino-green/10 p-4 sm:p-6"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-6 h-6 sm:w-8 sm:h-8 bg-dino-green flex items-center justify-center">
              <span className="text-foreground text-[10px] sm:text-xs">
                {level}
              </span>
            </div>
            <span className="text-xs sm:text-sm text-dino-green font-bold uppercase">
              {detection.title}
            </span>
          </div>
          <p className="text-[10px] sm:text-xs text-foreground/80">
            {detection.method}
          </p>
        </motion.div>

        {/* Level Complete */}
        <motion.div
          className="text-center mt-8 sm:mt-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
        >
          <div className="inline-block px-4 sm:px-6 py-2 bg-dino-green text-foreground text-[10px] sm:text-xs">
            LEVEL {level} COMPLETE
          </div>
        </motion.div>

        <ScrollIndicator />
      </div>
    </section>
  );
}
