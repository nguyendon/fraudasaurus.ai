"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface PixelCardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "boss" | "success";
  animate?: boolean;
}

export function PixelCard({
  children,
  className = "",
  variant = "default",
  animate = true,
}: PixelCardProps) {
  const variantStyles = {
    default: "bg-background pixel-border",
    boss: "bg-background boss-warning border-4 border-primary",
    success: "bg-dino-green/20 pixel-border border-dino-green",
  };

  const content = (
    <div className={`p-4 sm:p-6 ${variantStyles[variant]} ${className}`}>
      {children}
    </div>
  );

  if (!animate) {
    return content;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.4 }}
      className={`${variantStyles[variant]} ${className}`}
    >
      <div className="p-4 sm:p-6">{children}</div>
    </motion.div>
  );
}
