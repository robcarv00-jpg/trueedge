import React, { useState } from 'react';
import { ScrollView, Text, TouchableOpacity, View } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { useApp } from '../state';
import { Screen, H1, Label, Card, Mono , BrandHeader} from '../ui';
import { sealMirrorReport, verifyScore } from '../core/mirror';
import { verifyReceipt, shareLink, ReceiptDict } from '../core/receipt';
import { colors, MIN_TOUCH, radius, type } from '../theme';

// Where the single-file verifier lives once hosted (LAUNCH_PLAN: the
// permalink page). Until then the link still works from any local copy
// of carver-receipt-verifier.html opened with the same fragment.
const VERIFIER_URL = 'https://robcarv00-jpg.github.io/trueedge/verifier.html';

/** PRO tier — seal the Mirror report as a Carver Receipt.
 *  Sealing is Pro; verification is free for anyone, forever, because a
 *  seal that only paying parties can check isn't a seal. */
export default function SealScreen() {
  const { bets, tier } = useApp();
  const [sealed, setSealed] = useState<ReceiptDict | null>(null);
  const [check, setCheck] = useState('');

  if (tier !== 'pro') {
    return (
      <Screen>
        <BrandHeader />
        <H1>Seal your report</H1>
        <Card>
          <Text style={{ color: colors.text, fontSize: type.body }}>
            Pro seals your Mirror report as a Carver Receipt — tamper-evident,
            rubric pinned inside the seal, checkable by anyone with the link.
          </Text>
          <Text style={{ color: colors.textMuted, marginTop: 8 }}>
            Verification stays free for anyone, forever. Only sealing is Pro.
            See Plan to preview Pro.
          </Text>
        </Card>
      </Screen>
    );
  }

  const seal = () => {
    const r = sealMirrorReport(bets, {
      key: 'demo', // v1 demo key; per-user key + Ed25519 is the launch hardening step
      created_at: new Date().toISOString().replace(/\.\d+Z$/, '+00:00'),
      evidenceSource: 'bet journal (on-device, TrueEdge)',
      retrievedAt: new Date().toISOString().slice(0, 10),
    });
    setSealed(r);
    const v = verifyReceipt(r, 'demo');
    const s = verifyScore(bets, r);
    setCheck(`Receipt: ${v.msg}\nScore pin: ${s.msg}`);
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: colors.bg }}>
      <Screen>
        <BrandHeader />
        <H1>Seal your report</H1>
        <TouchableOpacity
          onPress={seal}
          style={{
            minHeight: MIN_TOUCH, justifyContent: 'center', alignItems: 'center',
            backgroundColor: colors.accentDeep, borderRadius: radius.chip, marginVertical: 8,
          }}>
          <Text style={{ color: colors.onAccent, fontWeight: '700', fontSize: type.body }}>
            Seal this report
          </Text>
        </TouchableOpacity>
        {sealed && (
          <Card>
            <Label>Receipt</Label>
            <Mono size={13}>merkle {sealed.merkle_root.slice(0, 24)}…</Mono>
            <Mono size={13}>mode {sealed.mode} · score {(sealed.meta as { score: number }).score}/99 · rubric v1.1 pinned</Mono>
            <Text style={{ color: colors.success, marginTop: 8 }}>{check}</Text>
            {sealed.claims.map((c) => (
              <Text key={c.id} style={{ color: colors.textMuted, marginTop: 6, fontFamily: 'monospace', fontSize: 13 }}>
                [OK] {c.id} · {c.text}
              </Text>
            ))}
            <TouchableOpacity
              onPress={() => Clipboard.setStringAsync(shareLink(VERIFIER_URL, sealed))}
              style={{
                minHeight: MIN_TOUCH, justifyContent: 'center', alignItems: 'center',
                borderColor: colors.border, borderWidth: 1, borderRadius: radius.chip, marginTop: 12,
              }}>
              <Text style={{ color: colors.text }}>Copy share link (anyone can verify, free)</Text>
            </TouchableOpacity>
            <Text style={{ color: colors.textFaint, fontSize: type.caption, marginTop: 8 }}>
              The receipt rides in the link's fragment — it is never sent to a server.
            </Text>
          </Card>
        )}
      </Screen>
    </ScrollView>
  );
}
