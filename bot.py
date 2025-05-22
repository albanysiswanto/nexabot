import os
import json
import re
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask
import threading

# Inisialisasi Flask untuk hosting di Railway
load_dotenv()
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

@app.route("/ping")
def flask_ping():
    return "Ping received from UptimeRobot!"

def run_flask():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5050))
    app.run(host=host, port=port)

# Membaca daftar kata-kata toxic dari file JSON
try:
    with open('toxic_words_indonesia.json', 'r') as file:
        data = json.load(file)
        TOXIC_WORDS = set(data['toxic_words'])
except FileNotFoundError:
    print("Error: File 'toxic_words_indonesia.json' tidak ditemukan. Pastikan file ada di direktori yang sama dengan bot.py.")
    TOXIC_WORDS = set()
except KeyError:
    print("Error: Format 'toxic_words_indonesia.json' tidak valid. Pastikan ada key 'toxic_words' yang berisi list kata-kata.")
    TOXIC_WORDS = set()

# Membuat pola regex untuk mencocokkan kata-kata toxic dengan batasan kata
def create_toxic_pattern():
    # Escaping kata-kata toxic untuk regex dan tambahkan word boundaries (\b)
    escaped_words = [re.escape(word) for word in TOXIC_WORDS]
    # Gabungkan semua kata dengan OR (|) untuk regex
    pattern = r'\b(' + '|'.join(escaped_words) + r')\b'
    return re.compile(pattern, re.IGNORECASE)

toxic_pattern = create_toxic_pattern() if TOXIC_WORDS else None

# Inisialisasi bot Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary untuk menyimpan channel log per server
log_channels = {}

# Event: Bot siap
@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online!")

# Perintah: Ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Perintah: Kick member
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.name} telah dikick dari server. Alasan: {reason or "Tidak ada alasan"}')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} telah mengkick {member.name}. Alasan: {reason or "Tidak ada alasan"}')

# Perintah: Ban member
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.name} telah diban dari server. Alasan: {reason or "Tidak ada alasan"}')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} telah memban {member.name}. Alasan: {reason or "Tidak ada alasan"}')

# Perintah: Membuat pengumuman
@bot.command()
@commands.has_permissions(manage_messages=True)
async def announce(ctx, channel: discord.TextChannel, *, message):
    await channel.send(f'📢 **Pengumuman**: \n\n {message}')
    await ctx.send('Pengumuman telah dikirim!')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} telah membuat pengumuman di {channel.mention}. Pesan: {message}')

# Perintah: Memberi peringatan (dikirim via DM)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason):
    try:
        await member.send(f'Kamu mendapat peringatan dari server {ctx.guild.name} karena: {reason}')
        await ctx.send(f'Peringatan telah dikirim ke DM {member.name}.')
        log_channel = log_channels.get(ctx.guild.id)
        if log_channel:
            await log_channel.send(f'**Log**: {ctx.author.name} telah memperingatkan {member.name} (via DM). Alasan: {reason}')
    except discord.Forbidden:
        await ctx.send(f'Gagal mengirim peringatan ke DM {member.name}. Pengguna mungkin menutup DM atau bot tidak memiliki izin.')
    except discord.HTTPException as e:
        await ctx.send(f'Terjadi kesalahan saat mengirim DM ke {member.name}: {e}')

# Perintah: Menampilkan jumlah member
@bot.command()
async def membercount(ctx):
    guild = ctx.guild
    total_members = guild.member_count
    await ctx.send(f'Member Total: {total_members}')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} memeriksa jumlah member. Total: {total_members}')

# Perintah: Memberi role
@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f'Role {role.name} telah diberikan kepada {member.name}')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} telah memberikan role {role.name} kepada {member.name}')

# Perintah: Menghapus role
@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f'Role {role.name} telah dihapus dari {member.name}')
    log_channel = log_channels.get(ctx.guild.id)
    if log_channel:
        await log_channel.send(f'**Log**: {ctx.author.name} telah menghapus role {role.name} dari {member.name}')

# Perintah: Mengatur channel log
@bot.command()
@commands.has_permissions(manage_messages=True)
async def setuplog(ctx, channel: discord.TextChannel):
    log_channels[ctx.guild.id] = channel
    await ctx.send(f'Channel log telah disetel ke {channel.mention}. Semua aktivitas akan dicatat di sini.')

# Penanganan error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Kamu tidak memiliki izin untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Perintah tidak lengkap. Silakan cek ulang formatnya.')
    else:
        await ctx.send(f'Terjadi kesalahan: {error}')

# Event: Deteksi pesan toxic
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Deteksi kata toxic menggunakan regex
    content = message.content
    if toxic_pattern and toxic_pattern.search(content):
        await message.delete()
        await message.channel.send(f'{message.author.mention}, pesan Anda telah dihapus karena mengandung kata toxic. Harap hindari penggunaan bahasa tersebut!')
        log_channel = log_channels.get(message.guild.id)
        if log_channel:
            await log_channel.send(f'**Log**: Pesan dari {message.author.name} dihapus karena mengandung kata toxic: "{message.content}"')

    await bot.process_commands(message)

# Menjalankan Flask di thread terpisah
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Menjalankan bot
token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    raise ValueError("Environment variable bot_TOKEN belum di-set!")
bot.run(token)
