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
        subtitle="$13.9M BSA/AML Violation Ring"
        description="Six accounts making identical $7,980 transfers - just under the $10,000 CTR threshold - 4-5 times per day for 18+ months. The clearest fraud signal in the dataset. Transaction memos reference 'DEPOSIT AT ATM... JLASTNAME TX'."
        stats={[
          {
            label: "Accounts",
            value: STRUCTURING_STATS.totalAccounts,
            color: "primary",
          },
          {
            label: "Transactions",
            value: STRUCTURING_STATS.totalTransactions.toLocaleString(),
            color: "secondary",
          },
          {
            label: "Total Amount",
            value: `$${(STRUCTURING_STATS.totalAmount / 1000000).toFixed(1)}M`,
            color: "accent",
          },
          {
            label: "Avg Txn",
            value: `$${STRUCTURING_STATS.avgTransactionAmount.toLocaleString()}`,
            color: "dino-green",
          },
        ]}
        detection={{
          title: "Detection Method: Repeating Amount + Daily Aggregation",
          method:
            "STRUCTURING SENTINEL flags accounts with 3+ identical amounts ($3K-$9,999) in 7 days, or daily totals exceeding $10K with no single transaction above threshold. These 6 accounts were running since April 2024 - $31,920 to $39,900 per day per account - totaling $13.9M over 18 months.",
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
        description="Analysis of 2,144 login attempts revealed brute force patterns, credential stuffing, and suspicious IP velocity. CarMeg's own account 'ilovemlms' shows 25 failed logins from 5 IPs - managing too many fake identities."
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
            label: "Shared IP Groups",
            value: ACCOUNT_TAKEOVER_STATS.geoAnomalies,
            color: "danger",
          },
        ]}
        detection={{
          title: "Detection Method: Login Velocity & IP Analysis",
          method:
            "LOGIN GUARDIAN tracks failed login velocity and unique IP counts. 'bannowanda1' (JAMES EVANS on mposkey@ email - name mismatch!) shows 59 failures from 12 IPs. 'brandygalloway06' hit 14 consecutive failures in 2 minutes - textbook brute force. 'jessica' attempted from 6 different IPs - every attempt from a new source.",
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
        subtitle="$4M Core-Digital Gap Exploit"
        description="By joining Symitar lastfmdate with Banno transactions, we found accounts appearing dormant in core banking but actively moving money through digital channels. The real owner isn't watching - and neither was the core system."
        stats={[
          {
            label: "Compromised",
            value: DORMANT_STATS.totalDormantCompromised,
            color: "primary",
          },
          {
            label: "Avg Dormancy",
            value: `${DORMANT_STATS.avgDormancyYears}+ yrs`,
            color: "secondary",
          },
          {
            label: "Suspicious Amt",
            value: `$${(DORMANT_STATS.totalSuspiciousAmount / 1000000).toFixed(1)}M`,
            color: "danger",
          },
          {
            label: "Detection Gap",
            value: "12 YEARS",
            color: "accent",
          },
        ]}
        detection={{
          title: "Detection Method: Core vs Digital Activity Correlation",
          method:
            "DORMANT WATCHER joins symitar.account_v1_raw.lastfmdate with banno transactions_fct. Member #6 shows last core activity in October 2012 - over 12 years ago - yet has 3,120 digital transactions totaling $4.09M. This is exactly the kind of account CarMeg targets: abandoned by its owner, unmonitored by the core system.",
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
