import pytest
from src.weather.weather import WeatherForecast, WeatherForecastExtractor, grab_weather_data, get_weather_forecast

def test_weather_forecast_initialization():
    wf = WeatherForecast(
        lang='en',
        location='Test Location',
        status='Sunny',
        status_code='01',
        icon='☀️',
        wind_speed='5 km/h',
        humidity='50%',
        visibility='10 km',
        air_quality=None,
        temperature=None,
        hourly_predictions=[],
        daily_predictions=[]
    )
    
    assert wf.lang == 'en'
    assert wf.location == 'Test Location'
    assert wf.status == 'Sunny'
    assert wf.status_code == '01'
    assert wf.icon == '☀️'
    assert wf.wind_speed == '5 km/h'
    assert wf.humidity == '50%'
    assert wf.visibility == '10 km'
    assert wf.air_quality is None
    assert wf.temperature is None
    assert wf.hourly_predictions == []
    assert wf.daily_predictions == []

def test_weather_forecast_extractor():
    # Mock HTML data for testing
    class MockHtmlData:
        def __init__(self):
            self.data = {
                "h1": "Test Location",
                "div[data-testid='wxPhrase']": "Sunny",
                "#regionHeader": "weather-status sunny",
                "span[data-testid='Wind'] span": "5 km/h",
                "span[data-testid='PercentageValue']": "50%",
                "span[data-testid='TemperatureValue']": "25°C",
                "section[data-testid='AirQualityModule'] header h2": "Good",
                "span[data-testid='AirQualityCategory']": "Good",
                "text[data-testid='DonutChartValue']": "50",
                "p[data-testid='AirQualitySeverity']": "Good",
                "span[data-testid='VisibilityValue']": "10 km"
            }

        def text(self, selector):
            return self.data.get(selector, "")

        def attr(self, selector):
            return self.data.get(selector, "")

        def eq(self, index):
            return self.data["span[data-testid='TemperatureValue']"]

    html_data = MockHtmlData()
    extractor = WeatherForecastExtractor(html_data)

    assert extractor.location() == "Test Location"
    assert extractor.status() == "Sunny"
    assert extractor.status_code() == "01"
    assert extractor.wind_speed() == "5 km/h"
    assert extractor.humidity() == "50%"
    assert extractor.temperature() == {
        "current": "25°C",
        "feel": "25°C",
        "max": "25°C",
        "min": "25°C"
    }
    assert extractor.visibility() == "10 km"
    assert extractor.air_quality() == {
        "title": "Good",
        "acronym": "G",
        "color": extractor._WeatherForecastExtractor__aqi_color(),
        "category": "Good",
        "aqi": "50",
        "severity": "Good"
    }

def test_grab_weather_data():
    # This test would require mocking the network call
    pass

def test_get_weather_forecast():
    # This test would require mocking the network call
    pass

# Additional tests can be added as needed.