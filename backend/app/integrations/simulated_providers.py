"""
Simulated data providers (for development and testing)
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

from app.integrations.base import (
    SmartMeterProvider,
    WeatherProvider,
    UtilityTariffProvider,
    UsageDataPoint,
    WeatherDataPoint,
    TariffStructure
)


class SimulatedSmartMeterProvider(SmartMeterProvider):
    """Simulated smart meter for development"""
    
    def __init__(self):
        self.name = "Simulated Smart Meter"
    
    async def get_current_reading(self, meter_id: str) -> UsageDataPoint:
        """Generate realistic simulated reading"""
        hour = datetime.now().hour
        
        # Realistic consumption pattern
        base = random.uniform(0.5, 2.0)
        if 0 <= hour < 6:
            multiplier = random.uniform(0.3, 0.5)
        elif 6 <= hour < 9:
            multiplier = random.uniform(1.0, 1.5)
        elif 9 <= hour < 17:
            multiplier = random.uniform(0.6, 1.0)
        elif 17 <= hour < 22:
            multiplier = random.uniform(1.2, 1.8)
        else:
            multiplier = random.uniform(0.4, 0.6)
        
        consumption = base * multiplier
        
        return UsageDataPoint(
            timestamp=datetime.now(),
            consumption_kwh=consumption,
            voltage=random.uniform(220, 240),
            current=random.uniform(5, 30),
            power_factor=random.uniform(0.85, 0.95),
            frequency=50.0
        )
    
    async def get_historical_data(
        self,
        meter_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[UsageDataPoint]:
        """Generate historical simulated data"""
        data_points = []
        current = start_date
        
        while current <= end_date:
            hour = current.hour
            base = random.uniform(0.5, 2.0)
            
            if 0 <= hour < 6:
                multiplier = random.uniform(0.3, 0.5)
            elif 6 <= hour < 9:
                multiplier = random.uniform(1.0, 1.5)
            elif 9 <= hour < 17:
                multiplier = random.uniform(0.6, 1.0)
            elif 17 <= hour < 22:
                multiplier = random.uniform(1.2, 1.8)
            else:
                multiplier = random.uniform(0.4, 0.6)
            
            is_weekend = current.weekday() >= 5
            if is_weekend:
                multiplier *= 1.2
            
            consumption = base * multiplier
            
            data_points.append(UsageDataPoint(
                timestamp=current,
                consumption_kwh=consumption,
                voltage=random.uniform(220, 240),
                current=random.uniform(5, 30),
                power_factor=random.uniform(0.85, 0.95),
                frequency=50.0
            ))
            
            current += timedelta(hours=1)
        
        return data_points
    
    async def test_connection(self) -> bool:
        """Always available"""
        return True


class SimulatedWeatherProvider(WeatherProvider):
    """Simulated weather for development"""
    
    def __init__(self):
        self.name = "Simulated Weather"
    
    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherDataPoint:
        """Generate realistic weather"""
        return WeatherDataPoint(
            timestamp=datetime.now(),
            temperature_celsius=random.uniform(20, 35),
            humidity_percentage=random.uniform(40, 80),
            pressure_hpa=random.uniform(1010, 1020),
            wind_speed=random.uniform(0, 20),
            precipitation=random.uniform(0, 5),
            cloud_cover=random.randint(0, 100)
        )
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> List[WeatherDataPoint]:
        """Generate forecast"""
        forecast = []
        current_time = datetime.now()
        
        for day in range(days):
            for hour in range(24):
                timestamp = current_time + timedelta(days=day, hours=hour)
                forecast.append(WeatherDataPoint(
                    timestamp=timestamp,
                    temperature_celsius=random.uniform(20, 35),
                    humidity_percentage=random.uniform(40, 80),
                    pressure_hpa=random.uniform(1010, 1020),
                    wind_speed=random.uniform(0, 20),
                    precipitation=random.uniform(0, 5),
                    cloud_cover=random.randint(0, 100)
                ))
        
        return forecast
    
    async def test_connection(self) -> bool:
        """Always available"""
        return True


class SimulatedUtilityTariffProvider(UtilityTariffProvider):
    """Simulated utility tariff"""
    
    def __init__(self):
        self.name = "Simulated Utility Tariff"
    
    async def get_current_tariff(self, region: str) -> TariffStructure:
        """Return standard tariff structure"""
        return TariffStructure(
            fixed_charge=50.0,
            slabs=[
                {"min": 0, "max": 100, "rate": 3.50},
                {"min": 101, "max": 200, "rate": 4.50},
                {"min": 201, "max": 400, "rate": 6.00},
                {"min": 401, "max": 500, "rate": 7.00},
                {"min": 501, "max": float('inf'), "rate": 8.00}
            ],
            time_of_use={
                "peak": 1.5,      # 17:00-22:00
                "off_peak": 0.8   # 22:00-06:00
            },
            seasonal_rates={
                "summer": 1.2,    # June-September
                "winter": 0.9     # December-February
            }
        )
    
    async def calculate_bill(
        self,
        consumption_kwh: float,
        tariff: TariffStructure
    ) -> Dict:
        """Calculate bill based on slabs"""
        bill_amount = tariff.fixed_charge
        energy_charges = 0
        remaining = consumption_kwh
        
        for slab in tariff.slabs:
            slab_min = slab["min"]
            slab_max = slab["max"]
            rate = slab["rate"]
            
            if remaining <= 0:
                break
            
            slab_size = slab_max - slab_min
            units_in_slab = min(remaining, slab_size)
            
            energy_charges += units_in_slab * rate
            remaining -= units_in_slab
        
        bill_amount += energy_charges
        
        return {
            "total_amount": bill_amount,
            "fixed_charge": tariff.fixed_charge,
            "energy_charges": energy_charges,
            "consumption_kwh": consumption_kwh,
            "breakdown": self._get_breakdown(consumption_kwh, tariff)
        }
    
    def _get_breakdown(self, consumption: float, tariff: TariffStructure) -> List[Dict]:
        """Get detailed breakdown"""
        breakdown = []
        remaining = consumption
        
        for slab in tariff.slabs:
            if remaining <= 0:
                break
            
            slab_min = slab["min"]
            slab_max = slab["max"]
            rate = slab["rate"]
            slab_size = slab_max - slab_min
            
            units = min(remaining, slab_size)
            amount = units * rate
            
            breakdown.append({
                "slab": f"{slab_min}-{slab_max}",
                "units": units,
                "rate": rate,
                "amount": amount
            })
            
            remaining -= units
        
        return breakdown
    
    async def test_connection(self) -> bool:
        """Always available"""
        return True