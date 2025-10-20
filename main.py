# --- main.py (The Starter File) ---
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import random

# --- ส่วนของ Flask (Keep-Alive) ---
# เรายังต้องใช้มันเพื่อให้ Render รันได้
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive and running Cogs!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
    print("Keep-alive server started.")
# --- จบส่วน Flask ---


# --- ส่วนของ Bot (Loader) ---
load_dotenv()
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# ตั้งค่า Intents (สิทธิ์) เหมือนเดิม
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True # สำคัญสำหรับเพลง

# สร้าง Bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """ทำงานเมื่อบอทพร้อม"""
    print(f'Logged in as {bot.user.name}')
    
    # สุ่ม Activity Status แบบเท่ๆ
    activities = [
        "🎵 /play | สั่งกูได้",
        "🎶 4KINGS Music",
        "🔥 เพลงเพราะๆ",
        "🎧 DJ นักเลง",
        "⚡ /help | ดูคำสั่ง",
        "🎸 Rock & Roll",
        "💎 Premium Sound",
        "🌟 เล่นให้ฟังฟรี"
    ]
    
    activity = discord.Activity(
        type=discord.ActivityType.listening, 
        name=random.choice(activities)
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    print('Bot is ready. Loading Cogs...')
    
    try:
        # สั่ง "ซิงค์" (Sync) คำสั่ง Slash Commands ทั้งหมด
        print("กำลัง Sync คำสั่ง...")
        synced = await bot.tree.sync()
        print(f"✅ Sync สำเร็จ! มี {len(synced)} คำสั่ง:")
        for cmd in synced:
            print(f"   - /{cmd.name}")
    except Exception as e:
        print(f"❌ Sync ล้มเหลว: {e}")
    print('------')

async def change_status():
    """เปลี่ยน Activity Status ทุกๆ 10 นาที"""
    await bot.wait_until_ready()
    
    # ใช้ Playing แทน Listening เพื่อไม่ให้ขึ้น "Listening to..."
    activities = [
        ("playing", "🎵 /play | สั่งกูได้"),
        ("playing", "🎶 /help | ขอส้นตีนเพิ่ม"),
        ("listening", "🔥 เพลงเพราะๆ"),
        ("playing", "🎧 DJ นักเลง"),
        ("playing", "⚡ /help | ดูคำสั่ง"),
        ("playing", "🎸 /play | จัดให้"),
        ("listening", "💎 Premium Sound"),
        ("playing", "🌟 เล่นให้ฟังฟรี"),
        ("playing", "🎤 /play | สั่งเพลงได้"),
        ("listening", "🎼 4KINGS Music"),
        ("playing", "🔊 /queue | ดูคิว"),
        ("playing", "✨ บอทนักเลง"),
        ("playing", "🎵 /skip | ข้ามได้"),
        ("playing", "🔥 /help | ขอส้นตีนเพิ่ม"),
        ("playing", "💯 /loop | วนซ้ำได้"),
        ("playing", "🎶 สั่งกูได้ทุกอย่าง")
    ]
    
    while not bot.is_closed():
        try:
            activity_type, activity_name = random.choice(activities)
            
            # เลือก ActivityType ตามที่กำหนด
            if activity_type == "playing":
                activity = discord.Activity(
                    type=discord.ActivityType.playing,
                    name=activity_name
                )
            else:  # listening
                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name=activity_name
                )
            
            await bot.change_presence(activity=activity, status=discord.Status.online)
            await asyncio.sleep(600)  # 10 นาที (ลดการกระตุก)
        except Exception as e:
            print(f"Error changing status: {e}")
            await asyncio.sleep(600)

async def load_cogs():
    """ฟังก์ชันสำหรับโหลด "แผนก" ทั้งหมดในโฟลเดอร์ cogs"""
    print("Loading 'music' cog...")
    try:
        await bot.load_extension('cogs.music') # 'cogs.music' คือ cogs/music.py
        print("Music cog loaded successfully.")
    except Exception as e:
        print(f"Failed to load music cog: {e}")

async def main():
    """ฟังก์ชันหลักสำหรับรันบอท"""
    if DISCORD_TOKEN is None:
        print("CRITICAL ERROR: 'DISCORD_TOKEN' not found.")
        return

    async with bot:
        keep_alive() # สั่งให้เว็บทำงาน
        await load_cogs() # สั่งให้โหลดแผนกเพลง
        bot.loop.create_task(change_status()) # เริ่ม task เปลี่ยน status
        await bot.start(DISCORD_TOKEN) # สั่งให้บอทเริ่มทำงาน

# --- สั่งรัน ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 บอทถูกหยุดโดยผู้ใช้ (Ctrl+C)")
        print("บ๊ายบาย! 🎵")
    except discord.errors.LoginFailure:
        print("❌ CRITICAL ERROR: Token ไม่ถูกต้อง! เช็กไฟล์ .env")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")