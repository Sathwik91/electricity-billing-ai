"""
Provider Factory - Automatically selects best available provider
"""
import os
from typing import Optional
import asyncio

from app.integrations.base import (
    SmartMeterProvider,
    WeatherProvider,
    UtilityTariffProvider,
    DataSource
)
from app.integrations.simulated_providers import (
    SimulatedSmartMeterProvider,
    SimulatedWeatherProvider,
    SimulatedUtilityTariffProvider
)
from app.integrations.real_providers import (
    RealSmartMeterProvider,
    OpenWeatherMapProvider,
    RealUtilityTariffProvider
)


class ProviderFactory:
    """
    Factory that automatically selects and initializes the best available provider
    with fallback to simulated data
    """
    
    _smart_meter_provider: Optional[SmartMeterProvider] = None
    _weather_provider: Optional[WeatherProvider] = None
    _tariff_provider: Optional[UtilityTariffProvider] = None
    
    _initialized = False
    
    @classmethod
    async def initialize(cls):
        """Initialize all providers based on configuration"""
        if cls._initialized:
            return
        
        print("🔌 Initializing Data Providers...")
        print("="*60)
        
        # Initialize Smart Meter Provider
        cls._smart_meter_provider = await cls._init_smart_meter()
        
        # Initialize Weather Provider
        cls._weather_provider = await cls._init_weather()
        
        # Initialize Tariff Provider
        cls._tariff_provider = await cls._init_tariff()
        
        cls._initialized = True
        print("="*60)
        print("✅ All providers initialized\n")
    
    @classmethod
    async def _init_smart_meter(cls) -> SmartMeterProvider:
        """Initialize smart meter provider with fallback"""
        
        # Try Real Smart Meter API first
        smart_meter_url = os.getenv("SMART_METER_API_URL")
        smart_meter_key = os.getenv("SMART_METER_API_KEY")
        
        if smart_meter_url and smart_meter_key:
            print("📡 Attempting Real Smart Meter API...")
            try:
                provider = RealSmartMeterProvider(smart_meter_url, smart_meter_key)
                if await provider.test_connection():
                    print("   ✅ Connected to Real Smart Meter API")
                    return provider
                else:
                    print("   ⚠️  Real Smart Meter API unavailable")
            except Exception as e:
                print(f"   ❌ Error connecting to Real Smart Meter: {e}")
        
        # Fallback to Simulated
        print("   🔄 Using Simulated Smart Meter (Development Mode)")
        return SimulatedSmartMeterProvider()
    
    @classmethod
    async def _init_weather(cls) -> WeatherProvider:
        """Initialize weather provider with fallback"""
        
        # Try OpenWeatherMap API first
        weather_api_key = os.getenv("OPENWEATHER_API_KEY")
        
        if weather_api_key:
            print("🌤️  Attempting OpenWeatherMap API...")
            try:
                provider = OpenWeatherMapProvider(weather_api_key)
                if await provider.test_connection():
                    print("   ✅ Connected to OpenWeatherMap")
                    return provider
                else:
                    print("   ⚠️  OpenWeatherMap API unavailable")
            except Exception as e:
                print(f"   ❌ Error connecting to OpenWeatherMap: {e}")
        
        # Fallback to Simulated
        print("   🔄 Using Simulated Weather (Development Mode)")
        return SimulatedWeatherProvider()
    
    @classmethod
    async def _init_tariff(cls) -> UtilityTariffProvider:
        """Initialize tariff provider with fallback"""
        
        # Try Real Utility API first
        tariff_url = os.getenv("UTILITY_TARIFF_API_URL")
        tariff_key = os.getenv("UTILITY_TARIFF_API_KEY")
        
        if tariff_url and tariff_key:
            print("⚡ Attempting Real Utility Tariff API...")
            try:
                provider = RealUtilityTariffProvider(tariff_url, tariff_key)
                if await provider.test_connection():
                    print("   ✅ Connected to Real Utility API")
                    return provider
                else:
                    print("   ⚠️  Real Utility API unavailable")
            except Exception as e:
                print(f"   ❌ Error connecting to Utility API: {e}")
        
        # Fallback to Simulated
        print("   🔄 Using Simulated Tariff (Development Mode)")
        return SimulatedUtilityTariffProvider()
    
    @classmethod
    def get_smart_meter_provider(cls) -> SmartMeterProvider:
        """Get the active smart meter provider"""
        if not cls._initialized:
            raise RuntimeError("ProviderFactory not initialized. Call await ProviderFactory.initialize() first")
        return cls._smart_meter_provider
    
    @classmethod
    def get_weather_provider(cls) -> WeatherProvider:
        """Get the active weather provider"""
        if not cls._initialized:
            raise RuntimeError("ProviderFactory not initialized. Call await ProviderFactory.initialize() first")
        return cls._weather_provider
    
    @classmethod
    def get_tariff_provider(cls) -> UtilityTariffProvider:
        """Get the active tariff provider"""
        if not cls._initialized:
            raise RuntimeError("ProviderFactory not initialized. Call await ProviderFactory.initialize() first")
        return cls._tariff_provider
    
    @classmethod
    def get_provider_status(cls) -> dict:
        """Get status of all providers"""
        return {
            "smart_meter": {
                "name": cls._smart_meter_provider.name if cls._smart_meter_provider else "Not initialized",
                "type": type(cls._smart_meter_provider).__name__ if cls._smart_meter_provider else None
            },
            "weather": {
                "name": cls._weather_provider.name if cls._weather_provider else "Not initialized",
                "type": type(cls._weather_provider).__name__ if cls._weather_provider else None
            },
            "tariff": {
                "name": cls._tariff_provider.name if cls._tariff_provider else "Not initialized",
                "type": type(cls._tariff_provider).__name__ if cls._tariff_provider else None
            }
        }
    
    @classmethod
    async def refresh_providers(cls):
        """Re-initialize providers (useful for switching modes)"""
        cls._initialized = False
        await cls.initialize()


# Convenience functions
async def get_smart_meter_reading(meter_id: str):
    """Quick access to smart meter reading"""
    provider = ProviderFactory.get_smart_meter_provider()
    return await provider.get_current_reading(meter_id)


async def get_current_weather(latitude: float, longitude: float):
    """Quick access to current weather"""
    provider = ProviderFactory.get_weather_provider()
    return await provider.get_current_weather(latitude, longitude)


async def get_current_tariff(region: str):
    """Quick access to current tariff"""
    provider = ProviderFactory.get_tariff_provider()
    return await provider.get_current_tariff(region)