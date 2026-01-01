import os
import psycopg2
import razorpay
import time
import webbrowser  # To open the link automatically
from dotenv import load_dotenv

# 1. Load the secrets
load_dotenv()

# 2. Get the Secrets securely
DB_PASS = os.getenv("DB_PASS")
RZP_KEY_ID = os.getenv("RZP_KEY")
RZP_KEY_SECRET = os.getenv("RZP_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")      # <--- New
ADMIN_USERNAME = os.getenv("SUPERUSERNAME") # <--- New (Safeguards your name)
PRICE = int(os.getenv("PRICE", "10000"))  # Price in PAISE (10000 paise = ₹100)

# 3. Validation Check (Optional but Smart)
# This warns you if you forgot to put them in the .env file
if not DB_PASS or not RZP_KEY_ID:
    print("❌ ERROR: Secrets are missing from .env file!")
    exit()

# Initialize Razorpay Client
client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))



def get_db_connection():
    # 1. Try to get the Cloud URL
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        # If we are on the Cloud (Render), use the URL
        return psycopg2.connect(db_url, sslmode='require')
    else:
        # If we are on Laptop, use Localhost
        return psycopg2.connect(
            dbname="anonchat",
            user="postgres",
            password=DB_PASS,
            host="localhost"
        )

def check_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, is_premium FROM users WHERE username = %s;", (username,))
    result = cur.fetchone()
    conn.close()
    if result:
        return result[0], result[1] 
    return None, False

def create_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    query = "INSERT INTO users (username) VALUES (%s) RETURNING user_id;"
    cur.execute(query, (username,))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id

def upgrade_user_to_premium(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_premium = TRUE WHERE user_id = %s;", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error upgrading: {e}")
        return False

# --- NEW: REAL PAYMENT LOGIC ---
def create_payment_link(username):
    """Creates a real payment link via Razorpay API"""
    print("   ⏳ Contacting Payment Gateway...")
    try:
        data = {
            "amount": PRICE,
            "currency": "INR",
            "description": "AnonChat Premium Upgrade",
            "customer": {
                "name": username,
                "email": "user@example.com",
                # 👇 CHANGE THIS LINE 👇
                "contact": "9876543210" 
            },
            "notify": {"sms": False, "email": False},
            "reminder_enable": False,
            "callback_url": "https://google.com", 
            "callback_method": "get"
        }
        payment_link = client.payment_link.create(data)
        return payment_link['short_url'], payment_link['id']
    except Exception as e:
        print(f"   ❌ Gateway Error: {e}")
        return None, None

def verify_payment_status(pl_id):
    """Checks if the specific link was actually paid"""
    try:
        # Fetch status from Razorpay
        details = client.payment_link.fetch(pl_id)
        status = details['status'] # 'created', 'paid', or 'expired'
        return status
    except Exception as e:
        return "error"

def get_admin_stats():
    """Fetches admin dashboard statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total users
        cur.execute("SELECT COUNT(*) FROM users;")
        total = cur.fetchone()[0]
        
        # Premium users
        cur.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE;")
        vip_count = cur.fetchone()[0]
        
        # Total revenue (assuming ₹100 per premium user)
        money = vip_count * 100
        
        conn.close()
        return total, vip_count, money
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return 0, 0, 0

# --- MAIN SYSTEM ---
def start_bot():
    print("🤖 SYSTEM: AnonChatBot Online...")
    user_input = input("Enter Username: ").strip()
    
    user_id, is_premium = check_user(user_input)

    # Registration
    if user_id is None:
        print(f"   User '{user_input}' does not exist.")
        choice = input("   Create account? (yes/no): ")
        if choice.lower() == "yes":
            user_id = create_user(user_input)
            is_premium = False 
        else:
            return

    if is_premium:
        print(f"\n🌟 WELCOME BACK, VIP {user_input}! 🌟")
    else:
        print(f"\nWelcome, {user_input} (Standard Plan).")
        print("💡 TIP: Type '!upgrade' to buy Premium (₹100).")

    while True:
        msg = input(f"{user_input}: ")
        
        if msg.lower() == "exit":
            break
        
        # --- THE REAL UPGRADE FLOW ---
        elif msg.lower() == "!upgrade":
            if is_premium:
                print("🤖 Bot: You are already Premium!")
            else:
                print("\n💳 --- SECURE PAYMENT GATEWAY ---")
                print("   Generating Payment Link for UPI / Cards...")
                
                # 1. Create Link
                url, pl_id = create_payment_link(user_input)
                
                if url:
                    print(f"   🔗 Link Created: {url}")
                    print("   Opening browser now...")
                    webbrowser.open(url) # Opens Chrome/Edge automatically
                    
                    print("\n   ⚠️  ACTION REQUIRED:")
                    print("   1. Complete payment in the browser.")
                    print("   2. Come back here and press ENTER.")
                    input("   [Press Enter after you pay]")
                    
                    # 2. Verify Status
                    print("   Verifying with Bank...")
                    status = verify_payment_status(pl_id)
                    
                    if status == "paid":
                        upgrade_user_to_premium(user_id)
                        is_premium = True
                        print("   ✅ PAYMENT SUCCESSFUL! Welcome to Premium.")
                    else:
                        print(f"   ❌ Payment Failed or Pending. Status: {status}")
                        print("   (If you paid, try typing !upgrade again)")
        
        # --- ADMIN DASHBOARD (SECURED) ---
        elif msg.lower() == "!admin":
            # 🔒 SECURITY CHECK 🔒
            if user_input != ADMIN_USERNAME:
                print(f"   ⛔ ACCESS DENIED. You are not authorized, {user_input}.")
            else:
                # Only runs if you are the Admin
                total, vip_count, money = get_admin_stats()
                print("\n📊 --- SUPERUSER DASHBOARD ---")
                print(f"   👑 Owner:          {ADMIN_USERNAME}")
                print(f"   👥 Total Users:    {total}")
                print(f"   🌟 Premium Users:  {vip_count}")
                print(f"   💰 Total Revenue:  ₹{money}")
                print("------------------------------")

        else:
            print("   (message sent)")

start_bot()