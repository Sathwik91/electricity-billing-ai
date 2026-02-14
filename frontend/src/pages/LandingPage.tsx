import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <span className="text-3xl">⚡</span>
            <span className="text-2xl font-bold text-gray-800">PowerAI</span>
          </div>
          <div className="flex space-x-4">
            <Link to="/login" className="px-6 py-2 text-indigo-600 font-semibold hover:text-indigo-700 transition">
              Login
            </Link>
            <Link to="/signup" className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition shadow-md">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <section className="container mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          AI-Powered Electricity
          <span className="text-indigo-600"> Bill Predictions</span>
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Predict your monthly electricity bills with 95 percent accuracy using advanced AI.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link to="/signup" className="px-8 py-4 bg-indigo-600 text-white rounded-lg font-bold text-lg hover:bg-indigo-700 transition shadow-xl">
            Start Free Trial
          </Link>
          <Link to="/login" className="px-8 py-4 bg-white text-indigo-600 rounded-lg font-bold text-lg hover:bg-gray-50 transition shadow-xl">
            Try Demo
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="text-4xl font-bold text-indigo-600 mb-2">95%</div>
            <div className="text-gray-600">Prediction Accuracy</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="text-4xl font-bold text-indigo-600 mb-2">30%</div>
            <div className="text-gray-600">Average Savings</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <div className="text-4xl font-bold text-indigo-600 mb-2">10K+</div>
            <div className="text-gray-600">Happy Users</div>
          </div>
        </div>
      </section>

      <section className="bg-white py-20">
        <div className="container mx-auto px-6">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-16">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 rounded-xl border-2 border-gray-100 hover:shadow-lg transition">
              <div className="text-5xl mb-4">🧠</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">AI Bill Predictions</h3>
              <p className="text-gray-600">Advanced LSTM neural networks predict your monthly bill with up to 95 percent accuracy.</p>
            </div>
            <div className="p-8 rounded-xl border-2 border-gray-100 hover:shadow-lg transition">
              <div className="text-5xl mb-4">📊</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Real-Time Analytics</h3>
              <p className="text-gray-600">Track your electricity consumption with beautiful charts.</p>
            </div>
            <div className="p-8 rounded-xl border-2 border-gray-100 hover:shadow-lg transition">
              <div className="text-5xl mb-4">💡</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Smart Recommendations</h3>
              <p className="text-gray-600">Get personalized energy-saving tips.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-indigo-600 to-purple-600 text-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6">Try It Now</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto opacity-90">
            Experience AI-driven electricity management with our demo account
          </p>
          <div className="bg-white bg-opacity-10 backdrop-blur rounded-xl p-8 max-w-md mx-auto">
            <p className="text-lg mb-4">Demo Credentials:</p>
            <div className="bg-white bg-opacity-20 rounded-lg p-4 mb-2">
              <p className="font-mono">demo1@example.com</p>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-4 mb-6">
              <p className="font-mono">Demo123!@#</p>
            </div>
            <Link to="/login" className="inline-block px-8 py-3 bg-white text-indigo-600 rounded-lg font-bold hover:bg-gray-100 transition">
              Try Demo Now
            </Link>
          </div>
        </div>
      </section>

      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-gray-400">&copy; 2026 PowerAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;