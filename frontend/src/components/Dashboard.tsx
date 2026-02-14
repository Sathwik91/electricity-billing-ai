import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface DashboardProps {
  onLogout: () => void;
}

interface Prediction {
  predicted_bill_amount: number;
  predicted_consumption_kwh: number;
  confidence_score: number;
  days_remaining: number;
  percentage_change: number;
  current_consumption_kwh: number;
}

interface Recommendation {
  estimated_savings_kwh: any;
  source: string;
  id: number;
  title: string;
  description: string;
  estimated_savings_amount: number;
  effort_level: string;
  action_steps: string[];
}

interface UsageHistory {
  date: string;
  total_consumption_kwh: number;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const navigate = useNavigate();
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [usageHistory, setUsageHistory] = useState<UsageHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [feedbackModal, setFeedbackModal] = useState<{
    show: boolean;
    recommendation: any;
  }>({ show: false, recommendation: null });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // FIXED: Changed 'token' to 'access_token'
      const token = localStorage.getItem('access_token');
      
      console.log('Token found:', token ? 'Yes' : 'No');
      
      if (!token) {
        console.error('No token found, redirecting to login');
        navigate('/login');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch prediction
      console.log('Fetching predictions...');
      const predResponse = await fetch('http://localhost:8000/api/v1/predictions/current-month', { headers });
      console.log('Prediction response status:', predResponse.status);
      
      if (predResponse.status === 401) {
        console.error('Token expired or invalid');
        localStorage.removeItem('access_token');
        navigate('/login');
        return;
      }
      
      if (predResponse.ok) {
        const predData = await predResponse.json();
        console.log('Prediction data:', predData);
        setPrediction(predData);
      }

      // Fetch recommendations
      console.log('Fetching recommendations...');
      const recResponse = await fetch('http://localhost:8000/api/v1/recommendations/active', { headers });
      if (recResponse.ok) {
        const recData = await recResponse.json();
        console.log('Recommendations:', recData);
        setRecommendations(recData);
      }

      // Fetch usage history
      console.log('Fetching usage history...');
      const usageResponse = await fetch('http://localhost:8000/api/v1/usage/history?days=7', { headers });
      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        console.log('Usage data:', usageData);
        setUsageHistory(usageData);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
      setLoading(false);
    }
  };

  const submitFeedback = async (recId: number, accepted: boolean, implemented: boolean, rating: number) => {
    try {
      // FIXED: Changed 'token' to 'access_token'
      const token = localStorage.getItem('access_token');
      await fetch('http://localhost:8000/api/v1/recommendations/feedback', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recommendation_id: recId,
          accepted,
          implemented,
          rating,
          actual_savings_kwh: 0,
          estimated_savings_kwh: 0,
          time_to_implement_days: 0
        })
      });
      
      alert('Feedback submitted! The AI will learn from your response.');
      setFeedbackModal({ show: false, recommendation: null });
      
      // Refresh recommendations
      fetchDashboardData();
    } catch (error) {
      console.error('Feedback error:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">❌ {error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">⚡ Electricity Dashboard</h1>
            <p className="text-gray-600 mt-2">AI-Powered Predictive Billing</p>
          </div>
          <button
            onClick={onLogout}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Main Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Predicted Bill */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Predicted Monthly Bill</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ₹{prediction?.predicted_bill_amount.toFixed(2) || '0.00'}
                </p>
                <p className={`text-sm mt-2 ${prediction && prediction.percentage_change > 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {prediction && prediction.percentage_change > 0 ? '↑' : '↓'} {Math.abs(prediction?.percentage_change || 0).toFixed(1)}% vs last month
                </p>
              </div>
              <div className="text-4xl">💵</div>
            </div>
          </div>

          {/* Consumption */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Current Consumption</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {prediction?.current_consumption_kwh.toFixed(0) || '0'} kWh
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {prediction?.days_remaining || 0} days remaining
                </p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </div>

          {/* Confidence */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Prediction Confidence</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {((prediction?.confidence_score || 0) * 100).toFixed(0)}%
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(prediction?.confidence_score || 0) * 100}%` }}
                  ></div>
                </div>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Recommendations</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {recommendations.length}
                </p>
                <p className="text-sm text-green-600 mt-2">
                  Save up to ₹{recommendations.reduce((sum, r) => sum + r.estimated_savings_amount, 0).toFixed(0)}/mo
                </p>
              </div>
              <div className="text-4xl">💡</div>
            </div>
          </div>
        </div>

        {/* Usage Chart */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Last 7 Days Usage</h2>
          {usageHistory.length > 0 ? (
            <div className="space-y-3">
              {usageHistory.map((day, index) => (
                <div key={index} className="flex items-center">
                  <div className="w-24 text-sm text-gray-600">
                    {new Date(day.date).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}
                  </div>
                  <div className="flex-1">
                    <div className="bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-blue-600 h-6 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${Math.min((day.total_consumption_kwh / 30) * 100, 100)}%` }}
                      >
                        <span className="text-white text-xs font-semibold">{day.total_consumption_kwh.toFixed(1)} kWh</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-4">No usage data available</p>
          )}
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              🤖 AI-Powered Recommendations
            </h2>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              Reinforcement Learning
            </span>
          </div>
          
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <div key={rec.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                      {rec.source === 'RL Engine' && (
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                          AI
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
                    
                    <div className="flex items-center gap-4 mb-3">
                      <span className="text-sm text-green-600 font-medium">
                        💰 Save ₹{rec.estimated_savings_amount.toFixed(0)}/month
                      </span>
                      <span className="text-sm text-blue-600">
                        ⚡ {rec.estimated_savings_kwh.toFixed(1)} kWh/day
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        rec.effort_level === 'easy' ? 'bg-green-100 text-green-800' :
                        rec.effort_level === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {rec.effort_level}
                      </span>
                    </div>
                    
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 font-semibold mb-1">Action Steps:</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {rec.action_steps?.map((step: string, idx: number) => (
                          <li key={idx}>• {step}</li>
                        ))}
                      </ul>
                    </div>
                    
                    {/* Feedback buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => submitFeedback(rec.id, true, false, 4)}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                      >
                        ✓ Accept
                      </button>
                      <button
                        onClick={() => submitFeedback(rec.id, false, false, 2)}
                        className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
                      >
                        ✗ Dismiss
                      </button>
                      <button
                        onClick={() => setFeedbackModal({ show: true, recommendation: rec })}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        📝 Give Feedback
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {recommendations.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg mb-2">🤖 AI is analyzing your usage patterns...</p>
              <p className="text-sm">Check back soon for personalized recommendations!</p>
            </div>
          )}
        </div>

        {/* Lifestyle Patterns */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            🧠 Your Lifestyle Patterns
          </h2>
          <button
            onClick={async () => {
              // FIXED: Changed 'token' to 'access_token'
              const token = localStorage.getItem('access_token');
              const response = await fetch('http://localhost:8000/api/v1/patterns/summary', {
                headers: { 'Authorization': `Bearer ${token}` }
              });
              const data = await response.json();
              alert(data.summary);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            View Pattern Summary
          </button>
        </div>
      </div>

      {/* Feedback Modal */}
      {feedbackModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Provide Detailed Feedback</h3>
            <p className="text-sm text-gray-600 mb-4">
              Help the AI learn by sharing your experience with: <strong>{feedbackModal.recommendation?.title}</strong>
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Did you accept this recommendation?</label>
                <div className="flex gap-2">
                  <button 
                    onClick={() => {
                      submitFeedback(feedbackModal.recommendation.id, true, false, 4);
                    }}
                    className="flex-1 px-4 py-2 bg-green-100 text-green-800 rounded hover:bg-green-200 transition-colors"
                  >
                    ✓ Yes, I'll try this
                  </button>
                  <button 
                    onClick={() => {
                      submitFeedback(feedbackModal.recommendation.id, false, false, 2);
                    }}
                    className="flex-1 px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors"
                  >
                    ✗ No, not for me
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Rate this recommendation:</label>
                <div className="flex gap-2 justify-center">
                  {[1, 2, 3, 4, 5].map(star => (
                    <button
                      key={star}
                      onClick={() => {
                        submitFeedback(feedbackModal.recommendation.id, true, false, star);
                      }}
                      className="text-3xl hover:scale-125 transition-transform"
                      title={`${star} star${star > 1 ? 's' : ''}`}
                    >
                      ⭐
                    </button>
                  ))}
                </div>
                <p className="text-xs text-center text-gray-500 mt-2">1 = Poor, 5 = Excellent</p>
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setFeedbackModal({ show: false, recommendation: null })}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;