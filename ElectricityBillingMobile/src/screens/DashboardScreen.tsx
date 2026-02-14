import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import apiClient from '../api/client';
import { Prediction, UsageStats } from '../types';

const { width } = Dimensions.get('window');

export default function DashboardScreen() {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      setError('');
      const [predData, statsData] = await Promise.all([
        apiClient.getCurrentMonthPrediction(),
        apiClient.getUsageStats(),
      ]);
      setPrediction(predData);
      setStats(statsData);
    } catch (error: any) {
      console.error('Error fetching data:', error);
      setError(error.message || 'Failed to load data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.errorText}>❌ {error}</Text>
        <Text style={styles.errorSubtext}>Pull down to retry</Text>
      </View>
    );
  }

  // Safe helper functions
  const getBillAmount = () => prediction?.predicted_bill_amount?.toFixed(2) || '0.00';
  const getCurrentConsumption = () => prediction?.current_consumption_kwh?.toFixed(1) || '0.0';
  const getDaysRemaining = () => prediction?.days_remaining || 0;
  const getConfidence = () => ((prediction?.confidence_score || 0) * 100).toFixed(0);
  const getAvgDaily = () => stats?.average_daily?.toFixed(1) || '0.0';
  const getPercentageChange = () => prediction?.percentage_change || 0;
  const getPreviousBill = () => prediction?.previous_month_bill?.toFixed(0) || '0';
  const getTotalConsumption = () => stats?.total_consumption?.toFixed(1) || '0.0';
  const getPeakConsumption = () => stats?.peak_consumption?.toFixed(1) || '0.0';

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      {/* Header */}
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <Text style={styles.headerTitle}>Dashboard</Text>
        <Text style={styles.headerSubtitle}>AI-Powered Bill Prediction</Text>
      </LinearGradient>

      {/* Predicted Bill Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>💰 Predicted Monthly Bill</Text>
          {prediction?.prediction_method && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>
                {prediction.prediction_method.includes('LSTM') ? '🤖 AI' : '📊'}
              </Text>
            </View>
          )}
        </View>
        <Text style={styles.bigAmount}>₹{getBillAmount()}</Text>
        <View style={styles.changeContainer}>
          <Text
            style={[
              styles.changeText,
              {
                color: getPercentageChange() > 0 ? '#e74c3c' : '#27ae60',
              },
            ]}>
            {getPercentageChange() > 0 ? '↑' : '↓'}{' '}
            {Math.abs(getPercentageChange()).toFixed(1)}% vs last month
          </Text>
        </View>
        <Text style={styles.methodText}>
          Method: {prediction?.prediction_method || 'Simple Average'}
        </Text>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <View style={[styles.statCard, { backgroundColor: '#667eea' }]}>
          <Text style={styles.statValue}>{getCurrentConsumption()}</Text>
          <Text style={styles.statLabel}>Current kWh</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: '#f093fb' }]}>
          <Text style={styles.statValue}>{getDaysRemaining()}</Text>
          <Text style={styles.statLabel}>Days Left</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: '#4facfe' }]}>
          <Text style={styles.statValue}>{getConfidence()}%</Text>
          <Text style={styles.statLabel}>Confidence</Text>
        </View>

        <View style={[styles.statCard, { backgroundColor: '#43e97b' }]}>
          <Text style={styles.statValue}>{getAvgDaily()}</Text>
          <Text style={styles.statLabel}>Avg Daily</Text>
        </View>
      </View>

      {/* Previous Month Comparison */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📊 Month Comparison</Text>
        <View style={styles.comparisonRow}>
          <View style={styles.comparisonItem}>
            <Text style={styles.comparisonLabel}>This Month</Text>
            <Text style={styles.comparisonValue}>₹{getBillAmount()}</Text>
          </View>
          <View style={styles.comparisonDivider} />
          <View style={styles.comparisonItem}>
            <Text style={styles.comparisonLabel}>Last Month</Text>
            <Text style={styles.comparisonValue}>₹{getPreviousBill()}</Text>
          </View>
        </View>
      </View>

      {/* Total Consumption */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>⚡ Total Statistics</Text>
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statItemValue}>{getTotalConsumption()}</Text>
            <Text style={styles.statItemLabel}>Total kWh</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statItemValue}>{getPeakConsumption()}</Text>
            <Text style={styles.statItemLabel}>Peak kWh</Text>
          </View>
        </View>
      </View>

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
  errorText: {
    fontSize: 18,
    color: '#e74c3c',
    textAlign: 'center',
    marginBottom: 10,
  },
  errorSubtext: {
    fontSize: 14,
    color: '#999',
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
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  badge: {
    backgroundColor: '#667eea',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  bigAmount: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#667eea',
  },
  changeContainer: {
    marginTop: 5,
  },
  changeText: {
    fontSize: 16,
    fontWeight: '600',
  },
  methodText: {
    marginTop: 10,
    fontSize: 12,
    color: '#999',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 15,
    gap: 15,
  },
  statCard: {
    width: (width - 60) / 2,
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 14,
    color: '#fff',
    marginTop: 5,
    opacity: 0.9,
  },
  comparisonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 15,
  },
  comparisonItem: {
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  comparisonValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  comparisonDivider: {
    width: 1,
    backgroundColor: '#ddd',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 15,
  },
  statItem: {
    alignItems: 'center',
  },
  statItemValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#667eea',
  },
  statItemLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
});