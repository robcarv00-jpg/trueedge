import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { colors, display, type, radius, space } from './theme';

export function Screen({ children }: { children: React.ReactNode }) {
  return <View style={styles.screen}>{children}</View>;
}

/** Brand header: the simplified icon + wordmark + blue swoosh.
 *  Every screen opens with the master look (Robert's direction). */
export function BrandHeader() {
  return (
    <View style={styles.brand}>
      <Image source={require('../assets/icon.png')} style={styles.brandIcon} />
      <Text style={styles.wordmark}>
        TRUE <Text style={{ color: colors.accent }}>EDGE</Text>
      </Text>
      <View style={styles.swoosh} />
    </View>
  );
}

export function H1({ children }: { children: React.ReactNode }) {
  return <Text style={styles.h1}>{children}</Text>;
}

export function Label({ children }: { children: React.ReactNode }) {
  return <Text style={styles.label}>{children}</Text>;
}

export function Card({ children }: { children: React.ReactNode }) {
  return <View style={styles.card}>{children}</View>;
}

export function Mono({ children, size = 16, color = colors.text }: {
  children: React.ReactNode; size?: number; color?: string;
}) {
  return <Text style={{ fontFamily: 'monospace', fontSize: size, color }}>{children}</Text>;
}

export function TierChip({ tier }: { tier: string }) {
  const c = tier === 'signal' ? colors.danger : tier === 'noise' ? colors.textMuted : colors.accent;
  return (
    <View style={[styles.chip, { borderColor: c }]}>
      <Text style={{ color: c, fontSize: 12 }}>{tier.toUpperCase()}</Text>
    </View>
  );
}

export function AxisBar({ label, value, color = colors.accent }: {
  label: string; value: number; color?: string;
}) {
  return (
    <View style={{ marginVertical: space.sm }}>
      <View style={styles.axisRow}>
        <Text style={styles.axisLabel}>{label}</Text>
        <Mono size={20}>{value}</Mono>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${value}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg, padding: space.md },
  brand: { marginBottom: space.sm },
  brandIcon: { width: 44, height: 44, borderRadius: 10 },
  wordmark: {
    color: colors.text, fontSize: 22, marginTop: 6,
    fontWeight: display.fontWeight, fontStyle: display.fontStyle,
    letterSpacing: display.letterSpacing,
  },
  swoosh: {
    height: 3, backgroundColor: colors.accentBlue, borderRadius: 2,
    marginTop: 8, width: '62%',
  },
  h1: {
    color: colors.text, fontSize: type.title2, marginBottom: space.sm,
    fontWeight: display.fontWeight, fontStyle: display.fontStyle,
    letterSpacing: display.letterSpacing,
  },
  label: {
    color: colors.textMuted, fontSize: type.caption,
    textTransform: 'uppercase', letterSpacing: 1, marginTop: space.md, marginBottom: space.xs,
  },
  card: {
    backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1,
    borderRadius: radius.card, padding: space.md, marginVertical: space.sm,
  },
  chip: {
    borderWidth: 1, borderRadius: radius.chip, paddingHorizontal: 8,
    paddingVertical: 2, alignSelf: 'flex-start',
  },
  axisRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  axisLabel: { color: colors.text, fontSize: type.body },
  track: { height: 6, backgroundColor: colors.border, borderRadius: 3, marginTop: 6 },
  fill: { height: 6, backgroundColor: colors.accent, borderRadius: 3 },
});
