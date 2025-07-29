import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Configuración de logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Configuración de intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Diccionario para almacenar aniversarios
aniversarios = {}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    check_aniversarios.start()

def calculate_next_aniversario(original_date):
    now = datetime.now()
    # Primero intentamos con el mes actual
    next_date = original_date.replace(year=now.year, month=now.month)
    
    # Si ya pasó este mes, vamos al próximo
    if next_date < now:
        next_month = now.month + 1
        next_year = now.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        next_date = original_date.replace(year=next_year, month=next_month)
    
    # Ajuste para meses con menos días
    while True:
        try:
            next_date = next_date.replace(day=original_date.day)
            break
        except ValueError:
            next_date = next_date.replace(day=next_date.day-1)
    
    return next_date

def format_time_remaining(target_date):
    now = datetime.now()
    time_left = target_date - now
    
    if time_left.total_seconds() <= 0:
        return "¡Es hoy!"
    
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} día{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
    
    if not parts:
        return "¡Es ahora!"
    
    return ", ".join(parts)

@bot.command(name='aniversario')
async def set_aniversario(ctx, name1: str, name2: str, date: str, time: str):
    """Establece un nuevo aniversario mensual. Formato: !aniversario nombre1 nombre2 DD-MM-AAAA HH:MM"""
    try:
        date_time_str = f"{date} {time}"
        aniversario_fecha = datetime.strptime(date_time_str, "%d-%m-%Y %H:%M")
        
        if isinstance(ctx.channel, discord.ForumChannel):
            await ctx.send("❌ No se pueden configurar aniversarios en canales de foro. Usa un canal de texto.")
            return
            
        aniversarios[ctx.author.id] = {
            'names': [name1, name2],
            'date': aniversario_fecha,
            'channel_id': ctx.channel.id
        }

        next_aniversario = calculate_next_aniversario(aniversario_fecha)
        time_remaining = format_time_remaining(next_aniversario)

        await ctx.send(f"✅ Aniversario establecido para {name1} y {name2}!\n"
                      f"📅 Próximo mesaniversario: {next_aniversario.strftime('%d %B %Y a las %H:%M')}\n"
                      f"⏳ Faltan {time_remaining}")
    except ValueError as e:
        await ctx.send("❌ Formato incorrecto. Usa: !aniversario nombre1 nombre2 DD-MM-AAAA HH:MM")

@bot.command(name='removeraniversario')
async def remove_aniversario(ctx):
    """Elimina tu aniversario registrado"""
    if ctx.author.id in aniversarios:
        del aniversarios[ctx.author.id]
        await ctx.send("✅ Tu aniversario ha sido eliminado correctamente.")
    else:
        await ctx.send("❌ No tienes ningún aniversario registrado para eliminar.")

@bot.command(name='proximoaniversario')
async def next_anniversary(ctx):
    """Muestra cuándo es el próximo mesaniversario"""
    if ctx.author.id in aniversarios:
        data = aniversarios[ctx.author.id]
        next_date = calculate_next_aniversario(data['date'])
        time_remaining = format_time_remaining(next_date)
        
        await ctx.send(f"Próximo mesaniversario de {data['names'][0]} y {data['names'][1]}:\n"
                      f"📅 {next_date.strftime('%d %B %Y a las %H:%M')}\n"
                      f"⏳ Faltan {time_remaining}")
    else:
        await ctx.send("No tienes un aniversario configurado. Usa !aniversario para establecer uno.")

@tasks.loop(minutes=1)
async def check_aniversarios():
    now = datetime.now()
    for user_id, data in aniversarios.items():
        next_aniversario = calculate_next_aniversario(data['date'])

        if abs((next_aniversario - now).total_seconds()) <= 60:
            try:
                channel = bot.get_channel(data['channel_id'])
                
                if channel and isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
                    name1, name2 = data['names']
                    months_together = (now.year - data['date'].year) * 12 + (now.month - data['date'].month)
                    await channel.send(f"🎉 **¡Mesaniversario!** 🎉\n"
                                    f"<@{user_id}> {name1} y {name2} han estado juntos por {months_together} meses!\n"
                                    f"Desde el {data['date'].strftime('%d %B %Y')} 💖")
            except Exception as e:
                print(f"Error al enviar mensaje de aniversario: {e}")

bot.run('')
