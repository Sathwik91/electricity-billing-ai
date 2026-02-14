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
import { LineChart, BarChart } from 'react-native-chart-kit';
import apiClient from '../api/client';
import { UsageData } from '../types';

const { width } = Dimensions.get('window');

export default function UsageScreen() {
  const [usageData, setUsageData] = useState<UsageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [days] = useState(7);

  const fetchData = async () => {
    try {
      setError('');
      const data = await apiClient.getUsageHistory(days);
      
      // Validate data
      if (Array.isArray(data) && data.length > 0) {
        setUsageData(data.reverse());
      } else {
        setUsageData([]);
        setError('No usage data available');
      }
    } catch (error: any) {
      console.error('Error fetching usage data:', error);
      setError(error.message || 'Failed to load usage data');
      setUsageData([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [days]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
        <Text style={styles.loadingText}>Loading usage data...</Text>
      </View>
    );
  }

  if (error || usageData.length === 0) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.loadingContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        <Text style={styles.errorText}>
          {error || '📊 No usage data available'}
        </Text>
        <Text style={styles.errorSubtext}>Pull down to retry</Text>
      </ScrollView>
    );
  }

  // Safe calculations with default values
  const totalConsumption = usageData.reduce(
    (sum, d) => sum + (d.consumption_kwh || 0),
    0
  );
  const avgConsumption = usageData.length > 0 ? totalConsumption / usageData.length : 0;
  const consumptionValues = usageData.map((d) => d.consumption_kwh || 0);
  const maxConsumption = consumptionValues.length > 0 ? Math.max(...consumptionValues) : 0;
  const minConsumption = consumptionValues.length > 0 ? Math.min(...consumptionValues) : 0;

  // Prepare chart data with safe defaults
  const chartData = {
    labels: usageData.map((d) => {
      try {
        const date = new Date(d.date);
        return `${date.getDate()}/${date.getMonth() + 1}`;
      } catch {
        return '';
      }
    }),
    datasets: [
      {
        data: consumptionValues.length > 0 ? consumptionValues : [0],
        color: (opacity = 1) => `rgba(102, 126, 234, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }>
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <Text style={styles.headerTitle}>📊 Usage Analytics</Text>
        <Text style={styles.headerSubtitle}>Last {days} Days</Text>
      </LinearGradient>

      {/* Stats Summary */}
      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{totalConsumption.toFixed(1)}</Text>
          <Text style={styles.statLabel}>Total kWh</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{avgConsumption.toFixed(1)}</Text>
          <Text style={styles.statLabel}>Avg/Day</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{maxConsumption.toFixed(1)}</Text>
          <Text style={styles.statLabel}>Peak</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{minConsumption.toFixed(1)}</Text>
          <Text style={styles.statLabel}>Lowest</Text>
        </View>
      </View>

      {/* Line Chart */}
      <View style={styles.card}>
        <Text style={styles.chartTitle}>Daily Consumption Trend</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <LineChart
            data={chartData}
            width={Math.max(width - 40, usageData.length * 60)}
            height={220}
            chartConfig={{
              backgroundColor: '#fff',
              backgroundGradientFrom: '#fff',
              backgroundGradientTo: '#fff',
              decimalPlaces: 1,
              color: (opacity = 1) => `rgba(102, 126, 234, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '4',
                strokeWidth: '2',
                stroke: '#667eea',
              },
            }}
            bezier
            style={styles.chart}
          />
        </ScrollView>
      </View>

      {/* Bar Chart */}
      <View style={styles.card}>
        <Text style={styles.chartTitle}>Daily Comparison</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <BarChart
            data={chartData}
            width={Math.max(width - 40, usageData.length * 60)}
            height={220}
            chartConfig={{
              backgroundColor: '#fff',
              backgroundGradientFrom: '#fff',
              backgroundGradientTo: '#fff',
              decimalPlaces: 1,
              color: (opacity = 1) => `rgba(67, 233, 123, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
            }}
            style={styles.chart}
            showValuesOnTopOfBars
          />
        </ScrollView>
      </View>

      {/* Usage List */}
      <View style={styles.card}>
        <Text style={styles.chartTitle}>Detailed Usage</Text>
        {usageData.map((item, index) => {
          const consumption = item.consumption_kwh || 0;
          const barWidth = maxConsumption > 0 ? (consumption / maxConsumption) * 100 : 0;
          
          return (
            <View key={index} style={styles.usageItem}>
              <View style={styles.usageLeft}>
                <Text style={styles.usageDate}>
                  {new Date(item.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </Text>
                <Text style={styles.usageDay}>
                  {new Date(item.date).toLocaleDateString('en-US', {
                    weekday: 'short',
                  })}
                </Text>
              </View>
              <View style={styles.usageRight}>
                <Text style={styles.usageValue}>
                  {consumption.toFixed(2)} kWh
                </Text>
                <View
                  style={[
                    styles.usageBar,
                    {
                      width: `${barWidth}%`,
                    },
                  ]}
                />
              </View>
            </View>
          );
        })}
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
    paddingHorizontal: 20,
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
  statsContainer: {
    flexDirection: 'row',
    padding: 15,
    gap: 10,
  },
  statBox: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#667eea',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
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
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  usageItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  usageLeft: {
    width: 80,
  },
  usageDate: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  usageDay: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  usageRight: {
    flex: 1,
    marginLeft: 15,
  },
  usageValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#667eea',
    marginBottom: 5,
  },
  usageBar: {
    height: 6,
    backgroundColor: '#667eea',
    borderRadius: 3,
  },
});