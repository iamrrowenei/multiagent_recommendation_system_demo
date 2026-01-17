"""
Multi-Service Agent System for Event Recommendations

SYSTEM OVERVIEW:
================
This is a sophisticated multi-agent system that combines weather data, event information,
and AI-powered reasoning to provide personalized event recommendations.

ARCHITECTURE & DESIGN:
======================

1. MULTI-AGENT APPROACH:
   - WeatherAgent: Handles weather API calls and weather-based suggestions
   - EventAgent: Manages database queries and event filtering
   - RecommendationAgent: Uses OpenAI GPT-4 to generate intelligent recommendations
   - CoordinatorAgent: Orchestrates all agents and combines their outputs

2. KEY DESIGN PRINCIPLES:
   - Separation of Concerns: Each agent has a specific responsibility
   - Modular Design: Agents can be updated independently
   - Context-Aware: Combines multiple data sources for holistic recommendations
   - User-Centric: Focuses on practical advice (what to wear, how to travel)

3. DATA FLOW:
   User Request → CoordinatorAgent → [WeatherAgent + EventAgent] → RecommendationAgent → Response
   
   a) CoordinatorAgent receives user request (location, date, filters)
   b) WeatherAgent fetches current weather data from API
   c) WeatherAgent generates clothing and transport suggestions
   d) EventAgent queries database with filters (type, time, price)
   e) EventAgent groups events by time of day
   f) RecommendationAgent combines all data and generates AI recommendations
   g) Final response includes weather box + AI recommendations

4. FILTERING CAPABILITIES:
   - Event Type: indoor/outdoor (weather-dependent)
   - Time of Day: morning (6-12), afternoon (12-18), evening (18+)
   - Price Range: Filter by maximum budget
   - Combined: Multiple filters can be applied simultaneously

5. WEATHER INTEGRATION:
   - Real-time weather from WeatherAPI.com
   - Temperature-based clothing suggestions
   - Condition-based transport recommendations
   - Indoor/outdoor event suitability assessment

6. AI RECOMMENDATION ENGINE:
   - Uses OpenAI GPT-4 for natural language recommendations
   - Provides explicit reasoning for each suggestion
   - Considers: weather, timing, price, availability, user experience
   - Structures output: Weather Summary → Recommendations → Schedule → Advice

7. VISUAL ENHANCEMENTS:
   - Weather icons based on conditions (☀️ ⛅ 🌧️ ❄️)
   - Temperature icons based on ranges (🥶 ❄️ 😊 😎 🥵)
   - Event type icons (🏠 indoor, 🌳 outdoor)
   - Time period icons (🌅 morning, ☀️ afternoon, 🌙 evening)
   - Availability status (✅ ⚠️ 🔴 ❌)
   - Formatted boxes with borders for structured display

TECHNICAL STACK:
================
- OpenAI API: GPT-4 for intelligent recommendations
- WeatherAPI: Real-time weather data
- SQLite: Event database storage
- Python: Core implementation language
- python-dotenv: Environment variable management

USAGE EXAMPLE:
==============
coordinator = CoordinatorAgent(WEATHER_API_KEY, OPENAI_API_KEY)

# Get all events for a date
recommendations = coordinator.get_recommendations("Singapore", "2026-02-15")

# Filter by time of day
recommendations = coordinator.get_recommendations("Singapore", "2026-02-15", time_of_day="evening")

# Filter by price
recommendations = coordinator.get_recommendations("Singapore", "2026-02-15", max_price=20)

# Filter by event type
recommendations = coordinator.get_recommendations("Singapore", "2026-02-15", event_type="indoor")

# Combine filters
recommendations = coordinator.get_recommendations(
    "Singapore", "2026-02-15", 
    event_type="outdoor", 
    time_of_day="morning", 
    max_price=15
)
"""

import openai 
import requests 
import sqlite3 
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This keeps sensitive API keys secure and out of source code
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY') 
 
