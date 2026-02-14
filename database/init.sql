-- Database Initialization Script for AI-Powered Electricity Billing System
-- PostgreSQL 15+

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('household', 'admin', 'utility_provider');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_type AS ENUM ('bill_threshold', 'unusual_usage', 'cost_saving', 'system');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_usage_data_user_timestamp ON usage_data(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usage_data_timestamp ON usage_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_user_month ON predictions(user_id, billing_month);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_user_status ON alerts(user_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id, created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DO $$ 
BEGIN
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
    CREATE TRIGGER update_user_profiles_updated_at 
        BEFORE UPDATE ON user_profiles 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_tariff_rates_updated_at ON tariff_rates;
    CREATE TRIGGER update_tariff_rates_updated_at 
        BEFORE UPDATE ON tariff_rates 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN others THEN null;
END $$;

-- Insert default tariff rates (Indian example)
INSERT INTO tariff_rates (
    utility_provider,
    region,
    tariff_name,
    rate_slabs,
    fixed_charge,
    has_tou_rates,
    effective_from,
    is_active
) VALUES (
    'Default Utility',
    'India',
    'Standard Residential Tariff',
    '{"0-100": 3.50, "101-200": 4.50, "201-400": 6.00, "401-500": 7.00, "500+": 8.00}',
    50.00,
    false,
    '2024-01-01',
    true
) ON CONFLICT DO NOTHING;

-- Create function to calculate days in billing cycle
CREATE OR REPLACE FUNCTION get_billing_cycle_days(billing_month TEXT)
RETURNS INTEGER AS $$
DECLARE
    year INTEGER;
    month INTEGER;
    days INTEGER;
BEGIN
    year := CAST(SPLIT_PART(billing_month, '-', 1) AS INTEGER);
    month := CAST(SPLIT_PART(billing_month, '-', 2) AS INTEGER);
    days := EXTRACT(DAY FROM (DATE_TRUNC('month', MAKE_DATE(year, month, 1)) + INTERVAL '1 month - 1 day'));
    RETURN days;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user's average consumption
CREATE OR REPLACE FUNCTION get_user_avg_consumption(
    p_user_id INTEGER,
    p_days INTEGER DEFAULT 30
)
RETURNS NUMERIC AS $$
DECLARE
    avg_consumption NUMERIC;
BEGIN
    SELECT AVG(consumption_kwh) INTO avg_consumption
    FROM usage_data
    WHERE user_id = p_user_id
      AND timestamp >= NOW() - (p_days || ' days')::INTERVAL;
    
    RETURN COALESCE(avg_consumption, 0);
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for daily aggregations (for performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_usage_summary AS
SELECT 
    user_id,
    DATE(timestamp) as usage_date,
    SUM(consumption_kwh) as total_consumption_kwh,
    AVG(consumption_kwh) as avg_consumption_kwh,
    MAX(consumption_kwh) as peak_consumption_kwh,
    AVG(temperature_celsius) as avg_temperature,
    AVG(humidity_percentage) as avg_humidity,
    COUNT(*) as data_points
FROM usage_data
GROUP BY user_id, DATE(timestamp);

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_usage_summary_user_date 
ON daily_usage_summary(user_id, usage_date DESC);

-- Create function to refresh daily summary
CREATE OR REPLACE FUNCTION refresh_daily_usage_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_usage_summary;
END;
$$ LANGUAGE plpgsql;

-- Create view for active alerts with user info
CREATE OR REPLACE VIEW active_alerts_view AS
SELECT 
    a.*,
    u.email,
    u.full_name,
    u.phone_number
FROM alerts a
JOIN users u ON a.user_id = u.id
WHERE a.status = 'active';

-- Create view for prediction accuracy
CREATE OR REPLACE VIEW prediction_accuracy_view AS
SELECT 
    user_id,
    billing_month,
    predicted_consumption_kwh,
    actual_consumption_kwh,
    predicted_bill_amount,
    actual_bill_amount,
    ABS(predicted_consumption_kwh - actual_consumption_kwh) as consumption_error_kwh,
    ABS(predicted_bill_amount - actual_bill_amount) as bill_error_amount,
    CASE 
        WHEN actual_consumption_kwh > 0 
        THEN ABS(predicted_consumption_kwh - actual_consumption_kwh) / actual_consumption_kwh * 100
        ELSE NULL
    END as consumption_error_percentage,
    CASE 
        WHEN actual_bill_amount > 0 
        THEN ABS(predicted_bill_amount - actual_bill_amount) / actual_bill_amount * 100
        ELSE NULL
    END as bill_error_percentage
FROM predictions
WHERE actual_consumption_kwh IS NOT NULL 
  AND actual_bill_amount IS NOT NULL;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create admin user (password: Admin123!@#)
-- Note: In production, use a secure password and hash it properly
INSERT INTO users (
    email,
    hashed_password,
    full_name,
    role,
    is_active,
    is_verified
) VALUES (
    'admin@electricitybilling.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aQy.XYcvP2J2', -- Admin123!@#
    'System Administrator',
    'admin',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Create sample demo user (password: Demo123!@#)
INSERT INTO users (
    email,
    hashed_password,
    full_name,
    role,
    is_active,
    is_verified
) VALUES (
    'demo@electricitybilling.ai',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXe.dFq/fB/RlPGCTwCx8bC8XYqxZKvVqK', -- Demo123!@#
    'Demo User',
    'household',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Add demo user profile
DO $$
DECLARE
    demo_user_id INTEGER;
BEGIN
    SELECT id INTO demo_user_id FROM users WHERE email = 'demo@electricitybilling.ai';
    
    IF demo_user_id IS NOT NULL THEN
        INSERT INTO user_profiles (
            user_id,
            household_size,
            house_area_sqft,
            house_type,
            location_city,
            location_state,
            location_pincode,
            appliances,
            occupancy_pattern,
            ac_usage,
            has_solar_panels
        ) VALUES (
            demo_user_id,
            4,
            1500,
            'apartment',
            'Bangalore',
            'Karnataka',
            '560001',
            '[{"name": "AC", "count": 2, "power_rating": 1500}, {"name": "Refrigerator", "count": 1, "power_rating": 200}, {"name": "Washing Machine", "count": 1, "power_rating": 500}]',
            'full_day',
            'moderate',
            false
        ) ON CONFLICT (user_id) DO NOTHING;
    END IF;
END $$;

-- Vacuum and analyze
VACUUM ANALYZE;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE 'Admin user: admin@electricitybilling.ai (password: Admin123!@#)';
    RAISE NOTICE 'Demo user: demo@electricitybilling.ai (password: Demo123!@#)';
END $$;
