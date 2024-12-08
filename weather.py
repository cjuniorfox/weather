from typing import List, Dict
import json, os
from pyquery import PyQuery as pq
from urllib.error import HTTPError
import argparse

skycodes = {
    32: 'sunnyDay',
    34: 'sunnyDay',
    31: 'clearNight',
    26: 'cloudyFoggyDay',
    30: 'cloudyFoggyDay' ,
    27: 'cloudyFoggyNight',
    11: 'rainyDay',
    39: 'rainyDay' ,
    12: 'rainyNight',
    16: 'snowyIcyDay',
    14: 'snowyIcyNight',
    3:  'severe',
    4:  'severe',
    44: 'default'
}

weather_icons_fa = {
    'sunnyDay': '\uf185',        # FA Sun
    'clearNight': '\uf186',      # FA Moon
    'cloudyFoggyDay': '\uf6c4',  # FA Cloud-Sun
    'cloudyFoggyNight': '\uf6c3',# FA Cloud-Moon
    'rainyDay': '\uf73d',        # FA Cloud-Sun-Rain
    'rainyNight': '\uf73c',      # FA Cloud-Moon-Rain
    'snowyIcyDay': '\uf2dc',     # FA Snowflake
    'snowyIcyNight': '\uf2dc',   # FA Snowflake (reuse)
    'severe': '\uf76c',          # FA Cloud-Showers-Heavy
    'default': '\uf0c2',         # FA Cloud
    'feel' : '\uf2c9',           # FA Thermometer
    'wind' : '\uf72e',           # FA Wind
    'visibility' : '\uf06e',     # FA Eye
    'humidity' : '\uf043',       # FA Humidity
    'rain' :  '\uf0e9'           # FA Weather Light raining
}

# Define weather emojis
weather_icons_emoji = {
    'sunnyDay': '\u2600\ufe0f',
    'clearNight': '🌙',
    'cloudyFoggyDay': '⛅',
    'cloudyFoggyNight': '🌥️',
    'rainyDay': '🌧️',
    'rainyNight': '🌧️',
    'snowyIcyDay': '❄️',
    'snowyIcyNight': ' ',
    'severe': '🌩️',
    'default': '☁️',
    'feel': '️️🌡️',
    'wind': '🍃',
    'visibility': '👁️',
    'humidity': '💧',
    'rain': '☔'
}

class WeatherForecast:
    class Prediction:
        def __init__(
                self, 
                moment: str, 
                status: str,
                skycode : str,
                icon : str,
                chance_of_rain: str, 
                temperature: str = None, 
                min: str = None, 
                max: str = None
        ):
            self.moment = moment
            self.status = status
            self.skycode = skycode
            self.icon = icon
            self.chance_of_rain = chance_of_rain
            self.temperature = temperature
            self.min = min
            self.max = max
    
    class Temperature:
        def __init__(
                self, 
                current: str, 
                feel: str, 
                max: str, 
                min: str):
            self.current = current
            self.feel = feel
            self.max = max
            self.min = min

    def __init__(
        self,
        weather_id: str,
        lang: str,
        location: str,
        status: str,
        status_code: str,
        icon: str,
        wind_speed: str,
        humidity: str,
        visibility: str,
        air_quality: str,
        temperature : Temperature = None,
        hourly_predictions: List[Prediction] = None,
        daily_predictions: List[Prediction] = None
    ):
        self.weather_id = weather_id
        self.lang = lang
        self.location = location
        self.status = status
        self.status_code = status_code
        self.icon = icon
        self.wind_speed = wind_speed
        self.humidity = humidity
        self.visibility = visibility
        self.air_quality = air_quality
        self.temperature = WeatherForecast.Temperature(**temperature)
        self.hourly_predictions = [
            WeatherForecast.Prediction(**hourly_prediction) for hourly_prediction in (hourly_predictions or [])
        ]
        self.daily_predictions = [
            WeatherForecast.Prediction(**daily_predicion) for daily_predicion in (daily_predictions or [])
        ]

