"""
Sample Data Generation Script
Generates realistic electricity usage data for testing and demo purposes
"""
import asyncio
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.models import User, UsageData, UserProfile


class DataGenerator:
    """Generate realistic electricity usage patterns"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def generate_household_profile(self, household_type: str) -> dict:
        """Generate realistic household profile"""
        profiles = {
            'small_apartment': {
                'household_size': random.randint(1, 2),
                'house_area_sqft': random.randint(500, 800),
                'house_type': 'apartment',
                'ac_usage': random.choice(['none', 'light']),
                'base_consumption': 8,  # kWh per day
                'peak_hours': [19, 20, 21, 22],
                'appliances': [
                    {'name': 'Refrigerator', 'count': 1, 'power_rating': 150},
                    {'name': 'TV', 'count': 1, 'power_rating': 100},
                    {'name': 'Washing Machine', 'count': 1, 'power_rating': 500},
                ]
            },
            'medium_apartment': {
                'household_size': random.randint(3, 4),
                'house_area_sqft': random.randint(900, 1500),
                'house_type': 'apartment',
                'ac_usage': random.choice(['moderate', 'heavy']),
                'base_consumption': 15,
                'peak_hours': [18, 19, 20, 21, 22],
                'appliances': [
                    {'name': 'Refrigerator', 'count': 1, 'power_rating': 200},
                    {'name': 'AC', 'count': 2, 'power_rating': 1500},
                    {'name': 'TV', 'count': 2, 'power_rating': 100},
                    {'name': 'Washing Machine', 'count': 1, 'power_rating': 500},
                    {'name': 'Microwave', 'count': 1, 'power_rating': 1000},
                ]
            },
            'large_house': {
                'household_size': random.randint(4, 6),
                'house_area_sqft': random.randint(1800, 3000),
                'house_type': 'independent_house',
                'ac_usage': 'heavy',
                'base_consumption': 25,
                'peak_hours': [18, 19, 20, 21, 22, 23],
                'appliances': [
                    {'name': 'Refrigerator', 'count': 2, 'power_rating': 200},
                    {'name': 'AC', 'count': 4, 'power_rating': 1500},
                    {'name': 'TV', 'count': 3, 'power_rating': 150},
                    {'name': 'Washing Machine', 'count': 1, 'power_rating': 600},
                    {'name': 'Microwave', 'count': 1, 'power_rating': 1200},
                    {'name': 'Water Heater', 'count': 2, 'power_rating': 2000},
                ]
            }
        }
        
        return profiles.get(household_type, profiles['medium_apartment'])
    
    def generate_hourly_pattern(
        self,
        hour: int,
        day_of_week: int,
        profile: dict,
        season: str = 'summer'
    ) -> float:
        """Generate realistic hourly consumption based on patterns"""
        base = profile['base_consumption'] / 24  # Base hourly consumption
        
        # Time-of-day pattern
        if hour in [0, 1, 2, 3, 4, 5]:  # Late night/early morning (sleeping)
            multiplier = 0.3
        elif hour in [6, 7, 8]:  # Morning routine
            multiplier = 1.2
        elif hour in [9, 10, 11, 12, 13, 14, 15, 16]:  # Daytime (work hours)
            multiplier = 0.5 if day_of_week < 5 else 1.0  # Lower on weekdays
        elif hour in profile['peak_hours']:  # Evening peak
            multiplier = 2.0
        else:  # Late evening
            multiplier = 1.0
        
        # Weekend adjustment
        if day_of_week >= 5:  # Weekend
            multiplier *= 1.2
        
        # Seasonal adjustment
        seasonal_factors = {
            'summer': 1.4,  # High AC usage
            'monsoon': 1.1,
            'winter': 0.9,
            'spring': 1.0
        }
        multiplier *= seasonal_factors.get(season, 1.0)
        
        # AC usage pattern
        if profile['ac_usage'] == 'heavy' and hour in [14, 15, 16, 21, 22, 23]:
            multiplier *= 1.5
        elif profile['ac_usage'] == 'moderate' and hour in [21, 22, 23]:
            multiplier *= 1.3
        
        # Add some randomness
        noise = np.random.normal(1, 0.1)
        
        consumption = base * multiplier * noise
        return max(0, consumption)  # Ensure non-negative
    
    def get_season(self, date: datetime) -> str:
        """Determine season based on month (India)"""
        month = date.month
        if month in [3, 4, 5, 6]:
            return 'summer'
        elif month in [7, 8, 9]:
            return 'monsoon'
        elif month in [10, 11]:
            return 'autumn'
        else:
            return 'winter'
    
    def get_weather_data(self, date: datetime, season: str) -> dict:
        """Generate realistic weather data"""
        seasonal_temps = {
            'summer': (28, 40),
            'monsoon': (25, 32),
            'autumn': (22, 30),
            'winter': (15, 25)
        }
        
        temp_range = seasonal_temps.get(season, (20, 30))
        temperature = np.random.uniform(temp_range[0], temp_range[1])
        
        # Humidity varies by season
        if season == 'monsoon':
            humidity = np.random.uniform(70, 95)
        elif season == 'summer':
            humidity = np.random.uniform(40, 70)
        else:
            humidity = np.random.uniform(50, 80)
        
        return {
            'temperature_celsius': round(temperature, 1),
            'humidity_percentage': round(humidity, 1)
        }
    
    async def generate_usage_data(
        self,
        user_id: int,
        start_date: datetime,
        days: int,
        household_type: str = 'medium_apartment'
    ):
        """Generate usage data for a user"""
        profile = self.generate_household_profile(household_type)
        
        async with self.async_session() as session:
            usage_records = []
            
            current_date = start_date
            for day in range(days):
                season = self.get_season(current_date)
                day_of_week = current_date.weekday()
                
                for hour in range(24):
                    timestamp = current_date + timedelta(hours=hour)
                    
                    # Generate consumption
                    consumption = self.generate_hourly_pattern(
                        hour, day_of_week, profile, season
                    )
                    
                    # Get weather data
                    weather = self.get_weather_data(timestamp, season)
                    
                    usage_record = UsageData(
                        user_id=user_id,
                        timestamp=timestamp,
                        consumption_kwh=round(consumption, 3),
                        temperature_celsius=weather['temperature_celsius'],
                        humidity_percentage=weather['humidity_percentage'],
                        is_weekend=(day_of_week >= 5),
                        hour_of_day=hour,
                        data_source='generated'
                    )
                    
                    usage_records.append(usage_record)
                
                current_date += timedelta(days=1)
                
                # Batch insert every 7 days
                if (day + 1) % 7 == 0:
                    session.add_all(usage_records)
                    await session.commit()
                    usage_records = []
                    print(f"Generated {day + 1}/{days} days of data...")
            
            # Insert remaining records
            if usage_records:
                session.add_all(usage_records)
                await session.commit()
            
            print(f"✓ Generated {days} days of usage data for user {user_id}")
    
    async def create_demo_users(self, count: int = 5):
        """Create demo users with varied profiles"""
        household_types = ['small_apartment', 'medium_apartment', 'large_house']
        cities = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad']
        
        async with self.async_session() as session:
            for i in range(count):
                # Create user
                user = User(
                    email=f"demo{i+1}@example.com",
                    hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXe.dFq/fB/RlPGCTwCx8bC8XYqxZKvVqK",
                    full_name=f"Demo User {i+1}",
                    role='household',
                    is_active=True,
                    is_verified=True
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                # Create profile
                household_type = random.choice(household_types)
                profile_data = self.generate_household_profile(household_type)
                
                user_profile = UserProfile(
                    user_id=user.id,
                    household_size=profile_data['household_size'],
                    house_area_sqft=profile_data['house_area_sqft'],
                    house_type=profile_data['house_type'],
                    location_city=random.choice(cities),
                    location_state='Karnataka',
                    location_pincode=f"5600{random.randint(10,99)}",
                    appliances=profile_data['appliances'],
                    occupancy_pattern=random.choice(['full_day', 'day_only', 'night_only']),
                    ac_usage=profile_data['ac_usage'],
                    has_solar_panels=random.choice([True, False]) if household_type == 'large_house' else False
                )
                
                session.add(user_profile)
                await session.commit()
                
                print(f"✓ Created demo user {i+1}: {user.email} ({household_type})")
                
                # Generate usage data (last 60 days)
                start_date = datetime.utcnow() - timedelta(days=60)
                await self.generate_usage_data(
                    user.id,
                    start_date,
                    60,
                    household_type
                )


async def main():
    """Main function to generate demo data"""
    print("=" * 60)
    print("AI-Powered Electricity Billing - Demo Data Generator")
    print("=" * 60)
    print()
    
    generator = DataGenerator()
    
    # Create demo users
    print("Creating demo users...")
    await generator.create_demo_users(count=5)
    
    print()
    print("=" * 60)
    print("✓ Demo data generation completed successfully!")
    print("=" * 60)
    print()
    print("You can now login with:")
    for i in range(5):
        print(f"  - demo{i+1}@example.com / Demo123!@#")
    print()


if __name__ == "__main__":
    asyncio.run(main())
