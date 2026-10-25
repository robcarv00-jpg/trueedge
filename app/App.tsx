import React, { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { AppProvider, useApp } from './src/state';
import ProfileScreen from './src/screens/ProfileScreen';
import TrendsScreen from './src/screens/TrendsScreen';
import LogScreen from './src/screens/LogScreen';
import SealScreen from './src/screens/SealScreen';
import PlanScreen from './src/screens/PlanScreen';
import { colors, MIN_TOUCH } from './src/theme';

const TABS = [
  { id: 'profile', label: 'Profile' },
  { id: 'trends', label: 'Trend' },
  { id: 'log', label: 'Log' },
  { id: 'seal', label: 'Seal' },
  { id: 'plan', label: 'Plan' },
] as const;

type TabId = (typeof TABS)[number]['id'];

function Shell() {
  const { ready } = useApp();
  const [tab, setTab] = useState<TabId>('profile');
  if (!ready) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color={colors.accent} />
        <Text style={{ color: colors.textMuted, marginTop: 12 }}>Opening your journal…</Text>
      </View>
    );
  }
  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <View style={styles.body}>
        {tab === 'profile' && <ProfileScreen />}
        {tab === 'trends' && <TrendsScreen />}
        {tab === 'log' && <LogScreen />}
        {tab === 'seal' && <SealScreen />}
        {tab === 'plan' && <PlanScreen />}
      </View>
      <View style={styles.tabbar}>
        {TABS.map((t) => (
          <TouchableOpacity key={t.id} onPress={() => setTab(t.id)} style={styles.tab}>
            <Text style={{
              color: tab === t.id ? colors.accent : colors.textMuted,
              fontWeight: tab === t.id ? '700' : '400', fontSize: 14,
            }}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  body: { flex: 1 },
  loading: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  tabbar: {
    flexDirection: 'row', borderTopWidth: 1, borderTopColor: colors.border,
    backgroundColor: colors.bg, paddingBottom: 8,
  },
  tab: { flex: 1, minHeight: MIN_TOUCH, justifyContent: 'center', alignItems: 'center' },
});
