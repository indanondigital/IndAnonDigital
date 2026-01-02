import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# 1. Get the FULL URL directly from .env
# This allows it to work with Railway, Localhost, or any other cloud provider automatically.
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("❌ Error: DATABASE_URL not found in .env file")
    exit()

async def create_tables():
    print("⏳ Connecting to database...")
    try:
        # Connect using the URL from .env
        conn = await asyncpg.connect(DB_URL)
        
        print("🔨 Creating tables...")
        
        # 1. Create Users Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                gender VARCHAR(10) DEFAULT 'unknown',
                is_premium BOOLEAN DEFAULT FALSE,
                vip_expiry TIMESTAMP,
                joined_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # 2. Create Queue Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS search_queue (
                user_id BIGINT PRIMARY KEY,
                looking_for VARCHAR(10) DEFAULT 'any',
                joined_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # 3. Create Chats Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                user_1 BIGINT,
                user_2 BIGINT,
                started_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        print("✅ SUCCESS! All tables created successfully.")
        await conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())