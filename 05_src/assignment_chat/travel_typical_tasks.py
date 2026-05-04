import datetime
from zoneinfo import ZoneInfo
from fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("TravelAssistant")

@mcp.tool()
def calculate_trip_costs(flights: float, accommodation: float, food_per_day: float, duration_days: int, activities: float = 0.0) -> str:
    """
    Calculates the total estimated cost of a trip.
    """
    total_food = food_per_day * duration_days
    grand_total = flights + accommodation + total_food + activities
    
    return (f"Trip Total: ${grand_total:,.2f}\n"
            f"Breakdown: Flights (${flights}), Lodging (${accommodation}), "
            f"Food (${total_food}), Activities (${activities})")

@mcp.tool()
def currency_conversion(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts an amount from one currency to another using (mocked) live rates.
    """
    # In a production app, you'd fetch these from an API like ExchangeRate-API
    rates = {
        "USD": 1.0,      # US Dollar
        "EUR": 0.94,     # Euro
        "JPY": 152.40,   # Japanese Yen
        "GBP": 0.81,     # British Pound
        "CNY": 7.24,     # Chinese Yuan
        "AUD": 1.53,     # Australian Dollar
        "CAD": 1.37,     # Canadian Dollar
        "CHF": 0.91,     # Swiss Franc
        "HKD": 7.82,     # Hong Kong Dollar
        "SGD": 1.35,     # Singapore Dollar
        "SEK": 10.85,    # Swedish Krona
        "KRW": 1375.0,   # South Korean Won
        "NOK": 10.92,    # Norwegian Krone
        "NZD": 1.68,     # New Zealand Dollar
        "INR": 83.50,    # Indian Rupee
        "MXN": 17.10,    # Mexican Peso
        "TWD": 32.40,    # New Taiwan Dollar
        "BRL": 5.15,     # Brazilian Real
        "ZAR": 18.60,    # South African Rand
        "TRY": 32.50     # Turkish Lira
    }
    
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    
    if from_curr not in rates or to_curr not in rates:
        return f"Error: Currency {from_curr} or {to_curr} not supported."
    
    # Convert to USD base then to target
    usd_amount = amount / rates[from_curr]
    converted_amount = usd_amount * rates[to_curr]
    
    return f"{amount} {from_curr} is approximately {converted_amount:.2f} {to_curr}"

@mcp.tool()
def time_zone_differences(city_a_timezone: str, city_b_timezone: str) -> str:
    """
    Calculates the time difference between two timezones (e.g., 'America/New_York', 'Europe/London').
    """
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        tz_a = ZoneInfo(city_a_timezone)
        tz_b = ZoneInfo(city_b_timezone)
        
        time_a = now.astimezone(tz_a)
        time_b = now.astimezone(tz_b)
        
        # Calculate offset difference in hours
        offset_a = tz_a.utcoffset(now).total_seconds() / 3600
        offset_b = tz_b.utcoffset(now).total_seconds() / 3600
        diff = offset_b - offset_a
        
        return (f"Time in {city_a_timezone}: {time_a.strftime('%I:%M %p')}\n"
                f"Time in {city_b_timezone}: {time_b.strftime('%I:%M %p')}\n"
                f"Difference: {diff:+} hours from {city_a_timezone}")
    except Exception as e:
        return f"Error calculating timezone difference: {str(e)}"

if __name__ == "__main__":
    mcp.run(
     transport="http", 
        host="0.0.0.0", 
        port=8001
    )