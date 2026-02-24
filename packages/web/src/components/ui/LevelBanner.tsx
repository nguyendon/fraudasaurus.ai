"use client";

import { motion } from "framer-motion";

interface LevelBannerProps {
  level: number;
  title: string;
  subtitle?: string;
  variant?: "normal" | "boss";
}

export function LevelBanner({
  level,
  title,
  subtitle,
  variant = "normal",
}: LevelBannerProps) {
  const isBoss = variant === "boss";

  return (
    <motion.div
      className="text-center mb-8"
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, type: "spring" }}
    >
      {/* Level indicator */}
      <motion.div
        className={`inline-block px-4 sm:px-6 py-2 mb-4 ${
          isBoss
            ? "bg-primary text-foreground boss-warning"
            : "bg-secondary text-foreground"
        }`}
        initial={{ y: -50 }}
        whileInView={{ y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
      >
        <span className="text-[10px] sm:text-sm">
          {isBoss ? "FINAL BOSS" : `LEVEL ${level}`}
        </span>
      </motion.div>

      {/* Title */}
      <motion.h2
        className={`text-lg sm:text-2xl md:text-4xl pixel-text mb-2 ${
          isBoss ? "text-primary glitch-text" : "text-primary"
        }`}
        data-text={title}
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.4 }}
      >
        {title}
      </motion.h2>

      {/* Subtitle */}
      {subtitle && (
        <motion.p
          className="text-[10px] sm:text-sm text-secondary"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
        >
          {subtitle}
        </motion.p>
      )}
    </motion.div>
  );
}
