import { Text, View } from 'react-native';

export default function LoginScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 24 }}>
      <Text style={{ fontSize: 20, fontWeight: '600' }}>Caravan HR</Text>
      <Text style={{ marginTop: 8, color: '#475569' }}>
        Мобильный shell готов для этапа 6. Основной MVP этапов 0-1 находится в API.
      </Text>
    </View>
  );
}
