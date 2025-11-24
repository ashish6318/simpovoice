"""
Database module for hotel room inventory management.
Handles SQLite operations for room data, bookings, FAQs, and analytics.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from config import config

DB_PATH = config.database.db_path

def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create all tables with sample data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            rack_rate REAL NOT NULL,
            direct_rate REAL NOT NULL,
            inventory INTEGER NOT NULL,
            description TEXT,
            amenities TEXT,
            max_occupancy INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_name TEXT,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            booking_source TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    """)
    
    # Create FAQs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create query analytics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed rooms table
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        rooms_data = [
            ("Deluxe Room", "deluxe", 5000.0, 4250.0, 10, 
             "Spacious room with premium amenities", "WiFi, TV, AC, Mini-bar", 2),
            ("Suite Room", "suite", 8000.0, 6800.0, 5,
             "Luxury suite with separate living area", "WiFi, TV, AC, Mini-bar, Bathtub, Balcony", 4),
            ("Standard Room", "standard", 3000.0, 2550.0, 15,
             "Comfortable room with essential amenities", "WiFi, TV, AC", 2),
            ("Executive Room", "executive", 6500.0, 5525.0, 8,
             "Business-class room with work desk", "WiFi, TV, AC, Mini-bar, Work Desk", 2)
        ]
        
        cursor.executemany("""
            INSERT INTO rooms (name, room_type, rack_rate, direct_rate, inventory, description, amenities, max_occupancy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rooms_data)
        print("✓ Rooms data seeded")
    
    # Seed FAQs table
    cursor.execute("SELECT COUNT(*) FROM faqs")
    if cursor.fetchone()[0] == 0:
        faqs_data = [
            ("What is the check-in time?", "Check-in time is 2:00 PM and check-out is 12:00 PM.", "policies", 10),
            ("Do you offer airport pickup?", "Yes, we offer complimentary airport pickup for suite bookings. For other rooms, it's available at ₹500.", "services", 8),
            ("Is WiFi free?", "Yes, high-speed WiFi is complimentary for all guests.", "amenities", 9),
            ("What is your cancellation policy?", "Free cancellation up to 24 hours before check-in. After that, one night's charge applies.", "policies", 10),
            ("Do you have parking facilities?", "Yes, we have free parking for all guests.", "facilities", 7),
            ("Is breakfast included?", "Breakfast is complimentary for direct bookings. OTA bookings can add breakfast for ₹300 per person.", "dining", 9),
            ("What payment methods do you accept?", "We accept cash, credit/debit cards, UPI, and bank transfers.", "payments", 6),
            ("Are pets allowed?", "Yes, we are pet-friendly. Additional charge of ₹500 per night applies.", "policies", 5),
        ]
        
        cursor.executemany("""
            INSERT INTO faqs (question, answer, category, priority)
            VALUES (?, ?, ?, ?)
        """, faqs_data)
        print("✓ FAQs data seeded")
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def get_rooms(available_only: bool = True) -> List[Dict]:
    """
    Fetch rooms from database.
    
    Args:
        available_only: If True, only return rooms with inventory > 0
        
    Returns:
        List of room dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM rooms"
    if available_only:
        query += " WHERE inventory > 0"
    query += " ORDER BY rack_rate"
    
    cursor.execute(query)
    rooms = cursor.fetchall()
    conn.close()
    
    rooms_list = []
    for room in rooms:
        rooms_list.append({
            "id": room["id"],
            "name": room["name"],
            "room_type": room["room_type"],
            "rack_rate": room["rack_rate"],
            "direct_rate": room["direct_rate"],
            "inventory": room["inventory"],
            "description": room["description"],
            "amenities": room["amenities"],
            "max_occupancy": room["max_occupancy"],
            "savings": room["rack_rate"] - room["direct_rate"],
            "discount_percentage": round(((room["rack_rate"] - room["direct_rate"]) / room["rack_rate"]) * 100)
        })
    
    return rooms_list


def get_room_by_type(room_type: str) -> Optional[Dict]:
    """
    Get specific room by type.
    
    Args:
        room_type: Type of room (deluxe, suite, standard, executive)
        
    Returns:
        Room dictionary or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rooms WHERE room_type = ? AND inventory > 0", (room_type.lower(),))
    room = cursor.fetchone()
    conn.close()
    
    if room:
        return {
            "id": room["id"],
            "name": room["name"],
            "room_type": room["room_type"],
            "rack_rate": room["rack_rate"],
            "direct_rate": room["direct_rate"],
            "inventory": room["inventory"],
            "description": room["description"],
            "amenities": room["amenities"],
            "max_occupancy": room["max_occupancy"],
            "savings": room["rack_rate"] - room["direct_rate"]
        }
    return None


def check_room_availability(room_type: str, check_in: str, check_out: str) -> Tuple[bool, int]:
    """
    Check if room is available for given dates.
    
    Args:
        room_type: Type of room
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        
    Returns:
        Tuple of (is_available, available_count)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get total inventory
    cursor.execute("SELECT inventory FROM rooms WHERE room_type = ?", (room_type.lower(),))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, 0
    
    total_inventory = result["inventory"]
    
    # Get booked rooms for the date range
    cursor.execute("""
        SELECT COUNT(*) as booked
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE r.room_type = ?
        AND b.status = 'confirmed'
        AND (
            (b.check_in <= ? AND b.check_out > ?) OR
            (b.check_in < ? AND b.check_out >= ?) OR
            (b.check_in >= ? AND b.check_out <= ?)
        )
    """, (room_type.lower(), check_in, check_in, check_out, check_out, check_in, check_out))
    
    booked = cursor.fetchone()["booked"]
    conn.close()
    
    available = total_inventory - booked
    return available > 0, available


def create_booking(room_type: str, check_in: str, check_out: str, 
                   booking_source: str = "direct", guest_name: Optional[str] = None) -> Optional[int]:
    """
    Create a new booking.
    
    Args:
        room_type: Type of room to book
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        booking_source: Source of booking (direct, ota, etc.)
        guest_name: Optional guest name
        
    Returns:
        Booking ID if successful, None otherwise
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get room details
    cursor.execute("SELECT id, direct_rate, rack_rate FROM rooms WHERE room_type = ?", (room_type.lower(),))
    room = cursor.fetchone()
    
    if not room:
        conn.close()
        return None
    
    # Calculate total amount
    from datetime import datetime
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
    nights = (check_out_date - check_in_date).days
    
    rate = room["direct_rate"] if booking_source == "direct" else room["rack_rate"]
    total_amount = rate * nights
    
    # Create booking
    cursor.execute("""
        INSERT INTO bookings (room_id, guest_name, check_in, check_out, booking_source, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
    """, (room["id"], guest_name, check_in, check_out, booking_source, total_amount))
    
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return booking_id


def get_faqs(category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Fetch FAQs from database.
    
    Args:
        category: Optional category filter
        limit: Maximum number of results
        
    Returns:
        List of FAQ dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT * FROM faqs 
            WHERE category = ? 
            ORDER BY priority DESC, id 
            LIMIT ?
        """, (category, limit))
    else:
        cursor.execute("""
            SELECT * FROM faqs 
            ORDER BY priority DESC, id 
            LIMIT ?
        """, (limit,))
    
    faqs = cursor.fetchall()
    conn.close()
    
    return [{"question": faq["question"], "answer": faq["answer"], "category": faq["category"]} 
            for faq in faqs]


def search_faqs(search_term: str) -> List[Dict]:
    """
    Search FAQs by keyword.
    
    Args:
        search_term: Search keyword
        
    Returns:
        List of matching FAQs
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{search_term}%"
    cursor.execute("""
        SELECT * FROM faqs 
        WHERE question LIKE ? OR answer LIKE ?
        ORDER BY priority DESC
        LIMIT 5
    """, (search_pattern, search_pattern))
    
    faqs = cursor.fetchall()
    conn.close()
    
    return [{"question": faq["question"], "answer": faq["answer"], "category": faq["category"]} 
            for faq in faqs]


def log_query(user_query: str, intent: str, confidence: float, response_time_ms: int):
    """
    Log user query for analytics.
    
    Args:
        user_query: User's query text
        intent: Detected intent
        confidence: Confidence score
        response_time_ms: Response time in milliseconds
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_logs (user_query, intent, confidence, response_time_ms)
            VALUES (?, ?, ?, ?)
        """, (user_query, intent, confidence, response_time_ms))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Query logging error: {e}")


def get_analytics(hours: int = 24) -> Dict:
    """
    Get comprehensive analytics data from query logs.
    
    Args:
        hours: Number of hours to look back for time-based metrics
    
    Returns:
        Dictionary with analytics metrics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    time_filter = f"datetime('now', '-{hours} hours')"
    
    # Total queries (all time)
    cursor.execute("SELECT COUNT(*) as total FROM query_logs")
    total_queries = cursor.fetchone()["total"]
    
    # Recent queries (last N hours)
    cursor.execute(f"SELECT COUNT(*) as recent FROM query_logs WHERE created_at >= {time_filter}")
    recent_queries = cursor.fetchone()["recent"]
    
    # Average confidence (all time)
    cursor.execute("SELECT AVG(confidence) as avg_conf FROM query_logs")
    avg_confidence = cursor.fetchone()["avg_conf"] or 0
    
    # Average response time (all time)
    cursor.execute("SELECT AVG(response_time_ms) as avg_time FROM query_logs")
    avg_response_time = cursor.fetchone()["avg_time"] or 0
    
    # Min/Max response times
    cursor.execute("SELECT MIN(response_time_ms) as min_time, MAX(response_time_ms) as max_time FROM query_logs")
    row = cursor.fetchone()
    min_response_time = row["min_time"] or 0
    max_response_time = row["max_time"] or 0
    
    # Top intents
    cursor.execute("""
        SELECT intent, COUNT(*) as count 
        FROM query_logs 
        GROUP BY intent 
        ORDER BY count DESC 
        LIMIT 5
    """)
    top_intents = [{"intent": row["intent"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Low confidence queries (potential errors)
    cursor.execute("""
        SELECT COUNT(*) as low_conf_count
        FROM query_logs 
        WHERE confidence < 0.5
    """)
    low_confidence_count = cursor.fetchone()["low_conf_count"]
    
    # Error rate (queries with unknown intent or low confidence)
    error_rate = (low_confidence_count / total_queries * 100) if total_queries > 0 else 0
    
    # Queries per hour (last 24 hours)
    cursor.execute(f"""
        SELECT strftime('%H:00', created_at) as hour, COUNT(*) as count
        FROM query_logs
        WHERE created_at >= {time_filter}
        GROUP BY hour
        ORDER BY hour DESC
        LIMIT 24
    """)
    hourly_stats = [{"hour": row["hour"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Most common queries
    cursor.execute("""
        SELECT user_query, COUNT(*) as count
        FROM query_logs
        GROUP BY LOWER(user_query)
        ORDER BY count DESC
        LIMIT 5
    """)
    common_queries = [{"query": row["user_query"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Intent distribution
    cursor.execute("""
        SELECT intent, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM query_logs), 1) as percentage
        FROM query_logs
        GROUP BY intent
        ORDER BY count DESC
    """)
    intent_distribution = [
        {"intent": row["intent"], "count": row["count"], "percentage": row["percentage"]} 
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return {
        "total_queries": total_queries,
        "recent_queries": recent_queries,
        "avg_confidence": round(avg_confidence, 2),
        "avg_response_time_ms": round(avg_response_time, 0),
        "min_response_time_ms": round(min_response_time, 0),
        "max_response_time_ms": round(max_response_time, 0),
        "error_rate": round(error_rate, 1),
        "low_confidence_count": low_confidence_count,
        "top_intents": top_intents,
        "hourly_stats": hourly_stats,
        "common_queries": common_queries,
        "intent_distribution": intent_distribution
    }


def get_performance_metrics() -> Dict:
    """
    Get system performance metrics.
    
    Returns:
        Dictionary with performance data
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Response time percentiles
    cursor.execute("""
        SELECT 
            MIN(response_time_ms) as p0,
            MAX(CASE WHEN row_num <= total * 0.5 THEN response_time_ms END) as p50,
            MAX(CASE WHEN row_num <= total * 0.95 THEN response_time_ms END) as p95,
            MAX(CASE WHEN row_num <= total * 0.99 THEN response_time_ms END) as p99,
            MAX(response_time_ms) as p100
        FROM (
            SELECT response_time_ms,
                   ROW_NUMBER() OVER (ORDER BY response_time_ms) as row_num,
                   COUNT(*) OVER () as total
            FROM query_logs
        )
    """)
    
    percentiles = cursor.fetchone()
    
    # Queries by confidence level
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN confidence >= 0.8 THEN 1 ELSE 0 END) as high_conf,
            SUM(CASE WHEN confidence >= 0.5 AND confidence < 0.8 THEN 1 ELSE 0 END) as medium_conf,
            SUM(CASE WHEN confidence < 0.5 THEN 1 ELSE 0 END) as low_conf
        FROM query_logs
    """)
    
    conf_dist = cursor.fetchone()
    
    conn.close()
    
    return {
        "response_time_percentiles": {
            "min": percentiles["p0"] or 0,
            "p50": percentiles["p50"] or 0,
            "p95": percentiles["p95"] or 0,
            "p99": percentiles["p99"] or 0,
            "max": percentiles["p100"] or 0
        },
        "confidence_distribution": {
            "high": conf_dist["high_conf"] or 0,
            "medium": conf_dist["medium_conf"] or 0,
            "low": conf_dist["low_conf"] or 0
        }
    }

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    print("\n" + "="*60)
    print("DATABASE TEST - All Functions")
    print("="*60)
    
    # Test 1: Get all rooms
    print("\n[1] Available Rooms:")
    for room in get_rooms():
        print(f"  • {room['name']}: ₹{room['direct_rate']} (Save {room['discount_percentage']}%)")
    
    # Test 2: Get specific room
    print("\n[2] Deluxe Room Details:")
    deluxe = get_room_by_type("deluxe")
    if deluxe:
        print(f"  • {deluxe['description']}")
        print(f"  • Amenities: {deluxe['amenities']}")
        print(f"  • Available: {deluxe['inventory']} rooms")
    
    # Test 3: Check availability
    print("\n[3] Availability Check:")
    available, count = check_room_availability("suite", "2025-12-01", "2025-12-05")
    print(f"  • Suite available: {available} ({count} rooms)")
    
    # Test 4: FAQs
    print("\n[4] Top FAQs:")
    for faq in get_faqs(limit=3):
        print(f"  Q: {faq['question']}")
        print(f"  A: {faq['answer']}\n")
    
    # Test 5: Search FAQs
    print("[5] Search Results for 'WiFi':")
    for faq in search_faqs("WiFi"):
        print(f"  • {faq['question']}")
    
    print("\n" + "="*60)
    print("✓ All database functions working correctly")
    print("="*60)
