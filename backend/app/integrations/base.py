"""
Base classes for data providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class DataSource(Enum):
    """Available data sources"""
    SIMULATED = "simulated"
    SMART_METER_API = "smart_meter_api"
    WEATHER_API = "weather_api"
    UTILITY_API = "utility_api"


class UsageDataPoint:
    """Standardized usage data point"""
    def __init__(
        self,
        timestamp: datetime,
        consumption_kwh: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        power_factor: Optional[float] = None,
        frequency: Optional[float] = None
    ):
        self.timestamp = timestamp
        self.consumption_kwh = consumption_kwh
        self.voltage = voltage
        self.current = current
        self.power_factor = power_factor
        self.frequency = frequency


class WeatherDataPoint:
    """Standardized weather data point"""
    def __init__(
        self,
        timestamp: datetime,
        temperature_celsius: float,
        humidity_percentage: float,
        pressure_hpa: Optional[float] = None,
        wind_speed: Optional[float] = None,
        precipitation: Optional[float] = None,
        cloud_cover: Optional[int] = None
    ):
        self.timestamp = timestamp
        self.temperature_celsius = temperature_celsius
        self.humidity_percentage = humidity_percentage
        self.pressure_hpa = pressure_hpa
        self.wind_speed = wind_speed
        self.precipitation = precipitation
        self.cloud_cover = cloud_cover


class TariffStructure:
    """Standardized tariff structure"""
    def __init__(
        self,
        fixed_charge: float,
        slabs: List[Dict],
        time_of_use: Optional[Dict] = None,
        seasonal_rates: Optional[Dict] = None
    ):
        self.fixed_charge = fixed_charge
        self.slabs = slabs  # [{"min": 0, "max": 100, "rate": 3.50}, ...]
        self.time_of_use = time_of_use  # {"peak": rate, "off_peak": rate}
        self.seasonal_rates = seasonal_rates  # {"summer": multiplier, "winter": multiplier}


class SmartMeterProvider(ABC):
    """Abstract base class for smart meter data providers"""
    
    @abstractmethod
    async def get_current_reading(self, meter_id: str) -> UsageDataPoint:
        """Get current meter reading"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        meter_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[UsageDataPoint]:
        """Get historical meter readings"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if provider is available"""
        pass


class WeatherProvider(ABC):
    """Abstract base class for weather data providers"""
    
    @abstractmethod
    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherDataPoint:
        """Get current weather"""
        pass
    
    @abstractmethod
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> List[WeatherDataPoint]:
        """Get weather forecast"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if provider is available"""
        pass


class UtilityTariffProvider(ABC):
    """Abstract base class for utility tariff providers"""
    
    @abstractmethod
    async def get_current_tariff(self, region: str) -> TariffStructure:
        """Get current tariff structure"""
        pass
    
    @abstractmethod
    async def calculate_bill(
        self,
        consumption_kwh: float,
        tariff: TariffStructure
    ) -> Dict:
        """Calculate bill amount"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if provider is available"""
        pass