# --- cogs/music.py (The Music Department) ---
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import datetime
import random
from gtts import gTTS
import os
import tempfile

# --- คลาส YTDLSource (เหมือนเดิม) ---
# (เรายังต้องใช้มันเพื่อดึงข้อมูลเพลง)

ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',  # เลือกฟอร์แมตที่เหมาะสม
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtoconsole': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': 'in_playlist',
    'cachedir': False,  # ปิด cache เพื่อลด I/O
    'prefer_ffmpeg': True,  # ใช้ FFmpeg
    'keepvideo': False,  # ไม่เก็บวิดีโอ
    'socket_timeout': 30,  # เพิ่ม timeout
}

ffmpeg_options = {
    'options': '-vn -b:a 128k',  # จำกัด bitrate ลดการใช้ bandwidth
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-probesize 10M '  # เพิ่ม buffer size
        '-analyzeduration 10M '  # เพิ่มเวลาวิเคราะห์
        '-loglevel warning'  # ลด log
    )
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    """คลาสจัดการสตรีมเสียงจาก YTDL"""
    def __init__(self, source, *, data, volume=0.3):  # ลด volume เริ่มต้นเป็น 0.3
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# --- จบคลาส YTDLSource ---


# --- คลาส "ปุ่มควบคุม" (Control Buttons) ---
# นี่คือส่วนที่สร้างปุ่ม Pause, Resume, Skip, Stop

