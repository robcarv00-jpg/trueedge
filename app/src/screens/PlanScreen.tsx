import React from 'react';
import { ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { useApp, Tier } from '../state';
import { Screen, H1, Label, Card, Mono , BrandHeader} from '../ui';
import { colors, MIN_TOUCH, radius, type } from '../theme';

const TIERS: { id: Tier; name: string; price: string; lines: string[] }[] = [
  {
    id: 'free', name: 'Free', price: '$0',
    lines: ['CSV import', 'Your Mirror profile', 'Skill / Discipline score', 'Price calibration'],
  },
  {
    id: 'plus', name: 'Plus', price: '$4.99/mo · $34.99/yr',
    lines: ['Unlimited history', 'Trend lines', 'Live-leak tracking'],
  },
  {
    id: 'pro', name: 'Pro', price: '$14.99/mo · $89.99/yr',
    lines: ['De-bias on your sealed numbers', 'Attribution (at volume)', 'Base-rate grading', 'Report sealing — verification free for anyone, forever'],
  },
];

/** The gate: Free = who you are. Paid = where you're improving.
 *  Plus shows the Pro countdown (the waiting-room rule, LAUNCH_PLAN). */
export default function PlanScreen() {
  const { tier, setTier, estimateCount } = useApp();
  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }}>
      <Screen>
        <BrandHeader />
        <H1>Plan</H1>
        <Text style={{ color: colors.textMuted }}>
          Free shows you who you are. Paid shows you where you're improving.
        </Text>
        {tier === 'plus' && (
          <Card>
            <Text style={{ color: colors.accent }}>
              Your Pro tools activate as you log — de-bias sharpens at 30 sealed
              estimates. You have {estimateCount}.
            </Text>
            <View style={{ height: 6, backgroundColor: colors.border, borderRadius: 3, marginTop: 8 }}>
              <View style={{
                height: 6, backgroundColor: colors.accent, borderRadius: 3,
                width: `${Math.min(100, (estimateCount / 30) * 100)}%`,
              }} />
            </View>
          </Card>
        )}
        {TIERS.map((t) => (
          <Card key={t.id}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <Text style={{ color: colors.text, fontSize: type.title3, fontWeight: '600' }}>{t.name}</Text>
              <Mono size={15}>{t.price}</Mono>
            </View>
            {t.lines.map((l) => (
              <Text key={l} style={{ color: colors.textMuted, marginTop: 4 }}>· {l}</Text>
            ))}
            <TouchableOpacity
              onPress={() => setTier(t.id)}
              disabled={tier === t.id}
              style={{
                minHeight: MIN_TOUCH, justifyContent: 'center', alignItems: 'center',
                borderRadius: radius.chip, marginTop: 10,
                backgroundColor: tier === t.id ? colors.border : colors.accentDeep,
              }}>
              <Text style={{
                color: tier === t.id ? colors.textMuted : colors.onAccent, fontWeight: '700',
              }}>
                {tier === t.id ? 'Current plan' : `Preview ${t.name} (billing at launch)`}
              </Text>
            </TouchableOpacity>
          </Card>
        ))}
        <Label>The fine print, in plain sight</Label>
        <Text style={{ color: colors.textMuted }}>
          Verification is free forever because a seal that only paying parties
          can check isn't a seal. Your betting history never leaves this phone.
          TrueEdge does not offer wagering of any kind.
        </Text>
      </Screen>
    </ScrollView>
  );
}
