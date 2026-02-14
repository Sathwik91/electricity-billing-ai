import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// Check if running in Expo Go
const isExpoGo = Constants.appOwnership === 'expo';

// Configure how notifications are displayed
if (!isExpoGo) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });
}

class NotificationService {
  async requestPermissions() {
    if (isExpoGo) {
      console.log('Notifications not available in Expo Go');
      return false;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Failed to get push notification permissions');
      return false;
    }

    return true;
  }

  async getExpoPushToken() {
    if (isExpoGo) {
      return null;
    }

    try {
      const token = (await Notifications.getExpoPushTokenAsync()).data;
      await AsyncStorage.setItem('expo_push_token', token);
      return token;
    } catch (error) {
      console.error('Error getting push token:', error);
      return null;
    }
  }

  async scheduleHighConsumptionAlert(consumption: number, threshold: number) {
    if (isExpoGo) {
      console.log('Notifications not available in Expo Go');
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '⚠️ High Consumption Alert',
        body: `Your usage (${consumption.toFixed(1)} kWh) exceeded threshold of ${threshold} kWh!`,
        data: { type: 'high_consumption', consumption },
        sound: true,
      },
      trigger: null,
    });
  }

  async scheduleBillPredictionAlert(predictedAmount: number, daysLeft: number) {
    if (isExpoGo) {
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '💰 Bill Prediction Update',
        body: `Predicted bill: ₹${predictedAmount.toFixed(0)} (${daysLeft} days left)`,
        data: { type: 'bill_prediction', amount: predictedAmount },
      },
      trigger: null,
    });
  }

  async scheduleRecommendationAlert(title: string, savings: number) {
    if (isExpoGo) {
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '💡 New Energy Saving Tip',
        body: `${title} - Save ₹${savings.toFixed(0)}/month`,
        data: { type: 'recommendation' },
      },
      trigger: null,
    });
  }

  async scheduleDailyReminder() {
    if (isExpoGo) {
      return;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title: '📊 Daily Usage Update',
        body: 'Check your electricity consumption for today',
        data: { type: 'daily_reminder' },
      },
      trigger: {
        hour: 20,
        minute: 0,
        repeats: true,
      },
    });
  }

  async cancelAllNotifications() {
    if (isExpoGo) {
      return;
    }

    await Notifications.cancelAllScheduledNotificationsAsync();
  }
}

export default new NotificationService();