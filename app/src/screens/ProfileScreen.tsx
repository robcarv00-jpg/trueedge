import React from 'react';
import { ScrollView, Text, View } from 'react-native';
import { useApp } from '../state';
import { Screen, H1, Label, Card, Mono, TierChip, AxisBar , BrandHeader} from '../ui';
import { priceCalibration } from '../core/mirror';
import { colors, type } from '../theme';

const pct = (x: number, dp = 0) => `${(x * 100).toFixed(dp)}%`;
const spct = (x: number, dp = 1) => `${x >= 0 ? '+' : ''}${(x * 100).toFixed(dp)}%`;

/** FREE tier — "who you are": profile, axes, price calibration.
 *  The identity report is never paywalled (LAUNCH_PLAN gate design). */
export default function ProfileScreen() {
  const { report: m, axes, bets, usingDemo } = useApp();
  if (!m || !axes) return <Screen><Text style={{ color: colors.text }}>No bets yet.</Text></Screen>;
  const cal = priceCalibration(bets);
  const demoted = (m.parlay_resolve_in ?? 0) > 500;
  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }}>
      <Screen>
        <BrandHeader />
        <H1>Your profile</H1>
        <Text style={{ color: colors.textMuted }}>
          {m.bets} bets{usingDemo ? ' · demo journal (import yours in Log)' : ''} — this is
          what the books see when they look at you.
        </Text>

        <Card>
          <AxisBar label="Skill — do you find edge" value={axes.skill} color={colors.accentBlue} />
          <AxisBar label="Discipline — do you keep it" value={axes.discipline} color={colors.accent} />
        </Card>

        <Card>
          <Label>Closing line value</Label>
          <Mono size={28}>{m.avg_clv_pct >= 0 ? '+' : ''}{m.avg_clv_pct.toFixed(2)}%</Mono>
          <Text style={{ color: colors.textMuted, marginTop: 4 }}>
            Beat the close {pct(m.beat_close_rate)} of graded bets
            (95% CI {pct(m.beat_close_ci[0])}–{pct(m.beat_close_ci[1])}) ·
            Brier {m.brier.toFixed(3)} · price-cal gap {(m.price_cal_gap * 100).toFixed(1)} pts
          </Text>
        </Card>

        <Label>Leaks</Label>
        <Card>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={{ color: colors.text, fontSize: type.body }}>Parlays</Text>
            <TierChip tier={m.parlay_tier} />
          </View>
          <Mono>{spct(m.parlay_roi)} ROI · n={m.parlay_n}</Mono>
          <Text style={{ color: colors.textMuted }}>
            {demoted
              ? `${m.parlay_units100 >= 0 ? '+' : ''}${m.parlay_units100.toFixed(1)} units per 100 bets — unresolvable at your volume; that is a reason to cut it, not ignore it.`
              : `95% CI ${spct(m.parlay_roi_ci[0])} to ${spct(m.parlay_roi_ci[1])}${m.parlay_resolve_in ? ` — clear answer in ~${m.parlay_resolve_in} more bets` : ''}`}
          </Text>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 }}>
            <Text style={{ color: colors.text, fontSize: type.body }}>Late bets (≤15 min)</Text>
            <TierChip tier={m.late_tier} />
          </View>
          <Mono>{spct(m.late_roi)} ROI · n={m.late_n}</Mono>
          <Text style={{ color: colors.textMuted }}>
            Early spread/total bets: {spct(m.early_main_roi)} ROI
          </Text>
          <Text style={{ color: colors.text, marginTop: 12 }}>
            Tilt: {m.tilt_events} stake-escalations after a loss ({m.tilt_per_100.toFixed(0)} per 100 bets)
          </Text>
        </Card>

        <Label>Price calibration</Label>
        <Card>
          <Text style={{ color: colors.textMuted, marginBottom: 8 }}>
            Your results vs the price you took. CIs are individual 95%, not family-wise.
          </Text>
          {cal.map((b) => (
            <View key={b.range} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 3 }}>
              <Mono size={14}>{b.range}</Mono>
              <Mono size={14}>n={b.n} said {pct(b.implied)} hit {pct(b.actual)}</Mono>
              <TierChip tier={b.tier} />
            </View>
          ))}
        </Card>
        <Text style={{ color: colors.textFaint, fontSize: type.caption, marginTop: 8 }}>
          TrueEdge does not offer wagering. It grades yours.
        </Text>
      </Screen>
    </ScrollView>
  );
}
