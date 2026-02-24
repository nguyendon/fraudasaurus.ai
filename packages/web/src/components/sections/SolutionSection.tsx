"use client";

import { motion } from "framer-motion";
import { PixelCard } from "@/components/ui/PixelCard";
import { StatBlock } from "@/components/ui/StatBlock";
import { DETECTORS, RISK_TIERS, SOLUTION_STATS, VICTORY_MESSAGE } from "@/data/fraud-data";

export function SolutionSection() {
  return (
    <section className="min-h-screen py-12 sm:py-20 px-4 sm:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Victory Banner */}
        <motion.div
          className="text-center mb-8 sm:mb-12"
          initial={{ opacity: 0, scale: 0.5 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 100 }}
        >
          <motion.div
            className="text-3xl sm:text-5xl md:text-7xl pixel-text text-dino-green mb-4"
            animate={{
              textShadow: [
                "4px 4px 0 var(--dino-dark)",
                "4px 4px 20px var(--dino-green), 4px 4px 0 var(--dino-dark)",
                "4px 4px 0 var(--dino-dark)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            YOU WIN!
          </motion.div>
          <p className="text-[10px] sm:text-sm text-secondary">
            FRAUD RING IDENTIFIED - DEFENSE SYSTEM DEPLOYED
          </p>
        </motion.div>

        {/* Solution Stats */}
        <StatBlock
          title="MISSION RESULTS"
          stats={[
            {
              label: "Detectors",
              value: SOLUTION_STATS.detectorsDeployed,
              color: "dino-green",
            },
            {
              label: "Alerts",
              value: SOLUTION_STATS.totalAlertsGenerated,
              color: "secondary",
            },
            {
              label: "Cases",
              value: SOLUTION_STATS.casesOpened,
              color: "accent",
            },
            {
              label: "Prevented",
              value: `$${(SOLUTION_STATS.fraudPrevented / 1000000).toFixed(1)}M`,
              color: "primary",
            },
          ]}
          className="mb-8 sm:mb-12"
        />

        {/* The 4 Detectors */}
        <motion.div
          className="mb-8 sm:mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="text-sm sm:text-lg text-center text-secondary mb-6 uppercase">
            The 4-Detector Defense System
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {DETECTORS.map((detector, i) => (
              <motion.div
                key={detector.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
              >
                <PixelCard className="h-full" animate={false}>
                  <div className="flex items-start gap-3 sm:gap-4">
                    {/* Icon */}
                    <div
                      className="w-12 h-12 sm:w-16 sm:h-16 flex items-center justify-center shrink-0"
                      style={{ backgroundColor: detector.color }}
                    >
                      <span className="text-[10px] sm:text-xs font-bold text-dino-dark">
                        {detector.icon}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div
                        className="text-xs sm:text-sm font-bold mb-2"
                        style={{ color: detector.color }}
                      >
                        {detector.name}
                      </div>
                      <p className="text-[8px] sm:text-[10px] text-foreground/70 mb-3">
                        {detector.description}
                      </p>
                      <div className="space-y-1">
                        {detector.metrics.map((metric, j) => (
                          <div
                            key={j}
                            className="text-[8px] sm:text-[10px] text-foreground/50 flex items-center gap-2"
                          >
                            <span
                              className="w-1.5 h-1.5"
                              style={{ backgroundColor: detector.color }}
                            />
                            {metric}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </PixelCard>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Risk Tiers */}
        <motion.div
          className="pixel-border bg-background p-4 sm:p-6 mb-8 sm:mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-4 uppercase">
            Risk Scoring System:
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            {RISK_TIERS.map((tier, i) => (
              <motion.div
                key={tier.tier}
                className="text-center p-3"
                style={{ borderLeft: `4px solid ${tier.color}` }}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <div
                  className="text-sm sm:text-lg font-bold"
                  style={{ color: tier.color }}
                >
                  {tier.tier}
                </div>
                <div className="text-[10px] sm:text-xs text-foreground/60">
                  Score: {tier.score}
                </div>
                <div className="text-[8px] sm:text-[10px] text-foreground/40 mt-1">
                  {tier.action}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Victory Terminal */}
        <motion.div
          className="bg-dino-dark p-4 sm:p-6 pixel-border mb-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="w-3 h-3 bg-dino-green" />
            <div className="w-3 h-3 bg-accent" />
            <div className="w-3 h-3 bg-primary" />
            <span className="text-[8px] sm:text-[10px] text-dino-green ml-2">
              MISSION DEBRIEF
            </span>
          </div>
          <pre className="text-[8px] sm:text-[10px] text-dino-green whitespace-pre-wrap leading-relaxed font-mono">
            {VICTORY_MESSAGE}
          </pre>
        </motion.div>

        {/* Team Credits */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-3 uppercase">
            Created By
          </div>
          <div className="text-xs sm:text-sm text-foreground/80 space-y-1">
            <div>Dylan Martinez</div>
            <div>Don Nguyen</div>
            <div>Alan Bixby</div>
            <div>Kyle Greer</div>
            <div>Mary Ann Woods</div>
          </div>
        </motion.div>

        {/* Victory Video */}
        <motion.div
          className="flex justify-center mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <video
            src="/dino_defender.mp4"
            autoPlay
            loop
            muted
            playsInline
            className="w-64 sm:w-80 md:w-96 rounded-lg"
            style={{ imageRendering: "pixelated" }}
          />
        </motion.div>

        {/* Credits */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
        >
          <div className="text-[10px] sm:text-xs text-secondary mb-4">
            JACK HENRY DEVCON 2026 HACK-A-THON
          </div>
          <div className="flex justify-center gap-2 sm:gap-3">
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-accent" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-primary" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-secondary" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-dino-green" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-secondary" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-primary" />
            <div className="w-3 h-3 sm:w-4 sm:h-4 bg-accent" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}
