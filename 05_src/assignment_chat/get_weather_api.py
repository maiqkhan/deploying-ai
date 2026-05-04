import requests
from datetime import date, timedelta
from statistics import mean
from openai import OpenAI
import os
from dotenv import load_dotenv
from utils import get_client
from fastapi import FastAPI, Query
from pydantic import BaseModel
import uvicorn
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()


class WeatherResponse(BaseModel):
    city: str
    travel_date: date
    weather_response: str

app = FastAPI(title="Weather Assistant")

WMO_DESCRIPTIONS = {
    0:  "clear sky",
    1:  "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    80: "light showers", 81: "moderate showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail",
}

def get_city_coordinates(city: str) -> tuple[float, float, str]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(url, params={"name": city, "count": 1, "language": "en"})
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city}")
    r = results[0]
    return r["latitude"], r["longitude"], r["name"]


def get_current_weather(city: str) -> dict:
    lat, lon, name = get_city_coordinates(city)
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "current": [
                "temperature_2m", "weathercode",
                "windspeed_10m", "precipitation",
            ],
            "timezone": "auto",
        },
    )
    resp.raise_for_status()
    c = resp.json()["current"]
    return {
        "city":        name,
        "data_type":   "current",
        "date":        date.today().isoformat(),
        "temperature": c["temperature_2m"],
        "condition":   WMO_DESCRIPTIONS.get((c["weathercode"]), f"weather code {c["weathercode"]}" ),
        "wind_kmh":    c["windspeed_10m"],
        "precip_mm":   c["precipitation"],
        "note":        "Live conditions right now.",
    }

def get_forecast_weather(city: str, travel_date: date) -> dict:
    lat, lon, name = get_city_coordinates(city)
    days_needed = (travel_date - date.today()).days + 1   # +1 so today=day 0
 
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "daily": [
                "temperature_2m_max", "temperature_2m_min",
                "weathercode", "precipitation_sum", "windspeed_10m_max",
            ],
            "forecast_days": min(days_needed, 16),
            "timezone": "auto",
        },
    )
    resp.raise_for_status()
    daily = resp.json()["daily"]
 
    # find the index matching travel_date
    target = travel_date.isoformat()
    try:
        idx = daily["time"].index(target)
    except ValueError:
        raise ValueError(f"Forecast doesn't reach {target} — too far out?")
 
    return {
        "city":        name,
        "data_type":   "forecast",
        "date":        target,
        "temp_max":    daily["temperature_2m_max"][idx],
        "temp_min":    daily["temperature_2m_min"][idx],
        "condition":   WMO_DESCRIPTIONS.get(daily["weathercode"][idx], f"weather code {daily["weathercode"][idx]}" ),
        "wind_kmh":    daily["windspeed_10m_max"][idx],
        "precip_mm":   daily["precipitation_sum"][idx],
        "note":        f"16-day forecast for {target}. Treat as an estimate.",
    }

def fetch_year(lat, lon, year, month):
    last_day = (
        date(year, 12, 31)
        if month == 12
        else date(year, month + 1, 1) - timedelta(days=1)
    )
    resp = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat, "longitude": lon,
            "start_date": date(year, month, 1).isoformat(),
            "end_date":   last_day.isoformat(),
            "daily": [
                "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "windspeed_10m_max",
            ],
            "timezone": "auto",
        },
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("error"):
        raise ValueError(f"Archive API error for {year}/{month}: {body.get('reason')}")
    return body["daily"]

def get_climate_average(city: str, month: int) -> dict:
    lat, lon, name = get_city_coordinates(city)
    current_year = date.today().year
    years = range(current_year - 5, current_year - 1)

    temp_maxes, temp_mins, precip_totals, wind_maxes = [], [], [], []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_year, lat, lon, year, month): year for year in years}
        for future in as_completed(futures):
            d = future.result()
            temp_maxes    += [v for v in d["temperature_2m_max"] if v is not None]
            temp_mins     += [v for v in d["temperature_2m_min"] if v is not None]
            precip_totals += [v for v in d["precipitation_sum"]  if v is not None]
            wind_maxes    += [v for v in d["windspeed_10m_max"]  if v is not None]

    if not temp_maxes:
        raise ValueError(f"No historical data returned for month {month}")

    month_name = date(2000, month, 1).strftime("%B")
    return {
        "city":             name,
        "data_type":        "climate_average",
        "month":            month_name,
        "avg_temp_max":     round(mean(temp_maxes), 1),
        "avg_temp_min":     round(mean(temp_mins), 1),
        "avg_daily_precip": round(mean(precip_totals), 1),
        "avg_wind_kmh":     round(mean(wind_maxes), 1),
        "note": (
            f"Historical averages for {month_name} based on the last 5 years. "
            "Not a forecast — typical conditions only."
        ),
    }

def get_travel_weather(city: str, travel_date: date) -> dict:
    
    days_out = (travel_date - date.today()).days
    print(days_out)
 
    if days_out <= 0:
        print("using current weather function")
        return get_current_weather(city)
    elif days_out <= 16:
        print("using forecast weather function")
        return get_forecast_weather(city, travel_date)
    else:
        print("using average weather function")
        return get_climate_average(city, travel_date.month)
        

@app.get("/weather", response_model=WeatherResponse)
def provide_travel_weather_details(city: str = Query(..., description="Destination city, e.g. 'Tokyo'"), 
                                   travel_date: date = Query(..., description="Travel date in YYYY-MM-DD format")):
    
    
    client = get_client(dev=False)
    
    system_prompt = """You are a weather assistant providing travellers weather details for the place you are visiting. 
                        Use only the weather json input and no external information to generate a message that can be returned to the traveller.
                        The tone of the response should be conversational, and the response should be succinct."""
    
    travel_data = get_travel_weather(city, travel_date)

    user_prompt = f"""
                      Please, provide a response based on the following weather details:
                          {travel_data}                    
                    """

    
    response = client.responses.create(
            #model = 'gpt-4o',
            model = 'gpt-4o-mini', # depending on the tier we have available, we might need to update the model to be used
            instructions = system_prompt,
            input = user_prompt,
    )

    print(response.output_text)

    return WeatherResponse(city=city, travel_date=travel_date, weather_response=response.output_text)


if __name__ == "__main__":
    
    uvicorn.run("get_weather_api:app", host="0.0.0.0", port=8005, reload=True)

