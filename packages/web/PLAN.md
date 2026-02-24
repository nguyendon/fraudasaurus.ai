# Fraud Analyst Dashboard - Design & Implementation Plan

## 1. Overview
The Fraud Analyst Dashboard is a specialized tool for detecting and investigating financial fraud patterns, specifically focused on "Structuring" (smurfing) and Identity Fraud ("CarMeg" case). It provides analysts with a high-level alert feed and deep-dive investigation capabilities.

## 2. Core Features
- **Alert Feed**: Real-time stream of detected fraud patterns (Structuring, Account Takeover, etc.).
- **Identity Graph**: Visualization of linked accounts, emails, and devices to catch identity spoofing.
- **Transaction Timeline**: Visual history of transactions to spot structuring patterns (e.g., repeated $7,980 transfers).
- **Risk Scoring**: Automated risk assessment for users and accounts.

## 3. Data Models (TypeScript Interfaces)

### User Profile
```typescript
interface UserProfile {
  userId: string;
  username: string;
  fullName: string;
  email: string;
  riskScore: number; // 0-100
  status: 'active' | 'frozen' | 'under_review';
  memberNumber?: string;
  associatedDevices: string[]; // IP addresses or device IDs
}
```

### Transaction
```typescript
interface Transaction {
  id: string;
  accountId: string;
  date: string; // ISO date
  amount: number;
  type: 'debit' | 'credit';
  memo: string;
  category: string;
  isStructuringSuspect: boolean; // Flag for $2k-$10k range
}
```

### Alert
```typescript
interface Alert {
  id: string;
  type: 'structuring' | 'identity_link' | 'velocity' | 'watch_list';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'new' | 'investigating' | 'resolved' | 'dismissed';
  timestamp: string;
  targetUser: UserProfile;
  summary: string;
}
```

## 4. Component Architecture

### Layout (`src/app/layout.tsx`)
- **SidebarNavigation**: Links to Dashboard, Cases, Settings.
- **TopBar**: Search, User profile, Global notifications.

### Dashboard Home (`src/app/page.tsx`)
- **StatsOverview**: Key metrics (Open Alerts, High Risk Users, Fraud Value Prevented).
- **AlertFeed**: Scrollable list of recent alerts.
- **RiskHeatmap**: Visualization of fraud hotspots (geographic or temporal).

### Investigation View (`src/app/cases/[id]/page.tsx`)
- **CaseHeader**: Subject details, current status, assignee.
- **NetworkGraph**: Interactive node-link diagram showing relationships (Users <-> Emails <-> IPs).
- **TransactionTimeline**: Chart showing transaction volume/velocity over time.
- **EvidenceLog**: List of flagged activities supporting the case.

## 5. Mock Data Strategy
We will create rich static data to simulate a live environment without a backend.
- `mock-carmeg.ts`: Contains the "Meg Bannister" identity ring data (multiple users, shared emails/IPs).
- `mock-structuring.ts`: Contains the transaction logs showing the $7,980 patterns.
- `mock-alerts.ts`: A mixed feed of normal and suspicious activities.

## 6. Implementation Steps (Todo List)

### Phase 1: Foundation & Data
1. [ ] Setup basic Next.js layout with Tailwind & ThemeProvider.
2. [ ] Create TypeScript interfaces for all data models.
3. [ ] Implement `mock-carmeg.ts` (Identity Graph data).
4. [ ] Implement `mock-structuring.ts` (Transaction data).
5. [ ] Implement `mock-alerts.ts` (Dashboard feed data).

### Phase 2: Core Components
6. [ ] Build `RiskScoreCard` component (Visual indicator of risk level).
7. [ ] Build `AlertCard` component for the feed.
8. [ ] Build `TransactionRow` and `TransactionTable` components.

### Phase 3: Visualizations
9. [ ] Implement `NetworkGraph` using `react-force-graph` or similar (or SVG/Canvas custom).
10. [ ] Implement `TransactionTimeline` using Recharts or simple SVG bars.

### Phase 4: Views & Integration
11. [ ] Assemble `DashboardHome` page.
12. [ ] Assemble `InvestigationView` page.
13. [ ] Add navigation and interaction (linking alerts to investigations).

## 7. Technology Stack
- **Framework**: Next.js 15+ (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Charts**: Recharts (if needed) or custom SVG
- **State**: React Context or local state (sufficient for mock demo)