class WeatherForecastExtractor:
    class TemperatureExtractor:
        def __init__(self, html_data):
            self.html_data = html_data
        
        def current(self):
            return self.html_data("span[data-testid='TemperatureValue']").eq(0).text()
        
        def feel(self):
            return self.html_data(
                "div[data-testid='FeelsLikeSection'] > span > span[data-testid='TemperatureValue']"
                ).text()
        def max(self):
            return self.html_data(
                "div[data-testid='wxData'] > span[data-testid='TemperatureValue']"
                ).eq(0).text()
        def min(self):
            return self.html_data(
                "div[data-testid='wxData'] > span[data-testid='TemperatureValue']"
                ).eq(1).text()
        
    def __init__(self, html_data):
        self.html_data = html_data
        self.temperature = WeatherForecastExtractor.TemperatureExtractor(self.html_data)

    def location(self):
        return self.html_data("h1").text()

    def status(self):
        status = self.html_data("div[data-testid='wxPhrase']").text()
        status = f"{status[:16]}.." if len(status) > 17 else status
        return status
    
    def status_code(self):
        self.__status_code = self.html_data("#regionHeader").attr("class").split(" ")[2].split("-")[2]
        return self.__status_code
    
    def icon(self):
        status_code = self.__status_code
        return (
            weather_icons[status_code] if status_code in weather_icons else weather_icons["default"]
        )

    def wind_speed(self):
        return self.html_data("span[data-testid='Wind']").text().split("\n")[1]
    
    def humidity(self):
        return self.html_data("span[data-testid='PercentageValue']").text()
    
    def visibility(self):
        return self.html_data("span[data-testid='VisibilityValue']").text()

    def air_quality(self):
        return self.html_data("text[data-testid='DonutChartValue']").text()
    
    def hourly_predictions(self):
        predictions = [
            {
                'moment': pq(span)("h3 > span").text(),
                'temperature': pq(span)("span[data-testid='TemperatureValue']").text(),
                'status' : pq(span)("svg[data-testid='Icon'] title").contents()[0],
                'skycode' :  pq(span)("svg[data-testid='Icon']").attr('skycode'),
                'icon' : self.__icon_predictions(int(pq(span)("svg[data-testid='Icon']").attr('skycode'))),
                'chance_of_rain' : pq(span)("div[data-testid='SegmentPrecipPercentage'] > span").contents()[1],
            }
                for span in self.html_data("section[data-testid='HourlyWeatherModule'] ul[data-testid='WeatherTable'] li")
            ]
        return predictions
    
    def daily_predictions(self):
        predictions = [
            {
                'moment': pq(span)("h3 > span").text(),
                'max': pq(span)("div[data-testid='SegmentHighTemp'] span[data-testid='TemperatureValue']").eq(0).text(),
                'min': pq(span)("div[data-testid='SegmentHighTemp'] span[data-testid='TemperatureValue']").eq(1).text(),
                'status' : pq(span)("svg[data-testid='Icon'] title").contents()[0],
                'skycode' :  pq(span)("svg[data-testid='Icon']").attr('skycode'),
                'icon' : self.__icon_predictions(int(pq(span)("svg[data-testid='Icon']").attr('skycode'))),
                'chance_of_rain' : pq(span)("div[data-testid='SegmentPrecipPercentage'] span").contents()[1],
            }
                for span in self.html_data("section[data-testid='DailyWeatherModule'] ul[data-testid='WeatherTable'] li")
            ]
        return predictions
    
    def to_weather_forecast(self, weather_id: str, lang: str) -> WeatherForecast:
        return WeatherForecast(
            weather_id=weather_id,
            lang=lang,
            location=self.location(),
            status=self.status(),
            status_code=self.status_code(),
            icon=self.icon(),
            wind_speed=self.wind_speed(),
            humidity=self.humidity(),
            visibility=self.visibility(),
            air_quality=self.air_quality(),
            temperature={
                "current": self.temperature.current(),
                "feel": self.temperature.feel(),
                "max": self.temperature.max(),
                "min": self.temperature.min(),
            },
            hourly_predictions=self.hourly_predictions(),
            daily_predictions=self.daily_predictions()  
        )

    def __icon_predictions(self,skycode: int) -> str:
        status_code = skycodes[skycode] if skycode in skycodes else 'default'
        return weather_icons[status_code]


