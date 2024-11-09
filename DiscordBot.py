import discord
from discord.ext import commands
import youtube_dl

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Youtube_DL ayarları
youtube_dl.utils.bug_reports_message = lambda: ""
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 sorunları için
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Eğer playlist ise, sadece ilk girişi çal
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.command(name='play', help='Bir URL\'den müzik çalar')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("Bir ses kanalında olmalısınız!")
        return

    channel = ctx.message.author.voice.channel
    voice_client = await channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        voice_client.play(player, after=lambda e: print(f'Çalma hatası: {e}') if e else None)

    await ctx.send(f"Şu anda çalıyor: {player.title}")


@bot.command(name='stop', help='Müziği durdurur ve ses kanalından ayrılır')
async def stop(ctx):
    voice_client = ctx.voice_client
    if not voice_client:
        await ctx.send("Şu anda bir ses kanalında değilim.")
        return
    await voice_client.disconnect()


# Bot tokeninizi buraya ekleyin
TOKEN = 'TOKEN BURAYA!'
bot.run(TOKEN)