class WeatherAgent:
    """
    Weather Agent - Handles weather data retrieval and weather-based suggestions.
    
    RESPONSIBILITIES:
    -----------------
    1. Fetch real-time weather data from WeatherAPI.com
    2. Generate clothing suggestions based on temperature and conditions
    3. Provide transport recommendations based on weather
    
    DESIGN RATIONALE:
    -----------------
    - Uses external API for real-time accuracy
    - Provides practical, actionable advice (not just raw data)
    - Considers both temperature AND conditions for comprehensive suggestions
    
    API: WeatherAPI.com (https://www.weatherapi.com/)
    - Free tier: 1 million calls/month
    - Current weather endpoint for real-time data
    - Returns: temperature, feels_like, humidity, wind, conditions
    """
    
    def __init__(self, api_key):
        """
        Initialize WeatherAgent with API key.
        
        Args:
            api_key (str): WeatherAPI.com API key from environment variables
        """
        self.api_key = api_key 
     
    def get_weather(self, location, date):
        """
        Fetch current weather data for a location.
        
        NOTE: Currently uses 'current' weather endpoint as we're doing same-day
        recommendations. For future dates, could switch to forecast endpoint.
        
        Args:
            location (str): City name or coordinates (e.g., "Singapore", "London")
            date (str): Event date (YYYY-MM-DD) - currently not used, prepared for forecast
        
        Returns:
            dict: Weather data including temperature, condition, humidity, wind
                  Structure: {'current': {'temp_c': float, 'condition': {...}, ...}}
        
        Raises:
            Exception: If API call fails (network error, invalid key, location not found)
        """
        # Use current weather since we're dealing with same-day recommendations 
        url = f"http://api.weatherapi.com/v1/current.json" 
        params = { 
            "key": self.api_key, 
            "q": location, 
            "aqi": "no"  # Air quality not needed for our use case
        } 
        try: 
            response = requests.get(url, params=params) 
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            return response.json() 
        except requests.exceptions.RequestException as e: 
            raise Exception(f"Weather API error: {str(e)}")
    
    def get_clothing_suggestion(self, temperature, condition):
        """
        Generate what-to-wear suggestions based on weather.
        
        LOGIC:
        ------
        1. Temperature-based suggestions:
           - <10°C: Heavy winter clothing
           - 10-15°C: Light jacket weather
           - 15-25°C: Comfortable, light clothing
           - >25°C: Hot weather gear with sun protection
        
        2. Condition-based additions:
           - Rain: Add umbrella/raincoat
           - Sun/Clear: Add sunglasses
        
        Args:
            temperature (float): Temperature in Celsius
            condition (str): Weather condition text (e.g., "Partly cloudy", "Rain")
        
        Returns:
            list[str]: List of clothing/accessory suggestions
        """
        suggestions = []
        
        # Temperature-based suggestions
        if temperature < 10:
            suggestions.append("heavy jacket or coat")
            suggestions.append("warm layers")
            suggestions.append("scarf and gloves")
        elif temperature < 15:
            suggestions.append("light jacket or sweater")
            suggestions.append("long sleeves")
        elif temperature < 25:
            suggestions.append("light clothing")
            suggestions.append("comfortable shirt or t-shirt")
        else:
            suggestions.append("light, breathable clothing")
            suggestions.append("sunscreen and hat")
        
        # Condition-based suggestions
        condition_lower = condition.lower()
        if any(word in condition_lower for word in ['rain', 'drizzle', 'shower']):
            suggestions.append("umbrella or raincoat")
            suggestions.append("waterproof shoes")
        elif 'sun' in condition_lower or 'clear' in condition_lower:
            suggestions.append("sunglasses")
        
        return suggestions
    
    def get_transport_suggestion(self, temperature, condition):
        """
        Suggest optimal transport method based on weather.
        
        LOGIC:
        ------
        - Heavy rain/storms: Covered transport recommended
        - Hot weather (>30°C): Air-conditioned transport preferred
        - Cold weather (<15°C): Warm transport options
        - Pleasant weather: All transport methods suitable
        
        Args:
            temperature (float): Temperature in Celsius
            condition (str): Weather condition text
        
        Returns:
            str: Transport recommendation with reasoning
        """
        condition_lower = condition.lower()
        
        if any(word in condition_lower for word in ['rain', 'storm', 'heavy']):
            return "Use covered transport (taxi, car, or covered walkways). Avoid motorcycles and long walks."
        elif any(word in condition_lower for word in ['hot', 'sun']) and temperature > 30:
            return "Use air-conditioned transport when possible. Stay hydrated if walking."
        elif temperature < 15:
            return "Dress warmly if walking or using public transport. Consider warmer transport options."
        else:
            return "Weather is pleasant for walking or any form of transport."
 
