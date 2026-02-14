import AsyncStorage from '@react-native-async-storage/async-storage';
import apiClient from '../api/client';

class AuthService {
  async login(email: string, password: string) {
    const response = await apiClient.login(email, password);
    await AsyncStorage.setItem('access_token', response.access_token);
    return response;
  }

  async logout() {
    await AsyncStorage.removeItem('access_token');
  }

  async isAuthenticated() {
    const token = await AsyncStorage.getItem('access_token');
    return !!token;
  }
}

export default new AuthService();