"use client";

import { motion } from "framer-motion";
import { BossProfile } from "@/data/fraud-data";

interface WantedPosterProps {
  profile: BossProfile;
}

export function WantedPoster({ profile }: WantedPosterProps) {
  return (
    <motion.div
      className="wanted-poster max-w-md mx-auto p-6 sm:p-8 text-center"
      initial={{ opacity: 0, rotateX: -90 }}
      whileInView={{ opacity: 1, rotateX: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, type: "spring" }}
    >
      {/* WANTED header */}
      <motion.div
        className="text-2xl sm:text-4xl md:text-5xl font-bold text-[#8b4513] mb-4"
        initial={{ scale: 0 }}
        whileInView={{ scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
      >
        WANTED
      </motion.div>

      {/* Reward */}
      <div className="text-[10px] sm:text-sm text-[#8b4513]/80 mb-4">
        REWARD: ${profile.totalSuspiciousAmount.toLocaleString()}
      </div>

      {/* Silhouette placeholder */}
      <motion.div
        className="w-32 h-32 sm:w-48 sm:h-48 mx-auto mb-4 bg-[#8b4513]/20 border-4 border-[#8b4513] flex items-center justify-center"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5 }}
      >
        <span className="text-4xl sm:text-6xl">?</span>
      </motion.div>

      {/* Name */}
      <motion.div
        className="text-lg sm:text-2xl font-bold text-[#8b4513] mb-1"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7 }}
      >
        {profile.name}
      </motion.div>

      {/* Alias */}
      <motion.div
        className="text-sm sm:text-base text-[#8b4513]/80 mb-4"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.8 }}
      >
        a.k.a. &quot;{profile.alias}&quot;
      </motion.div>

      {/* Crimes */}
      <motion.div
        className="text-[8px] sm:text-[10px] text-[#8b4513] mb-4"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.9 }}
      >
        <div className="font-bold mb-1">CHARGES:</div>
        <ul className="space-y-1">
          {profile.crimeTypes.map((crime, i) => (
            <li key={i}>{crime}</li>
          ))}
        </ul>
      </motion.div>

      {/* Stats */}
      <motion.div
        className="flex justify-center gap-4 sm:gap-8 text-[8px] sm:text-[10px] text-[#8b4513]"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 1 }}
      >
        <div>
          <div className="font-bold">{profile.accounts}</div>
          <div>ACCOUNTS</div>
        </div>
        <div>
          <div className="font-bold">{profile.usernames.length}</div>
          <div>ALIASES</div>
        </div>
      </motion.div>
    </motion.div>
  );
}