def serializer(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def grab_weather_data(lang, weather_id = None) -> str :
    url = f"https://weather.com/{lang}/weather/today/l/{weather_id}"
    if not weather_id:
        url = f"https://weather.com/{lang}/weather/today"
    elif len(weather_id) < 64 :
        raise ValueError("Invalid weather_id")
    if not lang:
        raise ValueError("lang must be specified")
    try:
        return pq(url=url)
    except HTTPError as e:
        if(e.code == 404):
            raise ValueError(f"HTTP error {e.code} when fetching weather data. Check for the location_id or lang data.")

def get_weather_forecast(lang, weather_id = None) -> WeatherForecast:
    html_data = grab_weather_data(lang, weather_id)
    forecast = WeatherForecastExtractor(html_data) 
    return forecast.to_weather_forecast(weather_id,lang)

def weather_to_waybar(wf: WeatherForecast) -> Dict:
    hourly_predictions = "\n".join(
        f"{h.moment}\t{'\t' if len(h.moment) < 4 else ''}  {h.temperature}\t\t{h.icon}\t{weather_icons['rain']} {h.chance_of_rain}"
        for h in wf.hourly_predictions
    )
    daily_predictions = "\n".join(
        f"{h.moment}\t{'\t' if len(h.moment) < 5 else ''}{h.max}/<small>{h.min}</small>\t{h.icon}\t{weather_icons['rain']} {h.chance_of_rain}"
        for h in wf.daily_predictions
    )
    
    tooltip_text = f"""{wf.location}

<span size="xx-large">{wf.icon}\t\t{wf.temperature.current}</span>

{wf.status}
{wf.temperature.max}/<small>{wf.temperature.max}</small>\t {weather_icons['feel']} {wf.temperature.feel}

{weather_icons['wind']} {wf.wind_speed}\t{weather_icons['humidity']} {wf.humidity}
{weather_icons['visibility']} {wf.visibility}\t AQI {wf.air_quality}

{hourly_predictions}

{daily_predictions}
"""

    return {
        "text": f"{wf.icon} {wf.temperature.current}",
        "alt": wf.status,
        "tooltip": tooltip_text,
        "class": wf.status_code,
    }

if __name__ == "__main__":
    ## Get current locale, or use the default one
    parser = argparse.ArgumentParser(description="Weather forecast grabber from weather.com")
    parser.add_argument("--location", "-l", type=str, help="64-character-hex code for location obtained from weather.com")
    parser.add_argument("--lang", "-L", type=str, help="Language (pt-BR, fr-FR, etc.), If not set, uses the machine one.")
    parser.add_argument("--output", "-o", type=str, choices=['json','waybar'], default='json', help="Output format. json or waybar")
    parser.add_argument("--icons", "-i", type=str, choices=['fa','emoji'], default='emoji', help="Icon set. 'fa' for Font-Awesome, or 'widget'")

    args = parser.parse_args()

    weather_icons = weather_icons_emoji if args.icons == 'emoji' else weather_icons_fa
    lang = args.lang if args.lang else os.getenv("LANG","en_IL.UTF-8").split(".")[0].replace("_","-")
    weather_forecast = get_weather_forecast(lang=lang, weather_id=args.location)

    if args.output == 'waybar':
        waybar_data = weather_to_waybar(weather_forecast)
        print(json.dumps(waybar_data))
    else:
        print(json.dumps(weather_forecast,default=serializer, indent=2))