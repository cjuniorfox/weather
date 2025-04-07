# This file contains the main functionality of the weather library. It includes classes such as WeatherForecast, WeatherForecastExtractor, and various methods for fetching and formatting weather data.

import json, os, re, argparse
from typing import List, Dict
from pyquery import PyQuery as pq
from urllib.error import HTTPError
from time import sleep

skynames = {
    'sunny': 'sunnyDay',
    'clear': 'clearNight',
    'partly-cloudy-day': 'cloudyFoggyDay',
    'mostly-cloudy-day': 'cloudy',
    'partly-cloudy-night': 'cloudyFoggyNight',
    'mostly-cloudy-night': 'cloudy',
    'rainy': 'rainyDay',
    'rain' : 'rainyDay',
    'snow': 'snowyIcyNight',
    'showers': 'rainyNight',
    'scattered-thunderstorms-day':  'severe',
    'thunderstorms':  'severe',
    'default': 'default'
}

weather_icons_fa = {
    'sunnyDay': chr(0xF0599),         # Weather Sunny
    'clearNight': chr(0xF0594),       # Weather Night
    'cloudyFoggyDay': chr(0xF0595),   # Weather Partially Cloudy
    'cloudyFoggyNight': chr(0xF0F31), # Weather Night Partially Cloudy
    'cloudy' : '\uf0c2',              # FA Cloud
    'rainyDay': chr(0x1F326),         # FA Cloud-Sun-Rain
    'rainyNight': '\ue323',           # FA Night Alt rain mix
    'snowyIcyDay': '\uf2dc',          # FA Snowflake
    'snowyIcyNight': '\uf2dc',        # FA Snowflake (reuse)
    'severe': '\ue317',               # FA Rain Wind
    'default': '\uf0c2',              # FA Cloud
    'feel' : '\uf2c9',                # FA Thermometer
    'wind' : chr(0xf059d),            # FA Weather Wind
    'visibility' : '\uf06e',          # FA Eye
    'humidity' : '\uf043',            # FA Humidity
    'rain' :  '\uf0e9'                # FA Weather Light raining
}

weather_icons_emoji = {
    'sunnyDay': '☀️',
    'clearNight': '🌙',
    'cloudyFoggyDay': '⛅',
    'cloudyFoggyNight':'☁️',
    'cloudy': '☁️',
    'rainyDay': '🌧️',
    'rainyNight': '🌧️',
    'snowyIcyDay': '❄️',
    'snowyIcyNight': '❄️',
    'severe': '🌩️',
    'default': '☁️',
    'feel': '️️🥵',
    'wind': '🌪️',
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
                name : str,
                icon : str,
                chance_of_rain: str,
                temperature: str = None,
                min: str = None,
                max: str = None
        ):
            self.moment = moment
            self.status = status
            self.name = name
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
    
    class AirQuality:
        class Color:
            def __init__(
                self,
                hex: str,
                r: str,
                g: str,
                b: str
            ):
                self.hex = hex
                self.r = r
                self.g = g
                self.b = b

        def __init__(
                self,
                title: str,
                acronym: str,
                aqi: str,
                color: Color,
                category: str,
                severity: str
        ):
            self.title = title
            self.acronym = acronym
            self.aqi = aqi
            self.color = WeatherForecast.AirQuality.Color(**color)
            self.category = category
            self.severity = severity

    def __init__(
        self,
        lang: str,
        location: str,
        status: str,
        status_code: str,
        icon: str,
        wind_speed: str,
        humidity: str,
        visibility: str,
        air_quality: AirQuality = None,
        temperature : Temperature = None,
        hourly_predictions: List[Prediction] = None,
        daily_predictions: List[Prediction] = None
    ):
        self.lang = lang
        self.location = location
        self.status = status
        self.status_code = status_code
        self.icon = icon
        self.wind_speed = wind_speed
        self.humidity = humidity
        self.visibility = visibility
        self.air_quality = WeatherForecast.AirQuality(**air_quality)
        self.temperature = WeatherForecast.Temperature(**temperature)
        self.hourly_predictions = [
            WeatherForecast.Prediction(**hourly_prediction) for hourly_prediction in (hourly_predictions or [])
        ]
        self.daily_predictions = [
            WeatherForecast.Prediction(**daily_predicion) for daily_predicion in (daily_predictions or [])
        ]

