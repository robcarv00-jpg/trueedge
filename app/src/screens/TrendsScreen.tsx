import React from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useApp } from '../state';
import { Screen, H1, Label, Card, Mono , BrandHeader} from '../ui';
import { colors } from '../theme';

/** PLUS tier — "where you're improving": rolling 40-bet windows.
 *  Free sees the first window (the baseline); the line is Plus. */
export default function TrendsScreen() {
  const { trend, tier } = useApp();
  const locked = tier === 'free';
  const shown = locked ? trend.slice(0, 1) : trend;
  const first = trend[0], last = trend[trend.length - 1];
  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }}>
      <Screen>
        <BrandHeader />
        <H1>Trend</H1>
        <Text style={{ color: colors.textMuted }}>
          40-bet rolling windows. Week 1 this is a baseline, not a verdict — the line is the product.
        </Text>
        {trend.length >= 2 && last && first && (
          <Card>
            <Mono size={18}>
              Skill {first.skill} → {last.skill} · Discipline {first.discipline} → {last.discipline}
            </Mono>
            <Text style={{ color: colors.textMuted }}>
              Tilt {first.tilt_per_100.toFixed(0)} → {last.tilt_per_100.toFixed(0)} per 100 bets ·
              CLV {first.avg_clv_pct >= 0 ? '+' : ''}{first.avg_clv_pct.toFixed(2)}% → {last.avg_clv_pct >= 0 ? '+' : ''}{last.avg_clv_pct.toFixed(2)}%
            </Text>
          </Card>
        )}
        <Label>Windows</Label>
        {shown.map((t) => (
          <Card key={t.through_bet}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Mono>through bet {t.through_bet}</Mono>
              <Mono>Skill {t.skill} · Disc {t.discipline}</Mono>
            </View>
          </Card>
        ))}
        {locked && trend.length > 1 && (
          <Card>
            <Text style={{ color: colors.accent }}>
              Plus unlocks the full line — {trend.length - 1} more windows, and live-leak
              tracking as you log. Your past is free. Your trajectory is Plus.
            </Text>
          </Card>
        )}
      </Screen>
    </ScrollView>
  );
}
