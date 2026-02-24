"use client";

import { motion } from "framer-motion";

interface ScrollIndicatorProps {
  text?: string;
  targetId?: string;
}

export function ScrollIndicator({
  text = "SCROLL TO CONTINUE",
  targetId,
}: ScrollIndicatorProps) {
  const handleClick = () => {
    if (targetId) {
      document.getElementById(targetId)?.scrollIntoView({ behavior: "smooth" });
    } else {
      window.scrollBy({ top: window.innerHeight, behavior: "smooth" });
    }
  };

  return (
    <motion.div
      className="flex flex-col items-center gap-2 py-8 cursor-pointer"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ delay: 0.5 }}
      onClick={handleClick}
    >
      <span className="text-[8px] sm:text-[10px] text-secondary">{text}</span>
      <motion.div
        className="float-animation"
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          className="text-secondary"
        >
          <path
            d="M4 8L12 16L20 8"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="square"
          />
        </svg>
      </motion.div>
    </motion.div>
  );
}
