import React, { useState } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import apiClient from '../api/client';

export default function TestScreen() {
  const [result, setResult] = useState('Not tested');

  const testConnection = async () => {
    try {
      setResult('Testing...');
      const response = await apiClient.login('demo1@example.com', 'Demo123!@#');
      setResult('✅ Connected! Token received');
    } catch (error: any) {
      setResult(`❌ Error: ${error.message}`);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Backend Connection Test</Text>
      <Text style={styles.result}>{result}</Text>
      <Button title="Test Login" onPress={testConnection} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  result: { fontSize: 16, marginBottom: 20, padding: 10, backgroundColor: '#f0f0f0' },
});