class MusicPlayerView(discord.ui.View):
    """
    คลาส 'View' (วิว) ที่รวมปุ่มทั้งหมดไว้ด้วยกัน
    """
    def __init__(self, bot, guild_id, cog, timeout=None): # timeout=None คือให้ปุ่มอยู่ตลอด
        super().__init__(timeout=timeout)
        self.bot = bot
        self.guild_id = guild_id
        self.cog = cog # ส่ง 'MusicCog' เข้ามาเพื่อเรียกใช้ฟังก์ชัน

    async def get_voice_client(self):
        """ตัวช่วยหา voice_client"""
        return discord.utils.get(self.bot.voice_clients, guild=self.bot.get_guild(self.guild_id))

    # --- ปุ่ม Pause (หยุดชั่วคราว) ---
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸️", row=0)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.get_voice_client()
        if vc and vc.is_playing():
            vc.pause()
            responses = [
                "⏸️ พักก่อนนะ",
                "⏸️ หยุดชั่วคราว",
                "⏸️ พักเบรก"
            ]
            await interaction.response.send_message(random.choice(responses), ephemeral=True)
        else:
            await interaction.response.send_message("ไม่มีอะไรเล่นอยู่", ephemeral=True)

    # --- ปุ่ม Resume (เล่นต่อ) ---
    @discord.ui.button(label="Resume", style=discord.ButtonStyle.primary, emoji="▶️", row=0)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.get_voice_client()
        if vc and vc.is_paused():
            vc.resume()
            responses = [
                "▶️ เล่นต่อ!",
                "▶️ ดำเนินการต่อ",
                "▶️ เริ่มใหม่"
            ]
            await interaction.response.send_message(random.choice(responses), ephemeral=True)
        else:
            await interaction.response.send_message("ไม่ได้หยุดเล่นอยู่", ephemeral=True)

    # --- ปุ่ม Skip (ข้าม) ---
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.get_voice_client()
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            responses = [
                "⏭️ ข้ามให้แล้ว",
                "⏭️ ไม่ชอบหรอ? ข้ามเลย",
                "⏭️ โอเค ข้าม"
            ]
            await interaction.response.send_message(random.choice(responses), ephemeral=True)
        else:
            await interaction.response.send_message("ไม่มีเพลงให้ข้าม", ephemeral=True)

    # --- ปุ่ม Stop (หยุดและออก) ---
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = await self.get_voice_client()
        if vc:
            responses = [
                "⏹️ หยุดแล้ว บ๊ายบาย",
                "⏹️ ปิดให้แล้ว ไปก่อน",
                "⏹️ เคลียร์หมดแล้ว"
            ]
            await interaction.response.send_message(random.choice(responses), ephemeral=True)
            # เรียก stop_and_clear โดยไม่ส่ง interaction (เพราะตอบไปแล้ว)
            await self.cog.stop_and_clear(interaction.guild, interaction=None)
        else:
            await interaction.response.send_message("กูไม่ได้อยู่ในช่องเสียง", ephemeral=True)

    # --- ปุ่ม Loop (วนซ้ำเพลง) ---
    @discord.ui.button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔂", row=1)
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_guild_state(interaction.guild.id)
        state["loop"] = not state["loop"]
        state["loop_queue"] = False  # ปิด loop queue
        
        if state["loop"]:
            responses = [
                "🔂 เปิดวนซ้ำเพลงนี้แล้ว",
                "🔂 วนซ้ำเพลงนี้ให้",
                "🔂 โอเค วนซ้ำ"
            ]
        else:
            responses = [
                "⏹️ ปิดวนซ้ำแล้ว",
                "⏹️ เลิกวนซ้ำแล้ว",
                "⏹️ โอเค ไม่วนแล้ว"
            ]
        await interaction.response.send_message(random.choice(responses), ephemeral=True)

    # --- ปุ่ม Queue (ดูคิว) ---
    @discord.ui.button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_guild_state(interaction.guild.id)
        
        embed = discord.Embed(
            title="🎵 คิวเพลง",
            color=0x5865F2
        )
        
        if not state["queue"] and not state["now_playing"]:
            embed.description = "ว่างเปล่า... เหมือนอนาคตมึงไงไอ้หนุ่ม"
        else:
            description = ""
            
            # แสดงเพลงที่กำลังเล่น
            if state["now_playing"]:
                player = state["now_playing"]["player"]
                description += f"**🎵 กำลังเล่น:**\n{player.title}\n\n"
            
            # แสดงคิว
            if state["queue"]:
                description += "**📋 ต่อคิว:**\n"
                for i, item in enumerate(state["queue"][:10], 1):
                    description += f"`{i}.` {item['player'].title}\n"
                
                if len(state["queue"]) > 10:
                    description += f"\n...และอีก {len(state['queue']) - 10} เพลง"
            
            embed.description = description
            
            # แสดงสถานะ Loop
            if state["loop"]:
                embed.set_footer(text="🔂 Loop: เพลงเดียว")
            elif state["loop_queue"]:
                embed.set_footer(text="🔁 Loop: ทั้งคิว")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- ปุ่ม Shuffle (สับคิว) ---
    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.secondary, emoji="🔀", row=1)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.cog.get_guild_state(interaction.guild.id)
        
        if len(state["queue"]) < 2:
            await interaction.response.send_message("ต้องมีอย่างน้อย 2 เพลงในคิว", ephemeral=True)
            return
        
        random.shuffle(state["queue"])
        responses = [
            f"🔀 สับเปลี่ยนคิวให้แล้ว {len(state['queue'])} เพลง",
            f"🔀 สุ่มลำดับให้แล้ว",
            f"🔀 เชคเกอร์! สับให้แล้ว"
        ]
        await interaction.response.send_message(random.choice(responses), ephemeral=True)


# --- "แผนกเพลง" (Music Cog) ---

