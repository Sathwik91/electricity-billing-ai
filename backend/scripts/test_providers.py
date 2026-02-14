"""
Test script to verify all providers work correctly
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.factory import ProviderFactory


async def test_all_providers():
    """Test all data providers"""
    
    print("🧪 Testing Data Providers")
    print("="*60)
    
    # Initialize
    await ProviderFactory.initialize()
    
    print("\n" + "="*60)
    print("Testing Smart Meter Provider")
    print("="*60)
    
    smart_meter = ProviderFactory.get_smart_meter_provider()
    print(f"Provider: {smart_meter.name}")
    
    try:
        reading = await smart_meter.get_current_reading("TEST_METER_1")
        print(f"✅ Current Reading:")
        print(f"   Timestamp: {reading.timestamp}")
        print(f"   Consumption: {reading.consumption_kwh:.2f} kWh")
        print(f"   Voltage: {reading.voltage}V")
        print(f"   Current: {reading.current}A")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Testing Weather Provider")
    print("="*60)
    
    weather = ProviderFactory.get_weather_provider()
    print(f"Provider: {weather.name}")
    
    try:
        current_weather = await weather.get_current_weather(12.9716, 77.5946)
        print(f"✅ Current Weather (Bangalore):")
        print(f"   Temperature: {current_weather.temperature_celsius}°C")
        print(f"   Humidity: {current_weather.humidity_percentage}%")
        print(f"   Pressure: {current_weather.pressure_hpa} hPa")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Testing Tariff Provider")
    print("="*60)
    
    tariff_provider = ProviderFactory.get_tariff_provider()
    print(f"Provider: {tariff_provider.name}")
    
    try:
        tariff = await tariff_provider.get_current_tariff("Karnataka")
        print(f"✅ Current Tariff:")
        print(f"   Fixed Charge: ₹{tariff.fixed_charge}")
        print(f"   Slabs: {len(tariff.slabs)}")
        
        # Test bill calculation
        bill = await tariff_provider.calculate_bill(350, tariff)
        print(f"✅ Bill for 350 kWh:")
        print(f"   Total: ₹{bill['total_amount']:.2f}")
        print(f"   Energy Charges: ₹{bill['energy_charges']:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Provider Status Summary")
    print("="*60)
    
    status = ProviderFactory.get_provider_status()
    for provider_type, info in status.items():
        print(f"{provider_type.upper()}: {info['name']}")
    
    print("\n✅ All tests complete!")


if __name__ == "__main__":
    asyncio.run(test_all_providers())