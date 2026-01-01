import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Get password from .env
DB_PASS = os.getenv("DB_PASS")
# Connection URL
DB_URL = f"postgresql://postgres:{DB_PASS}@localhost/anonchat"

async def create_tables():
    print("⏳ Connecting to database...")
    try:
        conn = await asyncpg.connect(DB_URL)
        
        print("🔨 Creating tables...")
        # 1. Create Users Table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                gender VARCHAR(10) DEFAULT 'unknown',
                is_premium BOOLEAN DEFAULT FALSE,
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
        
        print("✅ SUCCESS! All tables created.")
        await conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_tables())