class EventAgent:
    """
    Event Agent - Manages event database queries and data organization.
    
    RESPONSIBILITIES:
    -----------------
    1. Query events database with multiple filter criteria
    2. Group events by time of day for structured recommendations
    3. Find alternative dates for events (future enhancement)
    
    DESIGN RATIONALE:
    -----------------
    - SQL-based filtering for efficient queries
    - Flexible filter combinations (type + time + price)
    - Time-based grouping for better UX (plan your day)
    - Prepared for expansion (alternative dates, recurring events)
    
    DATABASE: SQLite (events.db)
    - Lightweight, serverless, zero-configuration
    - Schema defined in database.py
    """
    
    def get_events(self, date, event_type=None, time_of_day=None, max_price=None):
        """
        Query events with flexible filtering options.
        
        FILTERING LOGIC:
        ----------------
        1. Base: All events on specified date
        2. Type filter: 'indoor' OR 'outdoor' (weather-dependent)
        3. Time filter: 
           - morning: 06:00-12:00
           - afternoon: 12:00-18:00
           - evening: 18:00+
        4. Price filter: price_min <= max_price (inclusive of free events)
        
        SQL APPROACH:
        -------------
        - Dynamic query building based on provided filters
        - Uses parameterized queries to prevent SQL injection
        - Filters applied with AND logic (all must match)
        
        Args:
            date (str): Event date in YYYY-MM-DD format
            event_type (str, optional): 'indoor' or 'outdoor' filter
            time_of_day (str, optional): 'morning', 'afternoon', or 'evening'
            max_price (float, optional): Maximum price threshold
        
        Returns:
            list[tuple]: List of event records matching criteria
                        Each tuple: (id, name, type, description, location, date,
                                   start_time, end_time, price_min, price_max,
                                   capacity, available_spots)
        
        Raises:
            Exception: If database query fails
        """
        conn = sqlite3.connect('events.db') 
        c = conn.cursor() 
         
        try:
            # Start with base query for the date
            query = 'SELECT * FROM events WHERE date = ?'
            params = [date]
            
            # Add event type filter if specified
            if event_type:
                query += ' AND type = ?'
                params.append(event_type)
            
            # Add price filter if specified (checks minimum price)
            if max_price is not None:
                query += ' AND price_min <= ?'
                params.append(max_price)
            
            # Add time of day filter based on start_time
            if time_of_day:
                if time_of_day == 'morning':
                    query += ' AND start_time >= "06:00" AND start_time < "12:00"'
                elif time_of_day == 'afternoon':
                    query += ' AND start_time >= "12:00" AND start_time < "18:00"'
                elif time_of_day == 'evening':
                    query += ' AND start_time >= "18:00"'
            
            c.execute(query, params)
            events = c.fetchall()
            return events
        except sqlite3.Error as e: 
            raise Exception(f"Database error: {str(e)}") 
        finally: 
            conn.close()
    
    def get_alternative_dates(self, event_name, original_date):
        """
        Find alternative dates for recurring events.
        
        USE CASE: If weather is bad for outdoor event, suggest other dates
        
        Args:
            event_name (str): Name of the event to search for
            original_date (str): Date to exclude from results
        
        Returns:
            list[str]: List of alternative dates (YYYY-MM-DD format)
        """
        conn = sqlite3.connect('events.db')
        c = conn.cursor()
        
        try:
            c.execute('SELECT date FROM events WHERE name = ? AND date != ?', (event_name, original_date))
            dates = [row[0] for row in c.fetchall()]
            return dates
        except sqlite3.Error as e:
            return []  # Return empty list on error
        finally:
            conn.close()
    
    def group_events_by_time(self, events):
        """
        Organize events into morning/afternoon/evening groups.
        
        PURPOSE: Helps users plan their day with structured schedule
        
        TIME PERIODS:
        -------------
        - Morning: 06:00 - 12:00 (breakfast, early activities)
        - Afternoon: 12:00 - 18:00 (lunch, midday activities)
        - Evening: 18:00+ (dinner, night activities)
        
        Args:
            events (list[tuple]): List of event tuples from database
        
        Returns:
            dict: {
                'morning': [events],
                'afternoon': [events],
                'evening': [events]
            }
        """
        grouped = {
            'morning': [],
            'afternoon': [],
            'evening': []
        }
        
        for event in events:
            start_time = event[6]  # start_time is at index 6 in tuple
            hour = int(start_time.split(':')[0])  # Extract hour from HH:MM
            
            # Categorize based on start hour
            if 6 <= hour < 12:
                grouped['morning'].append(event)
            elif 12 <= hour < 18:
                grouped['afternoon'].append(event)
            else:
                grouped['evening'].append(event)
        
        return grouped
 
