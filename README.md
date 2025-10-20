# 🎵 บอทเพลง 4KINGS - สั่งกูได้

บอทเล่นเพลงสไตล์นักเลง สำหรับ Discord ที่มีฟีเจอร์ครบครัน

## ✨ ฟีเจอร์

### 🎵 เล่นเพลง
- `/play` - เล่นเพลงจาก YouTube (ชื่อเพลง, ลิงก์, หรือ Playlist)
- รองรับ YouTube Playlist (เพิ่มทีละหลายเพลง)
- ระบบคิวอัตโนมัติ
- แสดง Embed สวยงามพร้อมรูปภาพ

### 🎛️ ควบคุมเพลง
- `/nowplaying` - ดูเพลงที่กำลังเล่น
- `/skip` - ข้ามเพลง
- `/stop` - หยุดและออกจากช่อง
- ปุ่มควบคุม: Pause, Resume, Skip, Stop

### 📋 จัดการคิว
- `/queue` - ดูคิวเพลงทั้งหมด
- `/clear` - ล้างคิวทั้งหมด
- `/remove [ลำดับ]` - ลบเพลงในคิว
- `/shuffle` - สับเปลี่ยนลำดับคิว

### 🔁 วนซ้ำ
- `/loop` - วนซ้ำเพลงปัจจุบัน
- `/loopqueue` - วนซ้ำทั้งคิว

### 🤖 ระบบอัตโนมัติ
- **TTS (Text-to-Speech)** - เสียงพูดเตือนก่อนออกจากช่อง
- **Auto-disconnect** - ออกอัตโนมัติเมื่อไม่มีคนในช่อง
- **Auto-leave** - ออกเมื่อเพลงหมดและไม่มีการเพิ่มเพลงใน 2 นาที

### 💬 สไตล์ 4KINGS
- ข้อความตอบกลับแบบกวนๆ ตีนๆ
- สุ่มข้อความตอบกลับหลากหลาย
- บุคลิกนักเลงเก๋า

## 📦 การติดตั้ง

### 1. Clone โปรเจค
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. ติดตั้ง FFmpeg (สำคัญ!)
**Windows:**
```bash
choco install ffmpeg
```
หรือดาวน์โหลดจาก: https://ffmpeg.org/download.html

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

ดูคู่มือเต็มที่: [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md)

### 3. ติดตั้ง Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables
สร้างไฟล์ `.env`:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

### 5. รันบอท
```bash
python main.py
```

## 🚀 Deploy บน Render

1. สร้าง Web Service ใหม่บน Render
2. เชื่อมต่อกับ GitHub repository
3. ตั้งค่า:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. เพิ่ม Environment Variable: `DISCORD_TOKEN`
5. Deploy!

## 📝 คำสั่งทั้งหมด

| คำสั่ง | คำอธิบาย |
|--------|----------|
| `/play [ชื่อ/ลิงก์]` | เล่นเพลง (รองรับ Playlist) |
| `/nowplaying` | ดูเพลงที่กำลังเล่น |
| `/queue` | ดูคิวเพลง |
| `/skip` | ข้ามเพลง |
| `/stop` | หยุดและออกจากช่อง |
| `/loop` | วนซ้ำเพลงปัจจุบัน |
| `/loopqueue` | วนซ้ำทั้งคิว |
| `/clear` | ล้างคิว |
| `/remove [ลำดับ]` | ลบเพลงในคิว |
| `/shuffle` | สับเปลี่ยนลำดับคิว |
| `/help` | แสดงคำสั่งทั้งหมด |

## 🛠️ เทคโนโลยี

- **discord.py** - Discord Bot Framework
- **yt-dlp** - ดาวน์โหลดและสตรีมจาก YouTube
- **gTTS** - Text-to-Speech (เสียงพูดภาษาไทย)
- **Flask** - Keep-alive server สำหรับ Render
- **FFmpeg** - เล่นเสียง

## ⚙️ ความต้องการระบบ

- Python 3.8+
- **FFmpeg** (สำคัญ! ดูวิธีติดตั้งใน [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md))
- Discord Bot Token
- Internet connection

**หมายเหตุ:** 
- ไม่ต้องมีไฟล์ mp3 เพลง (streaming จาก YouTube)
- ไม่ต้องมีไฟล์เสียงพูด (สร้างอัตโนมัติด้วย gTTS)

## 🎯 ฟีเจอร์พิเศษ

### 🔊 TTS (Text-to-Speech)
บอทจะพูดเตือนก่อนออกจากช่องเสียง:
- "ถ้าไม่ใส่เพลงหนูจะไปละนะ"
- "บ๊ายบาย ไม่มีเพลงกูไปละ"
- "ไปก่อนไอ้หนุ่ม เรียกกูเมื่อไหร่ก็ได้"

### 🤖 Auto-disconnect
- ตรวจสอบทุก 1 นาทีว่ามีคนในช่องเสียงหรือไม่
- ออกอัตโนมัติเมื่อไม่มีคนฟัง
- ประหยัดทรัพยากร

### 📋 Playlist Support
- รองรับ YouTube Playlist
- เพิ่มเพลงทีละหลายเพลงพร้อมกัน
- แสดงจำนวนเพลงที่เพิ่ม

## 🐛 แก้ปัญหา

### บอทไม่เล่นเสียง
- ตรวจสอบว่าติดตั้ง FFmpeg แล้ว
- ตรวจสอบว่าบอทมีสิทธิ์เข้าช่องเสียง

### TTS ไม่ทำงาน
- ตรวจสอบว่าติดตั้ง gTTS แล้ว: `pip install gTTS`
- ตรวจสอบ internet connection

### Playlist ไม่โหลด
- ตรวจสอบว่า Playlist เป็น Public
- ลองใช้ลิงก์เพลงเดี่ยวแทน

## 📄 License

MIT License - ใช้ได้ตามสบาย

## 🤝 Contributing

Pull requests are welcome! สำหรับการเปลี่ยนแปลงใหญ่ กรุณาเปิด issue ก่อน

## 💡 ไอเดียพัฒนาต่อ

- [ ] Volume control (ปรับเสียง)
- [ ] Seek (กรอไปยังตำแหน่งในเพลง)
- [ ] Lyrics (แสดงเนื้อเพลง)
- [ ] Favorites (บันทึกเพลงโปรด)
- [ ] DJ Mode (โหมด DJ อัตโนมัติ)
- [ ] Web Dashboard (หน้าเว็บควบคุม)

---

**สั่งกูได้** - บอทนักเลง 4KINGS 🎵
