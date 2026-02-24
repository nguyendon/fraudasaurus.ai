"use client";

import { motion } from "framer-motion";
import { LevelBanner } from "@/components/ui/LevelBanner";
import { WantedPoster } from "@/components/ui/WantedPoster";
import { StatBlock } from "@/components/ui/StatBlock";
import { ScrollIndicator } from "@/components/ui/ScrollIndicator";
import { FINAL_BOSS, BOSS_STATS } from "@/data/fraud-data";

export function BossSection() {
  return (
    <section className="min-h-screen py-12 sm:py-20 px-4 sm:px-8 relative">
      {/* Warning overlay effect */}
      <motion.div
        className="absolute inset-0 bg-primary/5 pointer-events-none"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        animate={{
          opacity: [0.05, 0.1, 0.05],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Boss Warning */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <motion.div
            className="inline-block px-4 py-2 bg-primary text-foreground text-[10px] sm:text-xs mb-4"
            animate={{
              scale: [1, 1.05, 1],
              boxShadow: [
                "0 0 0 rgba(217, 87, 99, 0)",
                "0 0 30px rgba(217, 87, 99, 0.5)",
                "0 0 0 rgba(217, 87, 99, 0)",
              ],
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            WARNING: BOSS ENCOUNTER
          </motion.div>
        </motion.div>

        <LevelBanner
          level={4}
          title="CARMEG SANDIEGO"
          subtitle="The mastermind behind the fraud ring"
          variant="boss"
        />

        {/* Wanted Poster */}
        <motion.div
          className="mb-8 sm:mb-12"
          initial={{ opacity: 0, rotateY: 90 }}
          whileInView={{ opacity: 1, rotateY: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, type: "spring" }}
        >
          <WantedPoster profile={FINAL_BOSS} />
        </motion.div>

        {/* Boss Stats */}
        <StatBlock
          title="CRIMINAL PROFILE"
          stats={[
            {
              label: "Linked Accounts",
              value: BOSS_STATS.totalLinkedAccounts,
              color: "primary",
            },
            {
              label: "Known Aliases",
              value: BOSS_STATS.totalUsernames,
              color: "secondary",
            },
            {
              label: "Duration",
              value: BOSS_STATS.operationDuration,
              color: "accent",
            },
            {
              label: "Est. Loss",
              value: `$${(BOSS_STATS.estimatedLoss / 1000000).toFixed(1)}M`,
              color: "danger",
            },
          ]}
          className="mb-8"
        />

        {/* Connected Accounts */}
        <motion.div
          className="pixel-border bg-background p-4 sm:p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-4 uppercase">
            Linked Accounts:
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {FINAL_BOSS.linkedAccounts.map((account, i) => (
              <motion.div
                key={account}
                className="bg-dino-dark px-3 py-2 text-[8px] sm:text-[10px] text-dino-green"
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
              >
                {account}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Known Usernames */}
        <motion.div
          className="pixel-border bg-background p-4 sm:p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-4 uppercase">
            Known Usernames:
          </div>
          <div className="flex flex-wrap gap-2">
            {FINAL_BOSS.usernames.map((username, i) => (
              <motion.div
                key={username}
                className="bg-primary/20 border-2 border-primary px-3 py-1 text-[8px] sm:text-[10px] text-primary"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                @{username}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Boss Defeated */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
        >
          <motion.div
            className="inline-block px-6 py-3 bg-dino-green text-foreground text-xs sm:text-sm"
            animate={{
              boxShadow: [
                "0 0 0 rgba(55, 148, 110, 0)",
                "0 0 30px rgba(55, 148, 110, 0.5)",
                "0 0 0 rgba(55, 148, 110, 0)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            TARGET IDENTIFIED
          </motion.div>
        </motion.div>

        <ScrollIndicator text="VIEW SOLUTION" />
      </div>
    </section>
  );
}