class RecommendationAgent:
    """
    Recommendation Agent - AI-powered recommendation generation using OpenAI GPT-4.
    
    RESPONSIBILITIES:
    -----------------
    1. Generate weather display with icons and formatting
    2. Create context-rich prompts for AI model
    3. Produce structured, explicit recommendations
    4. Combine weather data + events into cohesive advice
    
    DESIGN APPROACH:
    ----------------
    - Visual Enhancement: Icons make information scannable
    - Explicit Instructions: AI receives clear formatting requirements
    - Context Aggregation: Weather + Events + Availability in one view
    - Structured Output: Consistent format (Weather → Recommendations → Schedule → Advice)
    
    AI MODEL: OpenAI GPT-4
    - Chosen for: Superior reasoning, contextual understanding, structured output
    - Alternative: GPT-3.5-turbo for faster/cheaper responses
    
    ICON SYSTEM:
    ------------
    Weather: ☀️ sunny, ⛅ partly cloudy, ☁️ cloudy, 🌧️ rain, ⛈️ storm, ❄️ snow, 🌫️ fog
    Temperature: 🥶 freezing, ❄️ cold, 😊 cool, ☺️ comfortable, 😎 warm, 🥵 hot
    Events: 🏠 indoor, 🌳 outdoor
    Time: 🌅 morning, ☀️ afternoon, 🌙 evening
    Status: ✅ available, ⚠️ limited, 🔴 almost full, ❌ sold out
    """
    
    def __init__(self, openai_api_key):
        """
        Initialize RecommendationAgent with OpenAI API key.
        
        Args:
            openai_api_key (str): OpenAI API key from environment variables
        """
        self.api_key = openai_api_key 
        openai.api_key = openai_api_key
    
    def get_weather_icon(self, condition, temperature):
        """
        Select appropriate weather icon based on conditions.
        
        ICON LOGIC:
        -----------
        - Prioritizes specific conditions (rain > clouds > clear)
        - Uses descriptive emojis for instant understanding
        - Falls back to default if condition unknown
        
        Args:
            condition (str): Weather condition text (e.g., "Partly cloudy")
            temperature (float): Temperature in Celsius (for context)
        
        Returns:
            str: Weather emoji icon
        """
        condition_lower = condition.lower()
        
        # Weather condition icons (ordered by priority)
        if 'sun' in condition_lower or 'clear' in condition_lower:
            return '☀️'
        elif 'partly cloudy' in condition_lower or 'partly cloud' in condition_lower:
            return '⛅'
        elif 'cloudy' in condition_lower or 'overcast' in condition_lower:
            return '☁️'
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return '🌧️'
        elif 'storm' in condition_lower or 'thunder' in condition_lower:
            return '⛈️'
        elif 'snow' in condition_lower:
            return '❄️'
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return '🌫️'
        else:
            return '🌤️'  # Default/mixed conditions
    
    def get_temperature_icon(self, temperature):
        """
        Select emoji icon based on temperature ranges.
        
        TEMPERATURE RANGES:
        -------------------
        <10°C: 🥶 Freezing - Heavy winter clothing needed
        10-15°C: ❄️ Cold - Jacket recommended
        15-20°C: 😊 Cool/Pleasant - Light layers
        20-25°C: ☺️ Comfortable - Normal clothing
        25-30°C: 😎 Warm - Light, breathable clothing
        >30°C: 🥵 Hot - Sun protection essential
        
        Args:
            temperature (float): Temperature in Celsius
        
        Returns:
            str: Temperature emoji icon
        """
        if temperature < 10:
            return '🥶'  # Freezing
        elif temperature < 15:
            return '❄️'  # Cold
        elif temperature < 20:
            return '😊'  # Cool/Pleasant
        elif temperature < 25:
            return '☺️'  # Comfortable
        elif temperature < 30:
            return '😎'  # Warm
        else:
            return '🥵'  # Hot
    
    def format_weather_display(self, weather_data, location, clothing_suggestions, transport_suggestion):
        """
        Create visually formatted weather information box.
        
        DESIGN FEATURES:
        ----------------
        - Box drawing characters for professional look
        - Icons for quick visual scanning
        - Grouped information (conditions → clothing → transport)
        - Explicit temperature with descriptive label
        
        SECTIONS:
        ---------
        1. Header: Weather icons and title
        2. Conditions: Temperature, feels-like, condition, humidity, wind
        3. Clothing: What to wear based on weather
        4. Transport: How to get around based on weather
        
        Args:
            weather_data (dict): Weather API response
            location (str): City/location name
            clothing_suggestions (list[str]): Clothing recommendations
            transport_suggestion (str): Transport advice
        
        Returns:
            str: Formatted weather display with box borders and icons
        """
        if 'current' not in weather_data:
            return "Weather data unavailable\n\n"
        
        # Extract weather data
        weather_condition = weather_data['current']['condition']['text']
        temperature = weather_data['current']['temp_c']
        humidity = weather_data['current'].get('humidity', 'N/A')
        wind_kph = weather_data['current'].get('wind_kph', 'N/A')
        feels_like = weather_data['current'].get('feelslike_c', temperature)
        
        # Get appropriate icons
        weather_icon = self.get_weather_icon(weather_condition, temperature)
        temp_icon = self.get_temperature_icon(temperature)
        
        # Temperature description mapping
        if temperature < 10:
            temp_desc = "Very Cold"
        elif temperature < 15:
            temp_desc = "Cold"
        elif temperature < 20:
            temp_desc = "Cool"
        elif temperature < 25:
            temp_desc = "Pleasant"
        elif temperature < 30:
            temp_desc = "Warm"
        elif temperature < 35:
            temp_desc = "Hot"
        else:
            temp_desc = "Very Hot"
        
        # Format display with box drawing characters
        weather_display = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    {weather_icon}  WEATHER CONDITIONS  {weather_icon}                      ║
