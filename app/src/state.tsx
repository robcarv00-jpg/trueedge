/** App state: journal from SQLite (demo journal until the user imports),
 *  subscription tier (local until StoreKit billing is wired — the gate
 *  logic is real, the payment rail is the launch checklist's job). */
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { BetRow, mirror, MirrorReport, sharpAxes, rollingTrend, TrendPoint } from './core/mirror';
import * as db from './storage/db';
import demoJournal from './core/demo_journal.json';

export type Tier = 'free' | 'plus' | 'pro';

interface AppState {
  ready: boolean;
  usingDemo: boolean;
  bets: BetRow[];
  report: MirrorReport | null;
  axes: { skill: number; discipline: number } | null;
  trend: TrendPoint[];
  tier: Tier;
  setTier: (t: Tier) => void;
  estimateCount: number;
  refresh: () => Promise<void>;
  loadDemo: () => Promise<void>;
  wipe: () => Promise<void>;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [bets, setBets] = useState<BetRow[]>([]);
  const [usingDemo, setUsingDemo] = useState(false);
  const [tier, setTierState] = useState<Tier>('free');
  const [estimateCount, setEstimateCount] = useState(0);

  const refresh = async () => {
    const rows = await db.listBets();
    if (rows.length) {
      setBets(rows); setUsingDemo(false);
    } else {
      setBets(demoJournal as BetRow[]); setUsingDemo(true);
    }
    setEstimateCount(await db.countEstimates());
    const t = await db.getKv('tier');
    if (t === 'plus' || t === 'pro' || t === 'free') setTierState(t);
  };

  useEffect(() => { (async () => { await db.initDb(); await refresh(); setReady(true); })(); }, []);

  const setTier = (t: Tier) => { setTierState(t); void db.setKv('tier', t); };

  const loadDemo = async () => {
    await db.clearBets();
    await db.addBets(demoJournal as BetRow[]);
    await refresh();
  };

  const wipe = async () => { await db.clearBets(); await refresh(); };

  const { report, axes, trend } = useMemo(() => {
    if (!bets.length) return { report: null, axes: null, trend: [] as TrendPoint[] };
    const r = mirror(bets);
    return { report: r, axes: sharpAxes(r), trend: rollingTrend(bets) };
  }, [bets]);

  return (
    <Ctx.Provider value={{
      ready, usingDemo, bets, report, axes, trend, tier, setTier,
      estimateCount, refresh, loadDemo, wipe,
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useApp(): AppState {
  const s = useContext(Ctx);
  if (!s) throw new Error('useApp outside AppProvider');
  return s;
}
