import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import authService from '../services/auth.service';
import notificationService from '../services/notification.service';
import apiClient from '../api/client';


interface ProfileScreenProps {
  onLogout: () => void;
}

export default function ProfileScreen({ onLogout }: ProfileScreenProps) {
  const [user, setUser] = useState<any>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [highUsageAlerts, setHighUsageAlerts] = useState(true);
  const [dailySummary, setDailySummary] = useState(true);
  

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          await authService.logout();
          onLogout();
        },
      },
    ]);
  };

  const handleNotificationToggle = async (value: boolean) => {
    setNotificationsEnabled(value);
    if (value) {
      const granted = await notificationService.requestPermissions();
      if (granted) {
        Alert.alert('Success', 'Notifications enabled');
      } else {
        setNotificationsEnabled(false);
        Alert.alert('Error', 'Please enable notifications in settings');
      }
    }
  };

  const handleExportPDF = async () => {
    Alert.alert('Export', 'PDF export feature coming soon!');
    // In production, call: await apiClient.exportBillPDF();
  };

  const handleExportCSV = async () => {
    Alert.alert('Export', 'CSV export feature coming soon!');
    // In production, call: await apiClient.exportUsageCSV();
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={40} color="#fff" />
          </View>
          <Text style={styles.userName}>{user?.full_name || 'User'}</Text>
          <Text style={styles.userEmail}>{user?.email || ''}</Text>
        </View>
      </LinearGradient>

      {/* Settings Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚙️ Settings</Text>

        <View style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="notifications" size={24} color="#667eea" />
            <Text style={styles.settingText}>Push Notifications</Text>
          </View>
          <Switch
            value={notificationsEnabled}
            onValueChange={handleNotificationToggle}
            trackColor={{ false: '#ccc', true: '#667eea' }}
          />
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="warning" size={24} color="#e74c3c" />
            <Text style={styles.settingText}>High Usage Alerts</Text>
          </View>
          <Switch
            value={highUsageAlerts}
            onValueChange={setHighUsageAlerts}
            trackColor={{ false: '#ccc', true: '#667eea' }}
            disabled={!notificationsEnabled}
          />
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="calendar" size={24} color="#27ae60" />
            <Text style={styles.settingText}>Daily Summary</Text>
          </View>
          <Switch
            value={dailySummary}
            onValueChange={setDailySummary}
            trackColor={{ false: '#ccc', true: '#667eea' }}
            disabled={!notificationsEnabled}
          />
        </View>

        <View style={styles.settingItem}>
          <View style={styles.settingLeft}>
            <Ionicons name="moon" size={24} color="#34495e" />
            <Text style={styles.settingText}>Dark Mode</Text>
          </View>
          <Switch
            value={darkMode}
            onValueChange={setDarkMode}
            trackColor={{ false: '#ccc', true: '#667eea' }}
          />
        </View>
      </View>

      {/* Export Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📄 Export Reports</Text>

        <TouchableOpacity style={styles.button} onPress={handleExportPDF}>
          <Ionicons name="document-text" size={24} color="#fff" />
          <Text style={styles.buttonText}>Export as PDF</Text>
          <Ionicons name="download" size={20} color="#fff" />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, { backgroundColor: '#27ae60' }]}
          onPress={handleExportCSV}>
          <Ionicons name="grid" size={24} color="#fff" />
          <Text style={styles.buttonText}>Export as CSV</Text>
          <Ionicons name="download" size={20} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* About Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ℹ️ About</Text>

        <TouchableOpacity style={styles.infoItem}>
          <Text style={styles.infoLabel}>Version</Text>
          <Text style={styles.infoValue}>1.0.0</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.infoItem}>
          <Text style={styles.infoLabel}>App ID</Text>
          <Text style={styles.infoValue}>{user?.id || 'N/A'}</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.infoItem}>
          <Text style={styles.infoLabel}>API Status</Text>
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Connected</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out" size={24} color="#e74c3c" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      <View style={{ height: 30 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingBottom: 30,
  },
  profileHeader: {
    alignItems: 'center',
    paddingTop: 60,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.8,
    marginTop: 5,
  },
  section: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 15,
  },
  settingText: {
    fontSize: 16,
    color: '#333',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#667eea',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    gap: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  infoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#27ae60',
  },
  statusText: {
    fontSize: 14,
    color: '#27ae60',
    fontWeight: '600',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    margin: 15,
    padding: 15,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#e74c3c',
    gap: 10,
  },
  logoutText: {
    color: '#e74c3c',
    fontSize: 16,
    fontWeight: 'bold',
  },
});