╠══════════════════════════════════════════════════════════════════╣
║  📍 Location: {location}                                           
║  🌡️  Temperature: {temperature}°C {temp_icon} ({temp_desc})
║  🌡️  Feels Like: {feels_like}°C
║  🌤️  Condition: {weather_condition}
║  💧 Humidity: {humidity}%
║  💨 Wind Speed: {wind_kph} km/h
╠══════════════════════════════════════════════════════════════════╣
║  👔 WHAT TO WEAR:
║     • {chr(10).join('     • ' + item for item in clothing_suggestions).replace('     • ', '', 1)}
╠══════════════════════════════════════════════════════════════════╣
║  🚗 TRANSPORT ADVICE:
║     {transport_suggestion}
╚══════════════════════════════════════════════════════════════════╝
"""
        return weather_display
     
    def generate_recommendation(self, weather_data, events, grouped_events, clothing_suggestions, 
                                transport_suggestion, location, date):
        """
        Generate AI-powered event recommendations combining all context.
        
        PROCESS FLOW:
        -------------
        1. Format weather display with icons
        2. Build events context grouped by time
        3. Add availability indicators and pricing
        4. Create comprehensive prompt for AI
        5. Call OpenAI GPT-4 with structured instructions
        6. Combine weather box + AI recommendations
        
        AI PROMPT ENGINEERING:
        ----------------------
        - Explicit instructions for structured output
        - Includes all context (weather + events + availability)
        - Requests specific sections (Weather Summary, Recommendations, Schedule, etc.)
        - Emphasizes explicit temperature mentions and reasoning
        
        CONTEXT PROVIDED TO AI:
        -----------------------
        1. Weather: Temperature, condition, feels-like, humidity, wind
        2. Clothing: What to wear
        3. Transport: How to get around
        4. Events: Grouped by time with full details
        5. Availability: Booking urgency indicators
        6. Pricing: Budget information
        
        OUTPUT STRUCTURE:
        -----------------
        1. Weather box (visual, with icons)
        2. Weather Summary (AI-generated, explicit)
        3. Top Recommendations (with reasoning)
        4. Time-Based Schedule (morning/afternoon/evening)
        5. Weather-Specific Advice (practical tips)
        6. Booking Urgency (which events to book now)
        
        Args:
            weather_data (dict): Weather API response
            events (list): All events matching filters
            grouped_events (dict): Events grouped by time of day
            clothing_suggestions (list): What to wear
            transport_suggestion (str): Transport advice
            location (str): City/location name
            date (str): Event date
        
        Returns:
            str: Complete formatted recommendation including weather box and AI response
        
        Raises:
            Exception: If OpenAI API call fails
        """
        try: 
            # Build visual weather display
            weather_display = self.format_weather_display(
                weather_data, location, clothing_suggestions, transport_suggestion
            )
            
            # Get temperature for context
            temperature = weather_data['current']['temp_c'] if 'current' in weather_data else None
            weather_condition = weather_data['current']['condition']['text'] if 'current' in weather_data else "Unknown"
            
            # Build events context grouped by time
            # Uses box drawing characters for visual structure
            events_context = "\n╔══════════════════════════════════════════════════════════════════╗\n"
            events_context += "║              📅 EVENTS GROUPED BY TIME OF DAY                    ║\n"
            events_context += "╚══════════════════════════════════════════════════════════════════╝\n"
            
            for time_period, time_events in grouped_events.items():
                if time_events:
                    # Time period icons
                    if time_period == 'morning':
                        period_icon = '🌅'
                    elif time_period == 'afternoon':
                        period_icon = '☀️'
                    else:
                        period_icon = '🌙'
                    
                    events_context += f"\n{period_icon} {time_period.upper()}\n"
                    events_context += "─" * 70 + "\n"
                    
                    for event in time_events:
                        # event structure: id, name, type, description, location, date, start_time, 
                        # end_time, price_min, price_max, capacity, available_spots
                        name = event[1]
                        event_type = event[2]
                        description = event[3]
                        event_location = event[4]
                        start_time = event[6]
                        end_time = event[7]
                        price_min = event[8]
                        price_max = event[9]
                        capacity = event[10]
                        available = event[11]
                        
                        # Event type icon
                        type_icon = '🏠' if event_type == 'indoor' else '🌳'
                        
                        # Format price
                        if price_min == 0 and price_max == 0:
                            price_str = "FREE 🎉"
                        elif price_min == price_max:
                            price_str = f"${price_min:.0f}"
                        else:
                            price_str = f"${price_min:.0f}-${price_max:.0f}"
                        
                        # Availability status
                        availability_pct = (available / capacity * 100) if capacity > 0 else 0
                        if availability_pct > 50:
                            avail_status = "✅ Good availability"
                        elif availability_pct > 20:
                            avail_status = "⚠️ Limited spots"
                        elif availability_pct > 0:
                            avail_status = "🔴 Almost full - BOOK NOW!"
                        else:
                            avail_status = "❌ SOLD OUT"
                        
                        events_context += f"""
  {type_icon} {name} ({event_type.upper()})
     {description}
     📍 {event_location}
     ⏰ {start_time} - {end_time}
     💰 {price_str}
     👥 {avail_status} ({available}/{capacity} spots available)
