"use client";

import { ThemeToggle } from "@/components/theme-toggle";
import { TitleScreen } from "@/components/sections/TitleScreen";
import { LevelSection } from "@/components/sections/LevelSection";
import { BossSection } from "@/components/sections/BossSection";
import { SolutionSection } from "@/components/sections/SolutionSection";
import { ArcadeTable } from "@/components/ui/ArcadeTable";
import {
  LEVEL_1_STRUCTURING,
  STRUCTURING_STATS,
  LEVEL_2_ACCOUNT_TAKEOVER,
  ACCOUNT_TAKEOVER_STATS,
  LEVEL_3_DORMANT,
  DORMANT_STATS,
  StructuringAccount,
  AccountTakeoverCase,
  DormantAccount,
} from "@/data/fraud-data";

export default function Home() {
  return (
    <main className="relative">
      {/* Theme toggle in corner */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Title Screen */}
      <TitleScreen />

      {/* Level 1: Structuring */}
      <LevelSection
        level={1}
        title="STRUCTURING"
        subtitle="BSA/AML Violation Detection"
        description="Multiple accounts are depositing exactly $7,980 - just under the $10,000 Currency Transaction Report threshold. This pattern indicates deliberate structuring to avoid federal reporting requirements."
        stats={[
          {
            label: "Accounts",
            value: STRUCTURING_STATS.totalAccounts,
            color: "primary",
          },
          {
            label: "Transactions",
            value: STRUCTURING_STATS.totalTransactions,
            color: "secondary",
          },
          {
            label: "Total Amount",
            value: `$${(STRUCTURING_STATS.totalAmount / 1000).toFixed(0)}K`,
            color: "accent",
          },
          {
            label: "Avg Txn",
            value: `$${STRUCTURING_STATS.avgTransactionAmount.toLocaleString()}`,
            color: "dino-green",
          },
        ]}
        detection={{
          title: "Detection Method: Threshold Proximity Analysis",
          method:
            "Our STRUCTURING SENTINEL monitors for repeated transactions within 80% of reporting thresholds. When an account shows 3+ transactions in this range within 30 days, it triggers enhanced review. These 6 accounts show a clear pattern of $7,980 deposits - exactly 79.8% of the $10K threshold.",
        }}
      >
        <ArcadeTable<StructuringAccount>
          data={LEVEL_1_STRUCTURING}
          columns={[
            { key: "accountId", header: "Account ID" },
            { key: "transactions", header: "Txns" },
            {
              key: "totalAmount",
              header: "Total",
              render: (v) => `$${(v as number).toLocaleString()}`,
            },
            {
              key: "avgAmount",
              header: "Avg",
              render: (v) => `$${(v as number).toLocaleString()}`,
            },
            { key: "pattern", header: "Pattern" },
          ]}
        />
      </LevelSection>

      {/* Level 2: Account Takeover */}
      <LevelSection
        level={2}
        title="ACCOUNT TAKEOVER"
        subtitle="Credential Attack Detection"
        description="Multiple accounts show signs of credential stuffing and brute force attacks. High failure rates combined with multiple source IPs indicate automated attack tools attempting to compromise accounts."
        stats={[
          {
            label: "Suspicious",
            value: ACCOUNT_TAKEOVER_STATS.totalSuspiciousAccounts,
            color: "primary",
          },
          {
            label: "Failed Attempts",
            value: ACCOUNT_TAKEOVER_STATS.totalFailedAttempts,
            color: "secondary",
          },
          {
            label: "Avg Fail Rate",
            value: `${ACCOUNT_TAKEOVER_STATS.avgFailRate}%`,
            color: "accent",
          },
          {
            label: "Geo Anomalies",
            value: ACCOUNT_TAKEOVER_STATS.geoAnomalies,
            color: "danger",
          },
        ]}
        detection={{
          title: "Detection Method: Login Velocity & Geo Analysis",
          method:
            "LOGIN GUARDIAN tracks failed login velocity, unique IP counts per account, and geographic impossibility (traveling faster than physically possible). User 'bannowanda1' shows 59 failed attempts from 12 different IPs - classic credential stuffing. 'jessica_2019' logged in from Texas and Florida within 2 hours - physically impossible travel.",
        }}
      >
        <ArcadeTable<AccountTakeoverCase>
          data={LEVEL_2_ACCOUNT_TAKEOVER}
          columns={[
            { key: "username", header: "Username" },
            { key: "failedLogins", header: "Failed" },
            { key: "successfulLogins", header: "Success" },
            {
              key: "failRate",
              header: "Fail %",
              className: "text-primary",
            },
            { key: "uniqueIPs", header: "IPs" },
            { key: "suspiciousActivity", header: "Activity" },
          ]}
        />
      </LevelSection>

      {/* Level 3: Dormant Account Abuse */}
      <LevelSection
        level={3}
        title="DORMANT ABUSE"
        subtitle="Sleeping Account Exploitation"
        description="Accounts dormant for years in the core banking system suddenly show heavy digital channel activity. This gap between core and digital records indicates potential account compromise or internal fraud."
        stats={[
          {
            label: "Compromised",
            value: DORMANT_STATS.totalDormantCompromised,
            color: "primary",
          },
          {
            label: "Avg Dormancy",
            value: `${DORMANT_STATS.avgDormancyYears} yrs`,
            color: "secondary",
          },
          {
            label: "Suspicious Amt",
            value: `$${(DORMANT_STATS.totalSuspiciousAmount / 1000000).toFixed(1)}M`,
            color: "danger",
          },
          {
            label: "Detection Gap",
            value: "CRITICAL",
            color: "accent",
          },
        ]}
        detection={{
          title: "Detection Method: Core vs Digital Activity Correlation",
          method:
            "DORMANT WATCHER cross-references Symitar core banking lastfmdate with Banno digital activity timestamps. Member #6 had no core activity since 2012 but suddenly moved $4.1M through digital channels in 2024. This 12-year gap between systems is a critical red flag indicating account compromise.",
        }}
      >
        <ArcadeTable<DormantAccount>
          data={LEVEL_3_DORMANT}
          columns={[
            { key: "memberNumber", header: "Member #" },
            { key: "lastCoreActivity", header: "Last Core" },
            { key: "digitalActivity", header: "Digital" },
            { key: "digitalTransactions", header: "Txns" },
            {
              key: "totalAmount",
              header: "Amount",
              render: (v) => `$${(v as number).toLocaleString()}`,
            },
            {
              key: "riskLevel",
              header: "Risk",
              render: (v) => (
                <span
                  className={
                    v === "CRITICAL" ? "text-primary" : "text-accent"
                  }
                >
                  {v as string}
                </span>
              ),
            },
          ]}
        />
      </LevelSection>

      {/* Final Boss: CarMeg SanDiego */}
      <BossSection />

      {/* Solution / Ending */}
      <SolutionSection />

      {/* Footer */}
      <footer className="py-8 text-center text-[10px] sm:text-xs text-secondary border-t-4 border-foreground/10">
        <p className="mb-2">FRAUDASAURUS - Fraud Detection for the Digital Age</p>
        <p>Jack Henry DevCon 2026 Hack-A-Thon</p>
      </footer>
    </main>
  );
}
