import React, { useState } from 'react';
import { Alert, ScrollView, Text, TextInput, TouchableOpacity, View } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import * as FileSystem from 'expo-file-system/legacy';
import { useApp } from '../state';
import { Screen, H1, Label, Card , BrandHeader} from '../ui';
import { importJournalCsv } from '../core/csv';
import { implied } from '../core/odds';
import * as db from '../storage/db';
import { colors, MIN_TOUCH, radius, space, type } from '../theme';

const input = {
  backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1,
  borderRadius: radius.chip, color: colors.text, padding: 12,
  fontSize: type.body, minHeight: MIN_TOUCH, marginVertical: 4,
} as const;

function Btn({ title, onPress, accent = false }: {
  title: string; onPress: () => void; accent?: boolean;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{
        minHeight: MIN_TOUCH, justifyContent: 'center', alignItems: 'center',
        borderRadius: radius.chip, marginVertical: 6, paddingHorizontal: 16,
        backgroundColor: accent ? colors.accentDeep : colors.surface,
        borderColor: colors.border, borderWidth: 1,
      }}>
      <Text style={{ color: accent ? colors.onAccent : colors.text, fontSize: type.body, fontWeight: '600' }}>
        {title}
      </Text>
    </TouchableOpacity>
  );
}

/** Log bets (manual + CSV import) and log sealed pre-game estimates —
 *  "your number": one field, pre-filled with the market price, exactly
 *  the TrueEdge design rule. Estimates power de-bias (Pro). */
export default function LogScreen() {
  const { refresh, loadDemo, wipe, bets } = useApp();
  const [odds, setOdds] = useState('-110');
  const [close, setClose] = useState('-110');
  const [stake, setStake] = useState('25');
  const [mins, setMins] = useState('180');
  const [market, setMarket] = useState('spread');
  const [yourPct, setYourPct] = useState('');

  const importCsv = async () => {
    const res = await DocumentPicker.getDocumentAsync({ type: 'text/csv' });
    if (res.canceled || !res.assets?.length) return;
    try {
      const text = await FileSystem.readAsStringAsync(res.assets[0].uri);
      const rows = importJournalCsv(text);
      if (!rows.length) throw new Error('No graded bets found in that CSV');
      await db.addBets(rows);
      await refresh();
      Alert.alert('Imported', `${rows.length} graded bets added to your journal.`);
    } catch (e) {
      Alert.alert('Import failed', e instanceof Error ? e.message : String(e));
    }
  };

  const addBet = async (won: boolean) => {
    const o = parseInt(odds, 10), c = parseInt(close, 10);
    if (Number.isNaN(o) || Number.isNaN(c)) { Alert.alert('Check the odds fields'); return; }
    await db.addBets([{
      market: market.toLowerCase(), odds: o, mins: parseInt(mins, 10) || 180,
      stake: Number(stake) || 25, close: [c, c < 0 ? -c : 100], won,
    }]);
    await refresh();
  };

  const logEstimate = async () => {
    const o = parseInt(odds, 10);
    if (Number.isNaN(o)) { Alert.alert('Enter the odds first'); return; }
    const marketPrice = implied(o);
    const stated = yourPct.trim() === '' ? marketPrice : Number(yourPct) / 100;
    await db.addEstimate({ marketPrice, statedProb: stated, odds: o });
    setYourPct('');
    await refresh();
    Alert.alert('Sealed', 'Your number is logged with a timestamp. It cannot be edited after the game — that is the point.');
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }}>
      <Screen>
        <BrandHeader />
        <H1>Log</H1>
        <Text style={{ color: colors.textMuted }}>{bets.length} bets in your journal. Everything stays on this phone.</Text>

        <Label>Import a journal (CSV)</Label>
        <Btn title="Import CSV (Pikkit-style export)" onPress={importCsv} accent />
        <View style={{ flexDirection: 'row', gap: space.sm }}>
          <View style={{ flex: 1 }}><Btn title="Load demo journal" onPress={loadDemo} /></View>
          <View style={{ flex: 1 }}><Btn title="Clear journal" onPress={wipe} /></View>
        </View>

        <Label>Add a bet</Label>
        <Card>
          <TextInput style={input} value={market} onChangeText={setMarket} placeholder="market: spread / total / moneyline / prop / parlay" placeholderTextColor={colors.textFaint} />
          <TextInput style={input} value={odds} onChangeText={setOdds} keyboardType="numbers-and-punctuation" placeholder="odds taken (American)" placeholderTextColor={colors.textFaint} />
          <TextInput style={input} value={close} onChangeText={setClose} keyboardType="numbers-and-punctuation" placeholder="closing odds (your side)" placeholderTextColor={colors.textFaint} />
          <TextInput style={input} value={stake} onChangeText={setStake} keyboardType="decimal-pad" placeholder="stake" placeholderTextColor={colors.textFaint} />
          <TextInput style={input} value={mins} onChangeText={setMins} keyboardType="number-pad" placeholder="minutes before start" placeholderTextColor={colors.textFaint} />
          <View style={{ flexDirection: 'row', gap: space.sm }}>
            <View style={{ flex: 1 }}><Btn title="Won" onPress={() => addBet(true)} accent /></View>
            <View style={{ flex: 1 }}><Btn title="Lost" onPress={() => addBet(false)} /></View>
          </View>
        </Card>

        <Label>Your number (sealed estimate)</Label>
        <Card>
          <Text style={{ color: colors.textMuted }}>
            Before the game: what do YOU think the chance is? Leave it blank to
            take the market price ({odds ? `${(implied(parseInt(odds, 10) || -110) * 100).toFixed(0)}%` : '—'}).
            One tap, no editing later. This is what de-bias (Pro) learns from.
          </Text>
          <TextInput style={input} value={yourPct} onChangeText={setYourPct} keyboardType="decimal-pad" placeholder="your % (blank = market price)" placeholderTextColor={colors.textFaint} />
          <Btn title="Seal my number" onPress={logEstimate} accent />
        </Card>
      </Screen>
    </ScrollView>
  );
}