class MusicCog(commands.Cog):
    """
    คลาสนี้คือ "แผนกเพลง" จัดการทุกอย่างที่เกี่ยวกับเพลง
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_states = {}
        self.check_alone_task = self.bot.loop.create_task(self.check_alone_in_voice())
        
        # ตั้งค่าเสียง: True = ใช้ไฟล์ mp3, False = ไม่ใช้เสียง (ส่งข้อความอย่างเดียว)
        self.use_custom_sound = False  # เปลี่ยนเป็น True ถ้าอยากใช้ไฟล์ mp3
        self.use_tts = False  # ปิด TTS เพราะช้าเกินไป

    def cog_unload(self):
        """ยกเลิก task เมื่อ unload cog"""
        self.check_alone_task.cancel()

    async def check_alone_in_voice(self):
        """ตรวจสอบว่าบอทอยู่คนเดียวในช่องเสียงหรือไม่"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for vc in self.bot.voice_clients:
                    try:
                        # เช็กว่า vc ยังเชื่อมต่ออยู่
                        if not vc.is_connected():
                            continue
                            
                        # นับจำนวนคนในช่อง (ไม่นับบอท)
                        members = [m for m in vc.channel.members if not m.bot]
                        
                        if len(members) == 0:
                            # ไม่มีคนในช่อง
                            state = self.get_guild_state(vc.guild.id)
                            
                            # ตั้ง flag ว่ากำลัง stop
                            state["is_stopping"] = True
                            
                            text_channel = state.get("text_channel")
                            
                            if text_channel:
                                try:
                                    messages = [
                                        "เฮ้ย! ไม่มีคนฟังแล้ว กูไปละ",
                                        "ทิ้งกูไว้คนเดียวหรอ? ไปก่อน",
                                        "ไม่มีใครฟังแล้ว บ๊ายบาย"
                                    ]
                                    await text_channel.send(random.choice(messages))
                                except:
                                    pass
                            
                            # ล้างคิวและออก
                            state["queue"].clear()
                            state["now_playing"] = None
                            state["loop"] = False
                            state["loop_queue"] = False
                            
                            if vc.is_playing() or vc.is_paused():
                                vc.stop()
                            
                            await asyncio.sleep(0.5)
                            
                            if vc.is_connected():
                                await vc.disconnect()
                            
                            # รีเซ็ต flag
                            state["is_stopping"] = False
                            
                    except Exception as e:
                        print(f"Error checking voice client: {e}")
                        continue
                
                await asyncio.sleep(60)  # เช็กทุก 1 นาที
            except Exception as e:
                print(f"Error in check_alone_in_voice: {e}")
                await asyncio.sleep(60)

    def get_guild_state(self, guild_id: int):
        """
        ตัวช่วยสร้าง/ดึง "หน้าสมุด" ของเซิร์ฟเวอร์นั้นๆ
        """
        if guild_id not in self.guild_states:
            # ถ้าเป็นเซิร์ฟเวอร์ใหม่ สร้างหน้าใหม่ให้
            self.guild_states[guild_id] = {
                "queue": [],
                "loop": False,
                "loop_queue": False,
                "now_playing": None,
                "now_playing_message": None,
                "text_channel": None,
                "is_stopping": False,  # เพิ่ม flag เพื่อป้องกันข้อความซ้ำ
            }
        return self.guild_states[guild_id]

    # --- ตัวช่วย: สร้าง Embed สวยๆ ---
    def create_now_playing_embed(self, player: YTDLSource, guild: discord.Guild, requester: discord.Member, voice_channel: discord.VoiceChannel):
        """สร้าง Embed (เอ็มเบด) แบบสวยๆ สำหรับเพลงที่กำลังเล่น"""
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{player.title}**",
            color=0x5865F2  # สีน้ำเงิน Discord
        )
        
        # ใส่รูปภาพใหญ่
        if player.thumbnail:
            embed.set_image(url=player.thumbnail)
        
        # แปลงวินาทีเป็น นาที:วินาที
        if player.duration:
            duration_formatted = str(datetime.timedelta(seconds=player.duration))
        else:
            duration_formatted = "Unknown"
            
        # เพิ่มข้อมูลแบบในภาพ
        embed.add_field(name="⏱️ Duration", value=duration_formatted, inline=True)
        embed.add_field(name="👤 Requested by", value=requester.mention, inline=True)
        embed.add_field(name="🔊 Voice Channel", value=voice_channel.name, inline=True)
        
        # Footer
        embed.set_footer(
            text=f"Powered by {self.bot.user.name} • Queue: {len(self.get_guild_state(guild.id)['queue'])} songs",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed

    def create_queue_embed(self, song_list: list, title: str):
        """สร้าง Embed สำหรับคิวเพลง"""
        embed = discord.Embed(
            title=title,
            color=0x5865F2
        )
        if not song_list:
            embed.description = "ว่างเปล่า... เหมือนอนาคตมึงไงไอ้หนุ่ม"
        else:
            # แสดงแค่ 10 เพลงแรก
            embed.description = "\n".join(
                f"`{i+1}.` {item['player'].title}" for i, item in enumerate(song_list[:10])
            )
            if len(song_list) > 10:
                embed.description += f"\n...และอีก {len(song_list) - 10} เพลง"
        return embed

    # --- เสียงก่อนออก ---
    async def speak_and_leave(self, vc: discord.VoiceClient, text: str, use_custom_sound: bool = False):
        """
        เล่นเสียงก่อนออกจากช่อง (ถ้ามีไฟล์ mp3)
        ถ้าไม่มีก็ออกเลย
        """
        try:
            if not vc or not vc.is_connected():
                return
            
            audio_file = None
            
            # ใช้ไฟล์ mp3 ถ้ามี
            if use_custom_sound:
                sound_files = [
                    "sounds/goodbye1.mp3",
                    "sounds/goodbye2.mp3",
                    "sounds/goodbye3.mp3",
                ]
                
                available_files = [f for f in sound_files if os.path.exists(f)]
                
                if available_files:
                    audio_file = random.choice(available_files)
            
            # เล่นเสียงถ้ามีไฟล์
            if audio_file and vc.is_connected():
                audio_source = discord.FFmpegPCMAudio(audio_file)
                vc.play(audio_source)
                
                # รอให้เล่นจบ (สูงสุด 10 วินาที)
                wait_time = 0
                while vc.is_playing() and wait_time < 10:
                    await asyncio.sleep(1)
                    wait_time += 1
                    
                await asyncio.sleep(0.5)
            
            # ออกจากช่อง
            if vc.is_connected():
                await vc.disconnect()
                
        except Exception as e:
            print(f"Sound Error: {e}")
            try:
                if vc and vc.is_connected():
                    await vc.disconnect()
            except:
                pass

    # --- ตัวจัดการคิว (Queue Manager) ---
    async def play_next(self, guild: discord.Guild, text_channel: discord.TextChannel = None):
        """
        หัวใจของระบบคิว: ถูกเรียกเมื่อเพลงจบ หรือเมื่อกด /skip
        """
        state = self.get_guild_state(guild.id)
        vc = discord.utils.get(self.bot.voice_clients, guild=guild)

        if not vc:
            return

        # ถ้ากำลัง stop อยู่ ไม่ต้องทำอะไร
        if state.get("is_stopping", False):
            return

        # ใช้ text_channel ที่เก็บไว้ถ้าไม่ได้ส่งมา
        if not text_channel:
            text_channel = state.get("text_channel")
        else:
            state["text_channel"] = text_channel

        if state["now_playing_message"]:
            try: 
                await state["now_playing_message"].delete()
            except discord.HTTPException: 
                pass
            state["now_playing_message"] = None

        # จัดการ Loop
        if state["loop"] and state["now_playing"]:
            # วนซ้ำเพลงเดิม
            queue_item = state["now_playing"]
        elif state["loop_queue"] and state["now_playing"]:
            # วนซ้ำคิว - เอาเพลงปัจจุบันไปต่อท้าย
            state["queue"].append(state["now_playing"])
            if not state["queue"]:
                state["now_playing"] = None
                await self.handle_empty_queue(vc, text_channel, state)
                return
            queue_item = state["queue"].pop(0)
        else:
            if not state["queue"]:
                state["now_playing"] = None
                await self.handle_empty_queue(vc, text_channel, state)
                return
            queue_item = state["queue"].pop(0)

        state["now_playing"] = queue_item
        player = queue_item["player"]
        requester = queue_item["requester"]
        
        # เล่นเพลง
        def after_playing(error):
            if error:
                print(f"Player error: {error}")
            # เช็กว่าไม่ได้กำลัง stop อยู่
            if not state.get("is_stopping", False):
                self.bot.loop.create_task(self.play_next(guild))
        
        vc.play(player, after=after_playing)
        
        # แสดง Embed
        embed = self.create_now_playing_embed(player, guild, requester, vc.channel)
        view = MusicPlayerView(self.bot, guild.id, self)
        
        if text_channel:
            state["now_playing_message"] = await text_channel.send(embed=embed, view=view)

    async def handle_empty_queue(self, vc: discord.VoiceClient, text_channel: discord.TextChannel, state: dict):
        """จัดการเมื่อคิวว่าง"""
        # ถ้ากำลัง stop อยู่ ไม่ต้องส่งข้อความ
        if state.get("is_stopping", False):
            return
        
        # รอ 15 วินาทีหลังเพลงจบ
        await asyncio.sleep(15)
        
        # เช็กว่ายังไม่มีเพลงใหม่
        if not state["queue"] and vc.is_connected() and not state.get("is_stopping", False):
            warning_messages = [
                "เพลงหมดแล้วไอ้หนุ่ม ไม่สั่งเพิ่มกูไปละนะ",
                "หมดเพลงแล้ว ถ้าไม่ใส่เพลงกูจะไปละนะ",
                "เฮ้ย! ไม่มีเพลงแล้ว อีก 15 วิกูไปละ",
                "คิวว่างเปล่า ไม่สั่งเพิ่มกูจะออกนะ",
                "ไม่มีเพลงแล้ว กูจะไปละ",
                "เพลงหมดคิวแล้ว ไม่ใส่เพิ่มกูไปจริงๆ นะ"
            ]
            
            warning_msg = random.choice(warning_messages)
            
            # ส่งข้อความเตือน
            if text_channel:
                await text_channel.send(warning_msg)
            
            # พูดเตือน (ถ้าเปิดใช้งาน)
            if self.use_custom_sound and vc.is_connected():
                await self.play_warning_sound(vc, warning_msg)
            
            # รออีก 15 วินาที
            await asyncio.sleep(15)
            
            # เช็กอีกทีว่ายังว่างอยู่ไหม
            if not state["queue"] and vc.is_connected() and not state.get("is_stopping", False):
                goodbye_messages = [
                    "บ๊ายบาย ไม่มีเพลงกูไปละ",
                    "เอาละ กูไปจริงๆ นะ",
                    "ไปก่อนไอ้หนุ่ม เรียกกูเมื่อไหร่ก็ได้"
                ]
                
                # ส่งข้อความลา
                if text_channel:
                    await text_channel.send(random.choice(goodbye_messages))
                
                # ออกจากช่องเลย (ไม่เล่นเสียง)
                try:
                    if vc.is_connected():
                        await vc.disconnect()
                except:
                    pass
    
    async def play_warning_sound(self, vc: discord.VoiceClient, text: str):
        """เล่นเสียงเตือน (ไม่ออกจากช่อง)"""
        try:
            if not vc or not vc.is_connected():
                return
            
            # หาไฟล์เสียงเตือน (ใช้ไฟล์เดียว)
            warning_file = "sounds/warning.mp3"
            
            if os.path.exists(warning_file):
                audio_source = discord.FFmpegPCMAudio(warning_file)
                vc.play(audio_source)
                
                # รอให้เล่นจบ (สูงสุด 10 วินาที)
                wait_time = 0
                while vc.is_playing() and wait_time < 10:
                    await asyncio.sleep(1)
                    wait_time += 1
        except Exception as e:
            print(f"Warning sound error: {e}")


    # --- คำสั่ง Slash Commands ---

    @app_commands.command(name="play", description="🎵 เล่นเพลงให้ฟัง | สั่งได้เลย")
    @app_commands.describe(search="ชื่อเพลง / ลิงก์ YouTube / Playlist")
    async def play(self, interaction: discord.Interaction, *, search: str):
        """(Slash Command) /play [search]"""
        
        if not interaction.user.voice:
            responses = [
                "เข้าช่องเสียงก่อนดิไอ้หนุ่ม ไม่งั้นกูจะเล่นให้ใครฟัง",
                "มึงไม่ได้อยู่ในช่องเสียงนะเว้ย เข้าก่อนสิ",
                "เฮ้ย! เข้าช่องเสียงก่อนสั่งกูสิ"
            ]
            await interaction.response.send_message(random.choice(responses), ephemeral=True)
            return

        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not vc:
            await interaction.user.voice.channel.connect()
            vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        elif vc.channel != interaction.user.voice.channel:
            await vc.move_to(interaction.user.voice.channel)

        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            state = self.get_guild_state(interaction.guild.id)
            state["text_channel"] = interaction.channel
            
            # ดึงข้อมูล (รองรับ playlist)
            loop = self.bot.loop
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
            
            songs_added = 0
            
            # เช็กว่าเป็น playlist หรือไม่
            if 'entries' in data:
                # เป็น Playlist
                await interaction.followup.send(f"🎵 เจอ Playlist! กำลังเพิ่ม {len(data['entries'])} เพลง...", ephemeral=True)
                
                for entry in data['entries']:
                    if entry:
                        try:
                            # ดึงข้อมูลเพลงแต่ละเพลง
                            song_data = await loop.run_in_executor(
                                None, 
                                lambda: ytdl.extract_info(entry['url'], download=False)
                            )
                            player = YTDLSource(
                                discord.FFmpegPCMAudio(song_data['url'], **ffmpeg_options),
                                data=song_data
                            )
                            
                            queue_item = {
                                "player": player,
                                "requester": interaction.user
                            }
                            state["queue"].append(queue_item)
                            songs_added += 1
                        except Exception as e:
                            print(f"Error adding song from playlist: {e}")
                            continue
                
                if songs_added > 0:
                    responses = [
                        f"จัดให้แล้ว {songs_added} เพลง! เตรียมเมาส์ไปเลย",
                        f"เพิ่ม {songs_added} เพลงเข้าคิวแล้ว ฟังกันยาวๆ เลย",
                        f"โอเค! ใส่ {songs_added} เพลงให้แล้ว เตรียมเต้นได้"
                    ]
                    await interaction.channel.send(random.choice(responses))
                    
                    if not vc.is_playing():
                        await self.play_next(interaction.guild, interaction.channel)
            else:
                # เพลงเดี่ยว
                player = YTDLSource(
                    discord.FFmpegPCMAudio(data['url'], **ffmpeg_options),
                    data=data
                )
                
                queue_item = {
                    "player": player,
                    "requester": interaction.user
                }

                if vc.is_playing() or vc.is_paused():
                    state["queue"].append(queue_item)
                    responses = [
                        f"เพิ่มเข้าคิวแล้ว: **{player.title}** - รออีกนิดนะไอ้หนุ่ม",
                        f"โอเค! ใส่ **{player.title}** เข้าคิวให้แล้ว",
                        f"จัดให้! **{player.title}** - เดี๋ยวถึงคิวมึง"
                    ]
                    await interaction.followup.send(random.choice(responses), ephemeral=True)
                else:
                    state["queue"].append(queue_item)
                    responses = [
                        f"จัดให้เลย: **{player.title}**",
                        f"เปิดให้ฟังแล้ว: **{player.title}**",
                        f"เล่นให้แล้วนะ: **{player.title}**"
                    ]
                    await interaction.followup.send(random.choice(responses), ephemeral=True)
                    await self.play_next(interaction.guild, interaction.channel)

        except Exception as e:
            print(f"Error in play command: {e}")
            error_responses = [
                f"เออเรอร์ว่ะ: {str(e)[:100]}",
                f"มีปัญหานิดหน่อย: {str(e)[:100]}",
                "เจอบั๊กแล้วไอ้หนุ่ม ลองใหม่ดิ"
            ]
            await interaction.followup.send(random.choice(error_responses), ephemeral=True)

    @app_commands.command(name="nowplaying", description="🎧 ดูเพลงที่กำลังเล่น")
    async def nowplaying(self, interaction: discord.Interaction):
        """(Slash Command) /nowplaying"""
        state = self.get_guild_state(interaction.guild.id)
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        
        if not vc or not vc.is_playing():
            await interaction.response.send_message("ไม่มีเพลงเล่นอยู่ตอนนี้", ephemeral=True)
            return
        
        if state["now_playing"]:
            player = state["now_playing"]["player"]
            requester = state["now_playing"]["requester"]
            embed = self.create_now_playing_embed(player, interaction.guild, requester, vc.channel)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("ไม่มีข้อมูลเพลง", ephemeral=True)

    @app_commands.command(name="queue", description="📋 ดูคิวเพลงทั้งหมด")
    async def queue(self, interaction: discord.Interaction):
        """(Slash Command) /queue"""
        state = self.get_guild_state(interaction.guild.id)
        
        embed = discord.Embed(
            title="🎵 คิวเพลง",
            color=0x5865F2
        )
        
        if not state["queue"] and not state["now_playing"]:
            embed.description = "ว่างเปล่า... เหมือนอนาคตมึงไงไอ้หนุ่ม"
        else:
            description = ""
            
            # แสดงเพลงที่กำลังเล่น
            if state["now_playing"]:
                player = state["now_playing"]["player"]
                description += f"**🎵 กำลังเล่น:**\n{player.title}\n\n"
            
            # แสดงคิว
            if state["queue"]:
                description += "**📋 ต่อคิว:**\n"
                for i, item in enumerate(state["queue"][:10], 1):
                    description += f"`{i}.` {item['player'].title}\n"
                
                if len(state["queue"]) > 10:
                    description += f"\n...และอีก {len(state['queue']) - 10} เพลง"
            
            embed.description = description
            
            # แสดงสถานะ Loop
            if state["loop"]:
                embed.set_footer(text="🔂 Loop: เพลงเดียว")
            elif state["loop_queue"]:
                embed.set_footer(text="🔁 Loop: ทั้งคิว")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="skip", description="⏭️ ข้ามเพลง | ไม่ชอบข้ามได้")
    async def skip(self, interaction: discord.Interaction):
        """(Slash Command) /skip"""
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        state = self.get_guild_state(interaction.guild.id)
        
        if not vc or not vc.is_connected():
            await interaction.response.send_message("กูไม่ได้อยู่ในช่องเสียง", ephemeral=True)
            return
            
        if vc.is_playing() or vc.is_paused():
            # เช็กว่ามีเพลงต่อไปไหม
            if state["queue"] or state["loop"] or state["loop_queue"]:
                responses = [
                    "ข้ามให้... ใจร้อนจริงมึง",
                    "โอเค ข้ามให้แล้ว",
                    "ไม่ชอบหรอ? ข้ามให้เลย"
                ]
            else:
                responses = [
                    "ข้ามให้ แต่ไม่มีเพลงต่อแล้วนะ",
                    "โอเค ข้าม แต่หมดคิวแล้ว",
                    "ข้ามเพลงสุดท้ายแล้ว"
                ]
            vc.stop()
            await interaction.response.send_message(random.choice(responses))
        else:
            await interaction.response.send_message("ไม่มีเพลงให้ข้าม", ephemeral=True)

    @app_commands.command(name="stop", description="⏹️ หยุดเพลง | ล้างคิวและออก")
    async def stop(self, interaction: discord.Interaction):
        """(Slash Command) /stop"""
        await self.stop_and_clear(interaction.guild, interaction)

    @app_commands.command(name="loop", description="🔂 วนซ้ำเพลงนี้")
    async def loop(self, interaction: discord.Interaction):
        """(Slash Command) /loop"""
        state = self.get_guild_state(interaction.guild.id)
        state["loop"] = not state["loop"]
        state["loop_queue"] = False  # ปิด loop queue
        
        if state["loop"]:
            await interaction.response.send_message("🔂 เปิดวนซ้ำเพลงนี้แล้ว")
        else:
            await interaction.response.send_message("⏹️ ปิดวนซ้ำแล้ว")

    @app_commands.command(name="loopqueue", description="🔁 วนซ้ำทั้งคิว")
    async def loopqueue(self, interaction: discord.Interaction):
        """(Slash Command) /loopqueue"""
        state = self.get_guild_state(interaction.guild.id)
        state["loop_queue"] = not state["loop_queue"]
        state["loop"] = False  # ปิด loop เพลงเดียว
        
        if state["loop_queue"]:
            await interaction.response.send_message("🔁 เปิดวนซ้ำทั้งคิวแล้ว")
        else:
            await interaction.response.send_message("⏹️ ปิดวนซ้ำแล้ว")

    @app_commands.command(name="clear", description="🗑️ ล้างคิวทั้งหมด")
    async def clear(self, interaction: discord.Interaction):
        """(Slash Command) /clear"""
        state = self.get_guild_state(interaction.guild.id)
        
        if not state["queue"]:
            await interaction.response.send_message("คิวว่างอยู่แล้ว ไม่มีอะไรให้ล้าง", ephemeral=True)
            return
        
        count = len(state["queue"])
        state["queue"].clear()
        responses = [
            f"ล้างคิวให้แล้ว {count} เพลง",
            f"โยนทิ้งไป {count} เพลง",
            f"เคลียร์ {count} เพลงให้แล้ว"
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="remove", description="❌ ลบเพลงในคิว")
    @app_commands.describe(position="ลำดับที่ต้องการลบ (1, 2, 3...)")
    async def remove(self, interaction: discord.Interaction, position: int):
        """(Slash Command) /remove [position]"""
        state = self.get_guild_state(interaction.guild.id)
        
        if not state["queue"]:
            await interaction.response.send_message("คิวว่างอยู่ ไม่มีอะไรให้ลบ", ephemeral=True)
            return
        
        if position < 1 or position > len(state["queue"]):
            await interaction.response.send_message(
                f"ใส่เลขผิดว่ะ ต้องเป็น 1-{len(state['queue'])}", 
                ephemeral=True
            )
            return
        
        removed = state["queue"].pop(position - 1)
        await interaction.response.send_message(
            f"ลบออกแล้ว: **{removed['player'].title}**"
        )

    @app_commands.command(name="shuffle", description="🔀 สับเปลี่ยนลำดับคิว")
    async def shuffle(self, interaction: discord.Interaction):
        """(Slash Command) /shuffle"""
        state = self.get_guild_state(interaction.guild.id)
        
        if len(state["queue"]) < 2:
            await interaction.response.send_message("ต้องมีอย่างน้อย 2 เพลงในคิว", ephemeral=True)
            return
        
        random.shuffle(state["queue"])
        responses = [
            f"สับเปลี่ยนคิวให้แล้ว {len(state['queue'])} เพลง",
            f"สุ่มลำดับให้แล้ว ดูซิจะได้เพลงไรก่อน",
            f"เชคเกอร์! สับ {len(state['queue'])} เพลงให้แล้ว"
        ]
        await interaction.response.send_message(random.choice(responses))

    @app_commands.command(name="help", description="❓ ดูคำสั่งทั้งหมด")
    async def help_command(self, interaction: discord.Interaction):
        """(Slash Command) /help"""
        embed = discord.Embed(
            title="🎵 คำสั่งบอทเพลง 4KINGS",
            description="สั่งกูได้ทุกอย่าง ไอ้หนุ่ม",
            color=0x5865F2
        )
        
        commands_list = [
            ("🎵 /play", "เล่นเพลง (ชื่อ/ลิงก์/Playlist)"),
            ("▶️ /nowplaying", "ดูเพลงที่กำลังเล่น"),
            ("📋 /queue", "ดูคิวเพลง"),
            ("⏭️ /skip", "ข้ามเพลง"),
            ("⏹️ /stop", "หยุดและออกจากช่อง"),
            ("🔂 /loop", "วนซ้ำเพลงปัจจุบัน"),
            ("🔁 /loopqueue", "วนซ้ำทั้งคิว"),
            ("🗑️ /clear", "ล้างคิวทั้งหมด"),
            ("❌ /remove", "ลบเพลงในคิว (ใส่ลำดับที่)"),
            ("🔀 /shuffle", "สับเปลี่ยนลำดับคิว"),
            ("❓ /help", "แสดงคำสั่งนี้"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="บอทนักเลง 4KINGS | สั่งกูได้")
        await interaction.response.send_message(embed=embed)

    # --- ฟังก์ชันตัวช่วยสำหรับปุ่ม Stop ---
    async def stop_and_clear(self, guild: discord.Guild, interaction: discord.Interaction = None):
        """หยุดเพลง, ล้างคิว, และออกจากช่อง"""
        vc = discord.utils.get(self.bot.voice_clients, guild=guild)
        state = self.get_guild_state(guild.id)

        # ตั้ง flag ว่ากำลัง stop เพื่อป้องกันข้อความซ้ำ
        state["is_stopping"] = True

        if state["now_playing_message"]:
            try: 
                await state["now_playing_message"].delete()
            except discord.HTTPException: 
                pass
            state["now_playing_message"] = None
        
        state["queue"].clear()
        state["now_playing"] = None
        state["loop"] = False
        state["loop_queue"] = False

        if vc:
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            await asyncio.sleep(0.5)  # รอให้ stop เสร็จ
            if vc.is_connected():
                await vc.disconnect()
        
        # รีเซ็ต flag หลังจากออกแล้ว
        state["is_stopping"] = False
        
        if interaction:
            responses = [
                "เออๆ หยุดก็หยุดวะ! ล้างคิวให้หมดแล้ว",
                "โอเค! หยุดให้แล้ว ไปก่อนนะ",
                "ปิดให้แล้ว บ๊ายบาย"
            ]
            await interaction.response.send_message(random.choice(responses))


# --- คำสั่ง "Setup" (เซ็ตอัป) ---
# นี่คือฟังก์ชันที่ main.py จะเรียกใช้
# เพื่อ "ลงทะเบียน" แผนกนี้กับบอท

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    print("Music cog has been set up.")