class WeatherForecastExtractor:

    def __init__(self, html_data):
        self.html_data = html_data

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
        return self.html_data("div[data-testid='WeatherDetailsListItem'] span[data-testid='Wind'] span").text().strip()

    def humidity(self):
        return self.html_data("span[data-testid='PercentageValue']").text()
    
    def temperature(self):
        current = self.html_data("span[data-testid='TemperatureValue']").eq(0).text()
        feel = self.html_data(
                "div[data-testid='FeelsLikeSection'] > span > span[data-testid='TemperatureValue']"
                ).text()
        max_temp = self.html_data(
                "div[data-testid='wxData'] > span[data-testid='TemperatureValue']"
                ).eq(0).text()
        min_temp = self.html_data(
                "div[data-testid='wxData'] > span[data-testid='TemperatureValue']"
                ).eq(1).text()

        return {
                "current": current,
                "feel": feel,
                "max": max_temp,
                "min": min_temp,
            }

    def visibility(self):
        return self.html_data("span[data-testid='VisibilityValue']").text()

    def air_quality(self):
        title = self.html_data("section[data-testid='AirQualityModule'] header h2").text()
        acronym = "".join(word[0] for word in title.split())
        category = self.html_data("span[data-testid='AirQualityCategory']").text()
        return {
            "title" : title,
            "acronym" : acronym,
            "color" : self.__aqi_color(),
            "category" : category,
            "aqi": self.html_data("text[data-testid='DonutChartValue']").text(),
            "severity": self.html_data("p[data-testid='AirQualitySeverity']").text()
        }

    def hourly_predictions(self):
        predictions = [
            self.__predictions(span)
                for span in self.html_data("section[data-testid='HourlyWeatherModule'] ul[data-testid='WeatherTable'] li")
            ]
        return predictions

    def daily_predictions(self):
        predictions = [
            self.__predictions(span, min_max = True)
                for span in self.html_data("section[data-testid='DailyWeatherModule'] ul[data-testid='WeatherTable'] li")
            ]
        return predictions

    def to_weather_forecast(self, lang: str) -> WeatherForecast:
        return WeatherForecast(
            lang=lang,
            location=self.location(),
            status=self.status(),
            status_code=self.status_code(),
            icon=self.icon(),
            wind_speed=self.wind_speed(),
            humidity=self.humidity(),
            visibility=self.visibility(),
            air_quality=self.air_quality(),
            temperature=self.temperature(),
            hourly_predictions=self.hourly_predictions(),
            daily_predictions=self.daily_predictions()
        )

    def __icon_predictions(self,name: str) -> str:
        status_code = skynames[name] if name in skynames else 'default'
        return weather_icons[status_code]
    
    def __aqi_color(self) -> dict:
        color_pattern = r"#([0-9A-Fa-f]{6})"        
        color_style_attribute = self.html_data("svg[data-testid='DonutChart'] circle:nth-of-type(2)").attr("style")
        match = re.search(color_pattern, color_style_attribute)
        color = f"#{match.group(1)}"
        hex_color = color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
        return {
            "hex" : color,
            "r" : r,
            "g" : g,
            "b" : b,
        }

    def __predictions(self, span, min_max: bool = False) -> dict:
        data = pq(span)("svg[data-testid='Icon']").attr('name')
        name = str(data) if data else 'cloudy'
        icon = self.__icon_predictions(name)
        temp_max = pq(span)("div[data-testid='SegmentHighTemp'] span[data-testid='TemperatureValue']").eq(0).text()
        temp_min = pq(span)("div[data-testid='SegmentHighTemp'] span[data-testid='TemperatureValue']").eq(1).text()
        temperature = pq(span)("span[data-testid='TemperatureValue']").text()
        return {
                'moment': pq(span)("h3 > span").text(),
                'min' : temp_min if min_max else None,
                'max' : temp_max if min_max else None,
                'temperature' : temperature if not min_max else None,
                'status' : pq(span)("svg").attr("name"),
                'name' :  name,
                'icon' : icon,
                'chance_of_rain' : pq(span)('div[data-testid="SegmentPrecipPercentage"] > span:nth-of-type(2)').contents()[1],
        }


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
    return forecast.to_weather_forecast(lang)

