"""
Event Database Setup Module

This module handles the creation and initialization of the SQLite database
that stores event information for the recommendation system.


"""

import sqlite3 


def setup_database():
    """
    Initialize the events database with schema and sample data.
    
    This function:
    1. Drops existing events table to ensure clean state
    2. Creates events table with enhanced schema
    3. Populates database with diverse sample events
    
    Database Schema:
    ----------------
    - id: Primary key (auto-increment)
    - name: Event name/title
    - type: 'indoor' or 'outdoor' (for weather considerations)
    - description: Brief event description
    - location: Venue/place name
    - date: Event date (YYYY-MM-DD format)
    - start_time: Event start time (HH:MM format)
    - end_time: Event end time (HH:MM format)
    - price_min: Minimum ticket price (0.0 for free events)
    - price_max: Maximum ticket price
    - capacity: Total event capacity
    - available_spots: Current available spots
    
    Sample Data Design:
    -------------------
    - Mix of indoor/outdoor events for weather testing
    - Various time slots (morning, afternoon, evening)
    - Different price points (free to premium)
    - Different availability levels (full, limited, available)
    """
    conn = sqlite3.connect('events.db') 
    c = conn.cursor() 
     
    # Drop existing table to recreate with new schema
    # This ensures clean slate during development/testing
    c.execute('DROP TABLE IF EXISTS events')
    
    # Create events table with comprehensive schema
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS events ( 
            id INTEGER PRIMARY KEY, 
            name TEXT, 
            type TEXT,  -- 'indoor' or 'outdoor' 
            description TEXT, 
            location TEXT, 
            date TEXT,
            start_time TEXT,  -- Time of day (e.g., '10:00', '14:00', '19:00')
            end_time TEXT,
            price_min REAL,  -- Minimum price
            price_max REAL,  -- Maximum price
            capacity INTEGER,  -- Total capacity
            available_spots INTEGER  -- Available spots
        ) 
    ''') 
     
    # Enhanced sample events with new fields
    # Event structure: (name, type, description, location, date, start_time, end_time,
    #                   price_min, price_max, capacity, available_spots)
    events = [ 
        # Evening outdoor event with limited availability - tests booking urgency
        ('Summer Concert', 'outdoor', 'Live music in the park', 'Central Park', '2026-02-15', '18:00', '22:00', 25.0, 50.0, 500, 120),
        
        # All-day indoor event, free/paid options - tests budget filtering
        ('Art Exhibition', 'indoor', 'Modern art showcase', 'City Gallery', '2026-02-15', '10:00', '18:00', 0.0, 15.0, 200, 200),
        
        # Early morning outdoor event with very limited spots - tests urgency alerts
        ('Morning Yoga', 'outdoor', 'Sunrise yoga session', 'Beach Park', '2026-02-15', '06:00', '07:30', 10.0, 10.0, 30, 8),
        
        # Long duration outdoor free event - tests weather impact on free events
        ('Food Festival', 'outdoor', 'International cuisine', 'Waterfront', '2026-02-16', '12:00', '20:00', 0.0, 0.0, 1000, 850),
        
        # Evening indoor premium event with limited spots - tests price + urgency
        ('Theater Show', 'indoor', 'Classical drama', 'Grand Theater', '2026-02-16', '19:30', '21:30', 40.0, 80.0, 300, 45),
        
        # Afternoon indoor workshop with critical availability - tests booking alerts
        ('Cooking Workshop', 'indoor', 'Learn Italian cuisine', 'Culinary Studio', '2026-02-16', '14:00', '17:00', 60.0, 60.0, 15, 3),
        
        # Evening outdoor free event with high capacity - tests weather impact
        ('Night Market', 'outdoor', 'Street food and crafts', 'Downtown Square', '2026-02-16', '18:00', '23:00', 0.0, 0.0, 2000, 2000),
        
        # Morning indoor tour with moderate availability - tests time-based filtering
        ('Museum Tour', 'indoor', 'Guided historical tour', 'National Museum', '2026-02-15', '11:00', '13:00', 12.0, 12.0, 50, 22)
    ] 
     
    # Insert all sample events into database
    c.executemany('''INSERT INTO events (name, type, description, location, date, start_time, end_time, 
                     price_min, price_max, capacity, available_spots) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', events) 
    conn.commit() 
    conn.close()
    print("✅ Database created successfully with sample events!")


if __name__ == "__main__": 
    setup_database() 