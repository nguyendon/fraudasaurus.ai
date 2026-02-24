"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="pixel-btn w-12 h-12 flex items-center justify-center" aria-label="Toggle theme">
        <span className="text-xl">?</span>
      </button>
    );
  }

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="pixel-btn w-12 h-12 flex items-center justify-center"
      aria-label="Toggle theme"
    >
      <span className="text-xl">{theme === "dark" ? "☀️" : "🌙"}</span>
    </button>
  );
}