def format_weather(wf: WeatherForecast) -> str:
    hourly_predictions = "\n".join(
        f"{h.moment}\t{'\t' if len(h.moment) < 5 else ''}  {h.temperature}\t\t{h.icon} \t{weather_icons['rain']} {h.chance_of_rain}"
        for h in wf.hourly_predictions
    )
    daily_predictions = "\n".join(
        f"{h.moment}\t{'\t' if len(h.moment) < 5 else ''}{h.max}/<small>{h.min}</small> \t{h.icon}\t{weather_icons['rain']} {h.chance_of_rain}"
        for h in wf.daily_predictions
    )

    return f"""{wf.location}

<span size="xx-large">{wf.icon}\t\t{wf.temperature.current}</span>

{wf.status}
{wf.temperature.max}/<small>{wf.temperature.min}</small>   {weather_icons['feel']} {wf.temperature.feel}

{weather_icons['wind']} {wf.wind_speed} \t{weather_icons['humidity']} {wf.humidity}
{weather_icons['visibility']} {wf.visibility}\t {wf.air_quality.acronym} {wf.air_quality.aqi} <span color="{wf.air_quality.color.hex}">{wf.air_quality.category}</span>

{hourly_predictions}

{daily_predictions}
"""

def waybar(wf: WeatherForecast) -> Dict:
    return {
        "text": f"{wf.icon} {wf.temperature.current}",
        "alt": wf.status,
        "tooltip": format_weather(wf),
        "class": wf.status_code,
    }

def console(wf: WeatherForecast) -> str:
    hex_color = wf.air_quality.color.hex
    r,g,b = wf.air_quality.color.r, wf.air_quality.color.g, wf.air_quality.color.b
    weather = ("\n"+format_weather(wf)
            .replace("<small>","").replace("</small>","")
            .replace('<span size="xx-large">',"\033[1m").replace("</span>","\033[0m")
            .replace(f'<span color="{hex_color}">',f"\033[38;2;{r};{g};{b}m")
    )
    return re.sub(r'(?: +\t|\t+ *|\t{2,})', '\t',weather)


def console_persist(weather_forecast: WeatherForecast) -> None:
    while True:
        forecast = console(weather_forecast)
        print(forecast)
        sleep(600) # every 10 minutes
        line_count = len(forecast.splitlines()) + 1
        # Clear all the lines and print a new weather forecast
        LINE_UP = '\033[1A'
        LINE_CLEAR = '\x1b[2K'
        for _ in range(line_count):
            print(LINE_UP, end=LINE_CLEAR)

if __name__ == "__main__":
    ## Get current locale, or use the default one
    parser = argparse.ArgumentParser(description="Weather forecast grabber from weather.com")
    parser.add_argument("--location", "-l", type=str, help="64-character-hex code for location obtained from weather.com")
    parser.add_argument("--lang", "-L", type=str, help="Language (pt-BR, fr-FR, etc.), If not set, uses the machine one.")
    parser.add_argument("--output", "-o", type=str, choices=['console','json','waybar'], default='console', help="Output format. console, json or waybar")
    parser.add_argument("--persist", "-p",action='store_true', default=False, help="Keep waybar open instead of exiting after execution. Does only makes sense for --output=console")
    parser.add_argument("--icons", "-i", type=str, choices=['fa','emoji'], default='emoji', help="Icon set. 'fa' for Font-Awesome, or 'emoji'")

    args = parser.parse_args()

    weather_icons = weather_icons_emoji if args.icons == 'emoji' else weather_icons_fa
    lang = args.lang if args.lang else os.getenv("LANG","en_IL.UTF-8").split(".")[0].replace("_","-")
    weather_id = args.location if args.location else os.getenv('WEATHER_LOCATION_ID')
    weather_forecast = get_weather_forecast(lang=lang, weather_id=weather_id)
    if args.output == 'console':
        if args.persist:
            console_persist(weather_forecast)
        else:
            print(console(weather_forecast))
    elif args.output == 'waybar':
        waybar_data = waybar(weather_forecast)
        print(json.dumps(waybar_data))
    else:
        print(json.dumps(weather_forecast,default=serializer, indent=2))