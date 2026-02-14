import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';

// ⚠️ IMPORTANT: Replace with YOUR computer's IP address
// Run: ipconfig | Select-String "IPv4" to find it
const API_BASE_URL = 'http://10.178.139.142:8000/api/v1'; // ← UPDATE THIS!

class APIClient {
  private client: AxiosInstance;
  private onUnauthorized?: () => void;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Handle response errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          await AsyncStorage.removeItem('access_token');
          
          // Call logout callback if set
          if (this.onUnauthorized) {
            this.onUnauthorized();
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setUnauthorizedCallback(callback: () => void) {
    this.onUnauthorized = callback;
  }

  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/users/me');
    return response.data;
  }

  async getCurrentMonthPrediction() {
    const response = await this.client.get('/predictions/current-month');
    return response.data;
  }

  async getUsageHistory(days: number = 7) {
    const response = await this.client.get(`/usage/history?days=${days}`);
    return response.data;
  }

  async getUsageStats() {
    const response = await this.client.get('/usage/stats');
    return response.data;
  }

  async getRecommendations() {
    const response = await this.client.get('/recommendations/active');
    return response.data;
  }

  async submitFeedback(recommendationId: number, data: any) {
    const response = await this.client.post('/recommendations/feedback', {
      recommendation_id: recommendationId,
      ...data,
    });
    return response.data;
  }
}

export default new APIClient();