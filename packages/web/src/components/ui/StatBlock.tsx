"use client";

import { motion } from "framer-motion";

interface Stat {
  label: string;
  value: string | number;
  color?: "primary" | "secondary" | "accent" | "dino-green" | "danger";
}

interface StatBlockProps {
  stats: Stat[];
  title?: string;
  className?: string;
}

export function StatBlock({ stats, title, className = "" }: StatBlockProps) {
  const colorMap = {
    primary: "text-primary",
    secondary: "text-secondary",
    accent: "text-accent",
    "dino-green": "text-dino-green",
    danger: "text-primary",
  };

  return (
    <motion.div
      className={`pixel-border bg-dino-dark p-4 ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.3 }}
    >
      {title && (
        <div className="text-[10px] sm:text-xs text-dino-green mb-3 uppercase">
          {title}
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            className="text-center"
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
          >
            <div
              className={`text-lg sm:text-2xl md:text-3xl font-bold ${colorMap[stat.color || "dino-green"]}`}
            >
              {typeof stat.value === "number"
                ? stat.value.toLocaleString()
                : stat.value}
            </div>
            <div className="text-[8px] sm:text-[10px] text-foreground/70 uppercase">
              {stat.label}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
