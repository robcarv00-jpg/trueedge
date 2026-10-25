/** On-device storage (expo-sqlite). The v1 privacy rule: bet data
 *  never leaves the phone — no accounts, no sync, no backend. */
import * as SQLite from 'expo-sqlite';
import { BetRow } from '../core/mirror';

let db: SQLite.SQLiteDatabase | null = null;

export async function initDb(): Promise<void> {
  if (db) return;
  db = await SQLite.openDatabaseAsync('trueedge.db');
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS bets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      market TEXT NOT NULL, odds INTEGER NOT NULL, mins INTEGER NOT NULL,
      stake REAL NOT NULL, close_a INTEGER NOT NULL, close_b INTEGER NOT NULL,
      won INTEGER NOT NULL, sport TEXT, placed_at TEXT, hour INTEGER, dow INTEGER
    );
    CREATE TABLE IF NOT EXISTS estimates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at TEXT NOT NULL, market_price REAL NOT NULL,
      stated_prob REAL NOT NULL, odds INTEGER NOT NULL,
      stake INTEGER NOT NULL DEFAULT 100,
      won INTEGER  -- NULL until graded; de-bias (Pro) reads these
    );
    CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
  `);
}

function rowToBet(r: Record<string, unknown>): BetRow {
  const bet: BetRow = {
    market: String(r.market), odds: Number(r.odds), mins: Number(r.mins),
    stake: Number(r.stake), close: [Number(r.close_a), Number(r.close_b)],
    won: Number(r.won) === 1,
  };
  if (r.sport) bet.sport = String(r.sport);
  if (r.placed_at) bet.placed_at = String(r.placed_at);
  if (r.hour !== null && r.hour !== undefined) bet.hour = Number(r.hour);
  if (r.dow !== null && r.dow !== undefined) bet.dow = Number(r.dow);
  return bet;
}

export async function listBets(): Promise<BetRow[]> {
  if (!db) await initDb();
  const rows = await db!.getAllAsync<Record<string, unknown>>(
    'SELECT * FROM bets ORDER BY id ASC');
  return rows.map(rowToBet);
}

export async function addBets(bets: BetRow[]): Promise<void> {
  if (!db) await initDb();
  for (const b of bets) {
    await db!.runAsync(
      `INSERT INTO bets (market, odds, mins, stake, close_a, close_b, won, sport, placed_at, hour, dow)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      b.market, b.odds, b.mins, b.stake, b.close[0], b.close[1], b.won ? 1 : 0,
      b.sport ?? null, b.placed_at ?? null, b.hour ?? null, b.dow ?? null);
  }
}

export async function clearBets(): Promise<void> {
  if (!db) await initDb();
  await db!.runAsync('DELETE FROM bets');
}

export async function addEstimate(e: {
  marketPrice: number; statedProb: number; odds: number; stake?: number;
}): Promise<void> {
  if (!db) await initDb();
  await db!.runAsync(
    'INSERT INTO estimates (created_at, market_price, stated_prob, odds, stake) VALUES (?, ?, ?, ?, ?)',
    new Date().toISOString(), e.marketPrice, e.statedProb, e.odds, e.stake ?? 100);
}

export async function countEstimates(): Promise<number> {
  if (!db) await initDb();
  const r = await db!.getFirstAsync<{ n: number }>('SELECT COUNT(*) AS n FROM estimates');
  return r?.n ?? 0;
}

export async function gradeOldestEstimate(won: boolean): Promise<void> {
  if (!db) await initDb();
  await db!.runAsync(
    'UPDATE estimates SET won = ? WHERE id = (SELECT MIN(id) FROM estimates WHERE won IS NULL)',
    won ? 1 : 0);
}

export async function getKv(key: string): Promise<string | null> {
  if (!db) await initDb();
  const r = await db!.getFirstAsync<{ value: string }>(
    'SELECT value FROM kv WHERE key = ?', key);
  return r?.value ?? null;
}

export async function setKv(key: string, value: string): Promise<void> {
  if (!db) await initDb();
  await db!.runAsync(
    'INSERT INTO kv (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
    key, value);
}