"""
            
            # Create the prompt
            full_context = f"""{weather_display}

{events_context}

IMPORTANT: Provide CONCISE and BULLETED recommendations:

TOP RECOMMENDATIONS:
- List each recommended event with brief reasoning
- Keep each bullet point to 1-2 sentences maximum
- Mention booking urgency if relevant (limited spots)
- Include why it's good based on weather/time/price
- Use exact event names and times

Format: Simple bullet points, no long paragraphs or elaborate sections."""
             
            response = openai.ChatCompletion.create( 
                model="gpt-4", 
                messages=[ 
                    {"role": "system", "content": """You are an event recommender. Provide CONCISE, bulleted recommendations.

RULES:
1. Use simple bullet points (•) for each event
2. Each recommendation: 1-2 sentences MAX
3. Format: Event name, time, brief reason why
4. Mention if booking urgency (limited spots)
5. Consider weather for indoor vs outdoor
6. Be direct and concise - no long explanations
7. Use emojis sparingly (only for urgency 🔴 or free 🎉)

Example format:
• Morning Yoga (6:00-7:30) - Great outdoor start to the day, only 8 spots left
• Art Exhibition (10:00-18:00) - Indoor option if weather turns, free entry
• Summer Concert (18:00-22:00) - Evening outdoor event, 120 spots available

