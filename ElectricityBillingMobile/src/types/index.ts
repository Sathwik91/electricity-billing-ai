export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface Prediction {
  predicted_bill_amount: number;
  current_consumption_kwh: number;
  predicted_remaining_kwh: number;
  previous_month_bill: number;
  percentage_change: number;
  confidence_score: number;
  days_remaining: number;
  days_elapsed: number;
  prediction_method: string;
}

export interface UsageData {
  date: string;
  consumption_kwh: number;
}

export interface UsageStats {
  total_consumption: number;
  average_daily: number;
  peak_consumption: number;
}

export interface Recommendation {
  id: number;
  title: string;
  description: string;
  estimated_savings_kwh: number;
  estimated_savings_amount: number;
  effort_level: 'easy' | 'moderate' | 'hard';
  action_steps: string[];
}