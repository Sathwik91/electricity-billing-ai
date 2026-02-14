import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import apiClient from '../api/client';
import { Recommendation } from '../types';

export default function RecommendationsScreen() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRecommendations = async () => {
    try {
      const data = await apiClient.getRecommendations();
      setRecommendations(data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchRecommendations();
  };

  const handleAccept = async (rec: Recommendation) => {
    try {
      await apiClient.submitFeedback(rec.id, {
        accepted: true,
        implemented: false,
        rating: 4,
        actual_savings_kwh: 0,
        estimated_savings_kwh: rec.estimated_savings_kwh,
        time_to_implement_days: 0,
      });
      Alert.alert('Success', 'Recommendation accepted! The AI will learn from your feedback.');
    } catch (error) {
      Alert.alert('Error', 'Failed to submit feedback');
    }
  };

  const handleDismiss = async (rec: Recommendation) => {
    try {
      await apiClient.submitFeedback(rec.id, {
        accepted: false,
        implemented: false,
        rating: 2,
        actual_savings_kwh: 0,
        estimated_savings_kwh: rec.estimated_savings_kwh,
        time_to_implement_days: 0,
      });
      Alert.alert('Noted', 'The AI will learn from your feedback.');
    } catch (error) {
      Alert.alert('Error', 'Failed to submit feedback');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={styles.loadingText}>Loading recommendations...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <Text style={styles.headerTitle}>💡 Recommendations</Text>
        <Text style={styles.headerSubtitle}>AI-Powered Energy Savings</Text>
      </LinearGradient>

      {recommendations.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>🤖 AI is analyzing your usage...</Text>
          <Text style={styles.emptySubtext}>Check back soon!</Text>
        </View>
      ) : (
        recommendations.map((rec) => (
          <View key={rec.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{rec.title}</Text>
              <View
                style={[
                  styles.effortBadge,
                  {
                    backgroundColor:
                      rec.effort_level === 'easy'
                        ? '#27ae60'
                        : rec.effort_level === 'moderate'
                        ? '#f39c12'
                        : '#e74c3c',
                  },
                ]}>
                <Text style={styles.effortText}>{rec.effort_level}</Text>
              </View>
            </View>

            <Text style={styles.description}>{rec.description}</Text>

            <View style={styles.savingsContainer}>
              <View style={styles.savingsItem}>
                <Text style={styles.savingsValue}>
                  ₹{rec.estimated_savings_amount.toFixed(0)}
                </Text>
                <Text style={styles.savingsLabel}>Savings/month</Text>
              </View>
              <View style={styles.savingsItem}>
                <Text style={styles.savingsValue}>
                  {rec.estimated_savings_kwh.toFixed(1)} kWh
                </Text>
                <Text style={styles.savingsLabel}>Energy saved</Text>
              </View>
            </View>

            <View style={styles.stepsContainer}>
              <Text style={styles.stepsTitle}>Action Steps:</Text>
              {rec.action_steps.map((step, index) => (
                <Text key={index} style={styles.step}>
                  • {step}
                </Text>
              ))}
            </View>

            <View style={styles.buttonContainer}>
              <TouchableOpacity
                style={[styles.button, styles.acceptButton]}
                onPress={() => handleAccept(rec)}>
                <Text style={styles.buttonText}>✓ Accept</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.dismissButton]}
                onPress={() => handleDismiss(rec)}>
                <Text style={styles.buttonText}>✗ Dismiss</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}

      <View style={{ height: 30 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  header: {
    padding: 30,
    paddingTop: 60,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.9,
    marginTop: 5,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 20,
    color: '#666',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#999',
  },
  card: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  effortBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  effortText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 15,
    lineHeight: 20,
  },
  savingsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
    padding: 15,
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
  },
  savingsItem: {
    alignItems: 'center',
  },
  savingsValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#27ae60',
  },
  savingsLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  stepsContainer: {
    marginBottom: 15,
  },
  stepsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  step: {
    fontSize: 13,
    color: '#666',
    marginBottom: 4,
    paddingLeft: 10,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  acceptButton: {
    backgroundColor: '#27ae60',
  },
  dismissButton: {
    backgroundColor: '#95a5a6',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});