Keep it SHORT and ACTIONABLE."""}, 
                    {"role": "user", "content": full_context} 
                ] 
            ) 
            
            # Combine weather display with AI recommendations
            final_response = weather_display + "\n" + response.choices[0].message.content
            return final_response 
        except Exception as e: 
            raise Exception(f"Recommendation error: {str(e)}") 
 
class CoordinatorAgent:
    """
    Coordinator Agent - Orchestrates all other agents to produce final recommendations.
    
    ROLE: Central controller that manages the recommendation workflow
    
    ORCHESTRATION FLOW:
    -------------------
    1. Receives user request (location, date, optional filters)
    2. Calls WeatherAgent to get weather data + suggestions
    3. Calls EventAgent to query and filter events
    4. Calls EventAgent to group events by time
    5. Calls RecommendationAgent to generate AI response
    6. Returns combined output to user
    
    DESIGN PATTERN: Facade Pattern
    - Provides simple interface to complex multi-agent system
    - User doesn't need to know about individual agents
    - Handles error cases gracefully
    
    ERROR HANDLING:
    ---------------
    - Weather API failures: Returns error message
    - No events found: Returns friendly "no events" message
    - Database errors: Caught and reported
    - AI failures: Exception with details
    """
    
    def __init__(self, weather_api_key, openai_api_key):
        """
        Initialize CoordinatorAgent with all sub-agents.
        
        Creates instances of:
        - WeatherAgent (for weather data)
        - EventAgent (for event queries)
        - RecommendationAgent (for AI generation)
        
        Args:
            weather_api_key (str): WeatherAPI.com API key
            openai_api_key (str): OpenAI API key
        """
        self.weather_agent = WeatherAgent(weather_api_key) 
        self.event_agent = EventAgent() 
        self.recommendation_agent = RecommendationAgent(openai_api_key) 
     
    def get_recommendations(self, location, date, event_type=None, time_of_day=None, max_price=None):
        """
        Main entry point for getting event recommendations.
        
        WORKFLOW:
        ---------
        1. Print status: Fetching weather...
        2. Get weather data from WeatherAgent
        3. Extract temperature and condition
        4. Get clothing suggestions from WeatherAgent
        5. Get transport suggestions from WeatherAgent
        6. Print status: Fetching events...
        7. Get filtered events from EventAgent
        8. Check if events exist (return early if not)
        9. Group events by time of day
        10. Print status: Generating recommendations...
        11. Get AI recommendations from RecommendationAgent
        12. Return final combined output
        
        FILTER COMBINATIONS:
        --------------------
        - All filters are optional (None = no filter)
        - Multiple filters use AND logic (all must match)
        - Examples:
          * event_type="indoor" → Only indoor events
          * time_of_day="evening" → Only evening events
          * max_price=20 → Only events $20 or less
          * All three → Indoor evening events under $20
        
        USER EXPERIENCE:
        ----------------
        - Progress indicators (emoji + text)
        - Clear "no events" message if nothing found
        - Error messages if API fails
        - Complete context in one response
        
        Args:
            location (str): City/location for weather (e.g., "Singapore", "London")
            date (str): Event date in YYYY-MM-DD format
            event_type (str, optional): 'indoor' or 'outdoor' filter
            time_of_day (str, optional): 'morning', 'afternoon', or 'evening' filter
            max_price (float, optional): Maximum price threshold
        
        Returns:
            str: Complete recommendation including:
                 - Weather conditions box with icons
                 - AI-generated recommendations
                 - Time-based schedule
                 - Practical advice
                 
        Returns (No Events):
            str: "No events found matching your criteria for this date."
            
        Returns (Error):
            str: "Error: [error message]"
        
        Example Usage:
        --------------
        ```python
        coordinator = CoordinatorAgent(WEATHER_API_KEY, OPENAI_API_KEY)
        
        # All events
        result = coordinator.get_recommendations("Singapore", "2026-02-15")
        
        # Filtered
        result = coordinator.get_recommendations(
            "Singapore", "2026-02-15",
            event_type="indoor",
            time_of_day="evening",
            max_price=50
        )
        ```
        """
        try: 
            # Get weather data 
            print(f"\n🌤️  Fetching weather data for {location} on {date}...") 
            weather_data = self.weather_agent.get_weather(location, date)
            
            # Get clothing and transport suggestions
            if 'current' in weather_data:
                temperature = weather_data['current']['temp_c']
                condition = weather_data['current']['condition']['text']
                clothing = self.weather_agent.get_clothing_suggestion(temperature, condition)
                transport = self.weather_agent.get_transport_suggestion(temperature, condition)
            else:
                clothing = []
                transport = "Weather data unavailable"
             
            # Get events with filters
            print("🎭 Fetching events...") 
            events = self.event_agent.get_events(date, event_type, time_of_day, max_price) 
             
            if not events: 
                return "No events found matching your criteria for this date." 
            
            # Group events by time of day
            grouped_events = self.event_agent.group_events_by_time(events)
             
            # Generate recommendations 
            print("🤖 Generating personalized recommendations...") 
            recommendations = self.recommendation_agent.generate_recommendation( 
                weather_data, events, grouped_events, clothing, transport, location, date
            ) 
             
            return recommendations 
             
        except Exception as e: 
            return f"Error: {str(e)}" 
 
if __name__ == "__main__": 
    # Test with enhanced features
    print("="*70)
    print("🎪 ENHANCED EVENT RECOMMENDATION SYSTEM")
    print("="*70)
    
    coordinator = CoordinatorAgent(WEATHER_API_KEY, OPENAI_API_KEY) 
    
    # Example 1: All events for a date
    print("\n\n" + "="*70)
    print("📅 EXAMPLE 1: All events on 2026-02-15 in Singapore")
    print("="*70)
    result = coordinator.get_recommendations("Singapore", "2026-02-15")
    print(result)
    
    # Example 2: Filter by time of day
    print("\n\n" + "="*70)
    print("📅 EXAMPLE 2: Evening events on 2026-02-16 in Singapore")
    print("="*70)
    result = coordinator.get_recommendations("Singapore", "2026-02-16", time_of_day="evening")
    print(result)
    
    # Example 3: Filter by price
    print("\n\n" + "="*70)
    print("📅 EXAMPLE 3: Budget-friendly events (max $20) on 2026-02-15")
    print("="*70)
    result = coordinator.get_recommendations("Singapore", "2026-02-15", max_price=20)
    print(result)
    
    # Example 4: Indoor events only
    print("\n\n" + "="*70)
    print("📅 EXAMPLE 4: Indoor events on 2026-02-16 in Singapore")
    print("="*70)
    result = coordinator.get_recommendations("Singapore", "2026-02-16", event_type="indoor")
    print(result)
    
    # Example 5: No events available for date
    print("\n\n" + "="*70)
    print("📅 EXAMPLE 5: Events on 2026-02-17 in Singapore (No events available)")
    print("="*70)
    result = coordinator.get_recommendations("Singapore", "2026-02-17")
    print(result) 