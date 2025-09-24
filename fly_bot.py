import discord
import json
from discord import app_commands
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# ------------ ENVIRONMENT -----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SPREADSHEET_ID = "1BMfeBceFx9wRDHvuyYyzcRb03aJNrBbRqCEYPG-0QBw"
LINK_SHEET = "https://docs.google.com/spreadsheets/d/1BMfeBceFx9wRDHvuyYyzcRb03aJNrBbRqCEYPG-0QBw/edit?gid=1348196106#gid=1348196106"

# ------------ GOOGLE SHEET -----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

google_credentials = os.getenv("GOOGLE_CREDENTIALS")
if not google_credentials:
    raise ValueError("Thiếu biến môi trường GOOGLE_CREDENTIALS")

# Convert chuỗi JSON trong Railway thành dict
creds_info = json.loads(google_credentials)

CREDS = service_account.Credentials.from_service_account_info(
    creds_info, scopes=SCOPES
)

service = build('sheets', 'v4', credentials=CREDS)

def append_to_sheet(sheet_name, values):
    body = {"values": [values]}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

# ------------ DISCORD SETUP -----------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

user_tasks = {}  # user_id: {sheet, ngày, số_lượng, images[], channel}

# ------------ ROLE CHECK -----------------
async def has_pilot_role(interaction: discord.Interaction):
    member = await interaction.guild.fetch_member(interaction.user.id)
    return any(role.name.lower() == 'pilot' for role in member.roles)

# ------------ KÉO MAN -----------------
@tree.command(name="keo-man", description="Ghi chú Kéo Man Rợ (ngày + số lượng)")
@app_commands.describe(ngay="Ngày (VD: 20/7/2025)", so_luong="Số lượng man rợ đã kéo")
async def keo_man(interaction: discord.Interaction, ngay: str, so_luong: int):
    if not await has_pilot_role(interaction):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ Bạn cần role **Pilot** để dùng lệnh này.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    await interaction.followup.send("Gửi ảnh chuỗi man rợ, nhắn `done` khi xong.")
    user_tasks[interaction.user.id] = {
        "sheet": "Kéo man",
        "ngay": ngay,
        "so_luong": so_luong,
        "images": [],
        "channel": interaction.channel
    }

# ------------ WAR GIỜ -----------------
@tree.command(name="war-gio", description="Ghi chú WAR kiểu Giờ (ngày + giờ + phút)")
@app_commands.describe(ngay="Ngày (VD: 20/7/2025)", gio="Số giờ tham gia", phut="Số phút tham gia")
async def war_gio(interaction: discord.Interaction, ngay: str, gio: int, phut: int):
    if not await has_pilot_role(interaction):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ Bạn cần role **Pilot** để dùng lệnh này.", ephemeral=True)
        return
    if gio < 0 or phut < 0 or (gio == 0 and phut == 0):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ Phải nhập giờ hoặc phút > 0.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    await interaction.followup.send("Gửi ảnh KP ban đầu, KP lúc hoàn thành, Kill và Heal trước sau, nhắn `done` khi xong.")
    so_luong = f"{gio}h{phut}p"
    user_tasks[interaction.user.id] = {
        "sheet": "War - Giờ",
        "ngay": ngay,
        "so_luong": so_luong,
        "images": [],
        "channel": interaction.channel
    }

# ------------ WAR KP -----------------
@tree.command(name="war-kp", description="Ghi chú WAR kiểu KP (ngày + KP số nguyên)")
@app_commands.describe(ngay="Ngày (VD: 20/7/2025)", kp="Số KP (chỉ nhập số, VD: 200 hoặc 200000000)")
async def war_kp(interaction: discord.Interaction, ngay: str, kp: int):
    if not await has_pilot_role(interaction):
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ Bạn cần role **Pilot** để dùng lệnh này.", ephemeral=True)
        return
    if kp <= 0:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("❌ KP phải > 0.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    await interaction.followup.send("Gửi ảnh KP ban đầu, KP lúc hoàn thành, Kill và Heal trước sau, nhắn `done` khi xong.")
    user_tasks[interaction.user.id] = {
        "sheet": "War - KP",
        "ngay": ngay,
        "so_luong": str(kp),  # lưu đúng số user nhập
        "images": [],
        "channel": interaction.channel
    }


# ------------ BỆ THỜ -----------------
@tree.command(name="be-tho", description="Ghi chú Bệ Thờ (ngày + giờ + phút)")
@app_commands.describe(ngay="Ngày (VD: 20/7/2025)", gio="Giờ (>= 0)", phut="Phút (>= 0)")
async def be_tho(interaction: discord.Interaction, ngay: str, gio: int = 0, phut: int = 0):
    if not await has_pilot_role(interaction):
        await interaction.response.send_message("❌ Bạn cần role **Pilot** để dùng lệnh này.", ephemeral=True)
        return
    if gio < 0 or phut < 0:
        await interaction.response.send_message("❌ Giờ và phút không được âm.", ephemeral=True)
        return
    if gio == 0 and phut == 0:
        await interaction.response.send_message("❌ Phải nhập giờ hoặc phút > 0.", ephemeral=True)
        return

    await interaction.response.defer()
    append_to_sheet("Bệ thờ", [ngay, interaction.user.name, gio, phut, f"#{interaction.channel.name}"])
    await interaction.followup.send("✅ Đã ghi nhận Bệ Thờ!")

# ------------ ARK -----------------
@tree.command(name="ark", description="Ghi chú Ark (chỉ cần ngày)")
@app_commands.describe(ngay="Ngày (VD: 20/7/2025)")
async def ark(interaction: discord.Interaction, ngay: str):
    if not await has_pilot_role(interaction):
        await interaction.response.send_message("❌ Bạn cần role **Pilot** để dùng lệnh này.", ephemeral=True)
        return
    await interaction.response.defer()
    append_to_sheet("Ark", [ngay, interaction.user.name, f"#{interaction.channel.name}"])
    await interaction.followup.send("✅ Đã ghi nhận Ark!")

# ------------ XEM SHEET -----------------
@tree.command(name="xem-sheet", description="Xem link Google Sheet")
async def xem_sheet(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.followup.send("❌ Bạn không đủ quyền để xem Google Sheet này.", ephemeral=True)
        return
    await interaction.followup.send(f"📄 Link tổng hợp: {LINK_SHEET}", ephemeral=True)

# ------------ NHẬN ẢNH + DONE -----------------
@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id in user_tasks:
        task = user_tasks[user_id]
        if message.channel != task["channel"]:
            return

        if message.content.strip().lower() == "done":
            links = [f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{msg.id}" for msg in task["images"]]
            append_to_sheet(task["sheet"], [
                task["ngay"],
                message.author.name,
                task["so_luong"],
                f"#{message.channel.name}",
                ", ".join(links) if links else "Không gửi ảnh"
            ])
            await message.channel.send("✅ Đã ghi nhận xong và lưu vào Google Sheet.")
            del user_tasks[user_id]
            return

        if message.attachments:
            task["images"].append(message)

# ------------ READY -----------------
@client.event
async def on_ready():
    await tree.sync()
    print(f"{client.user} is ready!")

# ------------ KEEP ALIVE -----------------
from keep_alive import keep_alive
keep_alive()

client.run(TOKEN)
