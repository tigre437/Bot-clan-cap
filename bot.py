from socket import timeout
import discord
import mysql.connector
import os
import asyncio
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext.commands import has_permissions, CheckFailure
from discord.ext import commands
from discord.utils import get, sleep_until
import time
import os
import json
import random
from random import randrange
from discord.ext.commands import Bot
from discord import Member
import datetime
from datetime import datetime
from discord import ui
import requests
import io
import subprocess
import psutil
import chat_exporter
from chat_exporter import AttachmentToDiscordChannelHandler


intents = discord.Intents.all()
intents.members = True

server = '127.0.0.1'
db = 'discord_bot'
usuario = 'root'
contraseña = 'ClanCapBoel2023'

TOKEN = "CAMBIAR TOKEN"

ID_PLMM = 766976837288460309 # ID del rol de PLMM 751822419400065085
ID_LOGS = 1285260088923258994 # ID del canal de logs 768731234398240788
ID_MULTICLAN = 1129875148594499675 # ID del canal de multiclan
ID_MIEMBRO = 345987030125248512 # ID del rol de miembro
ID_CANAL_MIEMBROS = 742859980058918999 # ID del canal de miembros

IGNORED_ROLES = [
    1065575164810645604, # ROL AV 
    622556649378545685,  # ROL reservista
    348617944449810433   # ROL invitado
]


try:
    db = mysql.connector.connect(user=usuario, password=contraseña,host=server,database=db)
    cursor = db.cursor()
    print("the database has been connected successfully")
except Exception as e:
    print(f"The database could not be connected successfully due to the following error: {e}")
    
DEFAULT_PREFIX = 't!'

async def command_prefix(bot: commands.Bot, msg: discord.Message):
    cursor.execute(f"SELECT server_prefix FROM prefix WHERE server_id = %s",(msg.guild.id, ))
    prefix = cursor.fetchone()
    if prefix != None:
        prefix = prefix[0]
        return prefix
        
    else:
        return DEFAULT_PREFIX
    
class button4(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        
        
    @discord.ui.button(label = 'Reabrir', style = discord.ButtonStyle.gray, emoji = '🔓', custom_id='persistent_view:reabrir')
    async def confirm(self, interaction:discord.Interaction, button: discord.ui.Button):
        try:
            role = discord.utils.get(interaction.guild.roles, id=ID_PLMM)
            if role in interaction.user.roles:
                cursor.execute(f"SELECT id_panel FROM ticket WHERE id_ticket = %s", (interaction.channel.id, ))
                panel = cursor.fetchone()
                panel = panel[0]
                print(panel)
                cursor.execute(f"SELECT id_category_open FROM ticket_config WHERE id_panel = %s", (panel, ))
                categoria = cursor.fetchone()
                categoria = categoria[0]
                categoria = discord.utils.get(interaction.guild.channels, id=categoria)
                cursor.execute(f"SELECT id_autor FROM ticket WHERE id_ticket = %s", (interaction.channel.id, ))
                autor = cursor.fetchone()
                autor = autor[0]
                member = discord.utils.get(interaction.guild.members, id=autor)
                await interaction.channel.set_permissions(member, read_messages=True,send_messages=True, read_message_history=True, attach_files=True, add_reactions=True)
                await interaction.channel.edit(category = categoria, end = True, reason = "ticket reabierto")
                view = button2()
                await interaction.message.edit(view = view)
                await interaction.response.send_message("Ticket reabierto", ephemeral=True)
            else:
                await interaction.response.send_message("Esta opcion solo esta disponible para PLMM", ephemeral = True)
            
        except Exception as e:
            raise e
        
    @discord.ui.button(label = 'Borrar', style = discord.ButtonStyle.gray, emoji = '⛔', custom_id='persistent_view:borrar')
    async def confirm2(self, interaction:discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message("El ticket será borrado en 10 segundos")
            await asyncio.sleep(10)
            await interaction.channel.delete()
        except Exception as e:
            raise e
        
    @discord.ui.button(label = 'Logs', style = discord.ButtonStyle.gray, emoji = '📋', custom_id='persistent_view:logs', disabled=True)
    async def confirm3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("En proceso")
    
class button(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @discord.ui.button(label='Abrir ticket', style=discord.ButtonStyle.red, emoji = '📩', custom_id='persistent_view:abrir')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            cursor.execute(f"SELECT id_category_open FROM ticket_config WHERE id_panel = %s", (interaction.message.id, ))
            categoria = cursor.fetchone()
            categoria = categoria [0]
            cursor.execute(f"SELECT COUNT(id_ticket) FROM ticket WHERE id_server = %s", (interaction.guild.id, ))
            ticket_number = cursor.fetchone()
            ticket_number = ticket_number[0]
            if ticket_number == None:
                ticket_number = 1
            else:
                ticket_number += 1
            cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s",(interaction.message.id, "permision"))
            ids = cursor.fetchall()

            category = discord.utils.get(interaction.guild.categories, id=int(categoria))
            ticket_channel = await interaction.guild.create_text_channel("ticket {}".format(ticket_number), category=category)
            embed = discord.Embed(
                    title = "Ticket creado",
                    description = f"Su ticket a sido creado en {ticket_channel.mention}",
                    color = 0x0080FF
                )
            cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s",(interaction.message.id, "mention"))
            ids = cursor.fetchall()
            for id in ids:
                role = discord.utils.get(interaction.guild.roles, id=int(id[0]))
                mensaje = await ticket_channel.send(f"{role.mention}")
                await mensaje.delete()
            await interaction.response.send_message(embed=embed, ephemeral = True)
            await ticket_channel.set_permissions(interaction.user, read_messages=True,send_messages=True, read_message_history=True, attach_files=True, add_reactions=True)
            try:
                cursor.execute("INSERT INTO ticket (id_ticket, id_autor, id_server, id_panel) VALUES (%s,%s,%s,%s)", (ticket_channel.id, interaction.user.id, interaction.guild.id, interaction.message.id))
                db.commit()
            except Exception as e:
                raise e

            for id in ids:
                role = discord.utils.get(interaction.guild.roles, id=int(id[0]))
                await ticket_channel.set_permissions(role, read_messages=True,send_messages=True, read_message_history=True, attach_files=True, add_reactions=True)
            embed = discord.Embed(
                title= "Sistema de ticket",
                description = "Muchas gracias por contactar con nuestra administración",
                color = 0x2EFE2E
            )
            view = button2()
            await ticket_channel.send(embed = embed, view = view)
        except Exception as e:
            raise e

class button2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None
        
    
    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.gray, emoji="❌", custom_id='persistent_view:cerrar')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, id=ID_PLMM)  # Reemplaza con el ID del rol
        if role in interaction.user.roles:
            canal = interaction.channel.id
            cursor.execute(f"SELECT id_autor FROM ticket WHERE id_ticket = %s", (canal,))
            usuario = cursor.fetchone()
            cursor.execute(f"SELECT id_panel FROM ticket WHERE id_ticket = %s", (canal,))
            panel = cursor.fetchone()
            cursor.execute(f"SELECT id_category_close FROM ticket_config WHERE id_panel = %s", (panel[0],))
            category = cursor.fetchone()
            category = discord.utils.get(interaction.guild.channels, id=int(category[0]))
            member = discord.utils.get(interaction.guild.members, id=usuario[0])

            # Enviar notificación de cierre al autor del ticket
            embed = discord.Embed(
                title=f"{interaction.channel.name}",
                description=f"Su ticket ha sido cerrado por {interaction.user.display_name}",
                color=0xFF0000
            )
            try:
                await member.send(embed=embed)
            except:
                await interaction.channel.send(embed=embed)

            await interaction.response.send_message("Se está generando la transcripcion, espere porfavor", ephemeral=True)

            # Exportar la conversación incluyendo adjuntos usando el handler
            log_channel = bot.get_channel(ID_LOGS)  # Reemplaza con el ID del canal de logs
            try:
                # Establish the file handler
                channel_handler = AttachmentToDiscordChannelHandler(
                    channel=log_channel,
                )
                transcript = await chat_exporter.export(
                    interaction.channel,
                    attachment_handler=channel_handler
                )
                
                if transcript:
                    # Crear un buffer de bytes para la transcripción
                    transcript_bytes = transcript.encode()
                    
                    # Crear el archivo HTML de la transcripción para enviar al usuario
                    transcript_file_user = discord.File(io.BytesIO(transcript_bytes), filename=f"transcript-{interaction.channel.name}.html")

                    # Crear una copia del archivo HTML para enviar al canal de logs
                    transcript_file_log = discord.File(io.BytesIO(transcript_bytes), filename=f"transcript-{interaction.channel.name}.html")

                    # Enviar el archivo exportado al autor del ticket por privado
                    try:
                        await member.send(content="Aquí está el archivo de la conversación de su ticket cerrado.", file=transcript_file_user)
                    except:
                        await interaction.channel.send("No se pudo enviar la transcripción al usuario.")

                    # Enviar el archivo exportado al canal de logs usando la copia
                    if log_channel:
                        await log_channel.send(content=f"Transcripción del ticket {interaction.channel.name} abierto por {member.display_name} y cerrado por {interaction.user.display_name}.", file=transcript_file_log)
                else:
                    # Si no se genera la transcripción, notificar y no cerrar el canal
                    await interaction.channel.send("No se pudo generar la transcripción. El ticket no será cerrado.")
                    return

            except Exception as e:
                # Capturar cualquier error durante la exportación y notificar al canal
                await interaction.channel.send(f"Ocurrió un error al exportar la conversación: {str(e)}. El ticket no será cerrado.")
                return

            # Si todo salió bien, cerrar el canal
            await interaction.channel.send("El ticket ha sido cerrado y la conversación exportada con éxito.")
            await interaction.channel.delete(reason="Ticket cerrado")
            

        else:
            await interaction.response.send_message("Esta opción solo está disponible para PLMM", ephemeral=True)
    

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True

        DEFAULT_PREFIX = 't!'

        async def command_prefix(bot: commands.Bot, msg: discord.Message):
            cursor.execute(f"SELECT server_prefix FROM prefix WHERE server_id = %s",(msg.guild.id, ))
            prefix = cursor.fetchone()
            if prefix != None:
                prefix = prefix[0]
                return prefix 
            else:
                return DEFAULT_PREFIX

        super().__init__(command_prefix=command_prefix, intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(button())
        self.add_view(button2())
        self.add_view(button4())



bot = PersistentViewBot()
bot.remove_command("help")


@bot.event
async def on_ready():
    print("Bot operational and working")
    await bot.change_presence(activity=discord.Game(name="default prefix = t!"))
    await send_message_at_9()



@bot.event
async def on_member_join(member):
    embed = discord.Embed(
            title="Bienvenido al clan cap",
            description="Te doy la bienvenida a nuestro clan de arma 3, en la mayor brevedad posible un recepcionista se pondrá en contacto contigo, en este [canal](https://discordapp.com/channels/345463885425541121/362124291430547456) tienes el pdf de bienvenida, en el tendrás todo lo necesario para entrar al clan. ¡Espero que nos veamos pronto!",
            color=0x000000
        )
    embed.add_field(name="Importante", value="No escribas por privado a ningun miembro del clan a menos de que el lo haga primero")
    embed.add_field(name="¿Tienes dudas?", value="Puedes hacerlas en este [canal](https://discordapp.com/channels/345463885425541121/815242793458728960) sin ninguna vergüenza")
    embed.set_thumbnail(url="https://i1.wp.com/www.clan-cap.es/wp-content/uploads/2019/02/cropped-cropped-cropped-cropped-cropped-cropped-emblema-de-brazo-20192-2.png?fit=1708%2C1920&ssl=1")
    embed.set_footer(text="Clan CAP 2023 | bot developed by tigre", icon_url="https://i1.wp.com/www.clan-cap.es/wp-content/uploads/2019/02/cropped-cropped-cropped-cropped-cropped-cropped-emblema-de-brazo-20192-2.png?fit=1708%2C1920&ssl=1")
    await member.send(embed = embed)
    cursor.execute(f"INSERT INTO registro (id_user, fecha_entrada) VALUES (%s, %s)", (member.name, datetime.now()))
    db.commit()
    
    
@bot.event
async def on_member_remove(member):
    hora = datetime.now()
    cursor.execute(f"UPDATE registro SET fecha_salida = %s WHERE id_user = %s", (hora, member.id, ))
    db.commit()
    
@bot.command()
async def registros(ctx):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        cursor.execute(f"SELECT id_user FROM registro")
        lista_entradas = cursor.fetchall()
        lista_entradas = list(lista_entradas[0])
        
        cursor.execute(f"SELECT fecha_entrada FROM registro")
        lista_fechaent = cursor.fetchall()
        lista_fechaent = list(lista_fechaent[0])
        
        cursor.execute(f"SELECT fecha_salida FROM registro")
        lista_fechasal = cursor.fetchall()
        lista_fechasal = list(lista_fechasal[0])
        
        
        for i in range(len(lista_entradas)):
            print(i)
            await ctx.send(lista_entradas[i] + " entro el "+lista_fechaent[i]+" y salio el "+lista_fechasal[i])
    

@bot.command()
async def addword(ctx, palabra):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        print(palabra)
        cursor.execute(f"INSERT INTO palabras (id_server, palabra) VALUES (%s, %s)", (ctx.guild.id, palabra))
        db.commit()
    
@bot.command()
async def votaciones(ctx, mensaje: discord.Message):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if role not in ctx.author.roles:
        await ctx.send("No eres PLMM")
    else:
        lista_miembros = []  # lista de miembros oficiales
        lista_miembros_1 = []  # lista de miembros que han votado
        lista_miembros_2 = []  # lista de miembros que no han votado
        role = discord.utils.get(ctx.guild.roles, id=ID_MIEMBRO)  # ROL CAP 345987030125248512
        
        for member in ctx.guild.members:
            # Excluir miembros con roles en la lista IGNORED_ROLES
            tiene_roles_ignorados = any(
                discord.utils.get(ctx.guild.roles, id=role_id) in member.roles for role_id in IGNORED_ROLES
            )
            if role in member.roles and not tiene_roles_ignorados:
                lista_miembros.append(member.display_name)
        
        embeds = mensaje.embeds
        for embed in embeds:
            for field in embed.fields:
                try:
                    if "No asisto" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    elif "Llego tarde" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    else:
                        index_i = field.value.index("<")
                        index_f = field.value.index(">")
                        cadena = field.value
                        sub_chane = cadena[index_i:index_f+2]

                    cadena = cadena.replace(sub_chane, "")

                    for member in lista_miembros:
                        if member in cadena:
                            lista_miembros_1.append(member)
                except Exception as e:
                    print(e)
                    await ctx.send(f"El campo de {field.name} estaba vacío")

            for field in embed.fields:
                try:
                    if "No asisto" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    elif "Llego tarde" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    else:
                        index_i = field.value.index("<")
                        index_f = field.value.index(">")
                        cadena = field.value
                        sub_chane = cadena[index_i:index_f+2]

                    cadena = cadena.replace(sub_chane, "")

                    for member in lista_miembros:
                        if member not in lista_miembros_1:
                            if member not in lista_miembros_2:
                                lista_miembros_2.append(member)

                except Exception as e:
                    print(e)
                    await ctx.send(f"En {field.name} no han votado")

            await ctx.send(lista_miembros_2)


@bot.command()
async def asistencia(ctx, mensaje: discord.Message):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if role not in ctx.author.roles:
        await ctx.send("No eres PLMM")
    else:
        lista_miembros = []  # lista de miembros oficiales
        lista_miembros_1 = []  # lista de miembros que han votado
        lista_miembros_2 = []  # lista de miembros que no han votado
        role = discord.utils.get(ctx.guild.roles, id=ID_MIEMBRO)  # ROL CAP
        
        # Excluir miembros con roles en la lista IGNORED_ROLES
        for member in ctx.guild.members:
            tiene_roles_ignorados = any(
                discord.utils.get(ctx.guild.roles, id=role_id) in member.roles for role_id in IGNORED_ROLES
            )
            if role in member.roles and not tiene_roles_ignorados:
                lista_miembros.append(member.display_name)
        
        embeds = mensaje.embeds
        for embed in embeds:
            for field in embed.fields:
                try:
                    if "No asisto" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    elif "Llego tarde" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    else:
                        index_i = field.value.index("<")
                        index_f = field.value.index(">")
                        cadena = field.value
                        sub_chane = cadena[index_i:index_f+2]

                    cadena = cadena.replace(sub_chane, "")

                    for member in lista_miembros:
                        if member in cadena:
                            lista_miembros_1.append(member)
                except Exception as e:
                    print(e)
                    await ctx.send(f"El campo de {field.name} estaba vacío")

            for field in embed.fields:
                try:
                    if "No asisto" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    elif "Llego tarde" in field.name:
                        cadena = field.value
                        sub_chane = cadena[0:1]
                    else:
                        index_i = field.value.index("<")
                        index_f = field.value.index(">")
                        cadena = field.value
                        sub_chane = cadena[index_i:index_f+2]

                    cadena = cadena.replace(sub_chane, "")

                    for member in lista_miembros:
                        if member not in lista_miembros_1:
                            if member not in lista_miembros_2:
                                lista_miembros_2.append(member)

                except Exception as e:
                    print(e)
                    await ctx.send(f"En {field.name} no han votado")

        # Si el embed no tiene color o es rojo, se envían notificaciones
        if embed.color is None:
            for member in lista_miembros_2:
                try:
                    member_obj = ctx.guild.get_member_named(member)
                    if member_obj and member_obj.id != ctx.author.id:
                        await member_obj.send(f"{member_obj.mention}, recuerda votar en la {embed.title}")
                        await ctx.send(f"Se ha notificado a {member_obj.display_name}")
                except Exception as e:
                    await ctx.send(f"No se ha podido notificar a {member}")
                    print(e)
                    print(member)

        elif str(embed.color) == "#ff0000":
            for member in lista_miembros_2:
                try:
                    member_obj = ctx.guild.get_member_named(member)
                    if member_obj:
                        await member_obj.send(f"{member_obj.mention}, no has votado en {embed.title} a tiempo, esto conllevará una falta")
                        await ctx.send(f"Se ha notificado a {member_obj.display_name} que se llevará una falta")
                except Exception as e:
                    await ctx.send(f"No se ha podido notificar a {member}")
                    print(e)
                    print(member)

        await ctx.send(lista_miembros_2)

@bot.command()
async def mencionar(ctx):
   
    await ctx.author.send(f"{ctx.author.mention}, no has votado a tiempo, esto conllevará una falta")


@bot.command()
async def clear(ctx, amount: int):
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.channel.purge(limit=amount)
        await ctx.send(f"{amount} mensajes borrados", delete_after = 2)

@bot.command()
async def changeprefix(ctx, prefix):
    try:
        role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
        if ( role not in ctx.author.roles):
            await ctx.send("No eres PLMM")
        else:
            await ctx.message.delete()
            try:
                cursor.execute(f"UPDATE prefix SET server_prefix = %s WHERE server_id = %s", (prefix, ctx.guild.id))
                db.commit()
            except Exception as e:
                cursor.execute(f"INSERT INTO prefix (server_id, server_prefix) values (%s, %s)", (ctx.guild.id, prefix))
                db.commit()
                raise e
            await ctx.send("Prefijo cambiado exitosamente")
    except Exception as e:
        raise e

@bot.command()
async def autorole(ctx, canal: discord.TextChannel = None, role: discord.Role = None, emogi = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if canal == None:
            await ctx.send("Se te olvido especificar el canal")
        elif role == None:
            await ctx.send("Se te olvido especificar el rol despues del canal")
        elif emogi == None:
            await ctx.send("No especificastes el emogi despues del rol")
        else:

            await ctx.message.delete()

            embed = discord.Embed(
                title="Dime el titulo.",
                description="Ejemplo: **Buenos dias a todos**",
                color=0x012B54
            )
            message = await ctx.send(embed=embed)

            titulo = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await titulo.delete()
            embed = discord.Embed(
                title="Dime la descripcion de tu embed.",
                description="Ejemplo: **Buenos dias a todos**",
                color=0x012B54
            )
            await message.edit(embed=embed)
            descripcion = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await descripcion.delete()

            embed = discord.Embed(
                title="Dime el color en Hexacode.",
                description="Ejemplo: **0x012B54**, importante poner 0x antes del codigo y quitar el #.",
                color=0x012B54
            )
            await message.edit(embed=embed)
            color = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await color.delete()
            await message.delete()

            embed = discord.Embed(
                title = titulo.content,
                description = descripcion.content,
                colour = int(color.content,0)
            )
            mensaje_rol = await canal.send(embed=embed)
            await mensaje_rol.add_reaction(f"{emogi}")
            cursor.execute( f"INSERT INTO roles (idmsg, idrole, emogi) values (%s,%s,%s)", (mensaje_rol.id, role.id, str(emogi)))  #0087FF
            db.commit()


@bot.command()
async def addreact(ctx, message: discord.Message = None, role: discord.Role = None, emogi = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if message == None:
            await ctx.send("Se te olvido especificar el canal")
        elif role == None:
            await ctx.send("Se te olvido especificar el rol despues del canal")
        elif emogi == None:
            await ctx.send("No especificastes el emogi despues del rol")
        else:
            await ctx.message.delete()
            cursor.execute( f"INSERT INTO roles (idmsg, idrole, emogi) values (%s,%s,%s)", (message.id, role.id, str(emogi)))
            await message.add_reaction(f"{emogi}")
            db.commit()


@bot.command()
async def delreact(ctx, message: discord.Message, emogi):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.message.delete()
        cursor.execute(f"DELETE FROM roles where emogi = %s and ")

@bot.event
async def on_raw_reaction_add(payload):
    try:
        guild = bot.get_guild(payload.guild_id)
        if payload.channel_id != 933072562857062400:
            if payload.guild_id is None:
                return
            member = guild.get_member(payload.user_id)
            message_id = str(payload.message_id)
            cursor.execute(f'SELECT idrole from roles where idmsg = %s and emogi = %s', (message_id, str(payload.emoji)))
            role = cursor.fetchone()
            role = int(role[0])
            role = discord.utils.get(guild.roles, id=role)
            await member.add_roles(role, reason=f"se añadio rol de {role.name}")
        
        else:
            member = guild.get_member(payload.user_id)
            channel = guild.get_channel(ID_MULTICLAN) 
            await channel.send(f"{member.display_name} se ha apuntado a las {datetime.now()} --> {payload.emoji}")
    except Exception as e: 
        raise e


@bot.event
async def on_raw_reaction_remove(payload):
    try:
        guild = bot.get_guild(payload.guild_id)
        if payload.channel_id != 933072562857062400:
            if payload.guild_id is None:
                return
            print(payload.emoji)
            member = guild.get_member(payload.user_id)
            message_id = str(payload.message_id)
            cursor.execute(f'SELECT idrole from roles where idmsg = %s and emogi = %s', (message_id, str(payload.emoji)))
            role = cursor.fetchone()
            role = int(role[0])
            role = discord.utils.get(guild.roles, id=role)
            await member.remove_roles(role, reason=f"se quito rol de {role.name}")
            
        else:
            member = guild.get_member(payload.user_id)
            channel = guild.get_channel(1129875148594499675)
            await channel.send(f"{member.display_name} se ha desapuntado a las {datetime.now()} --> {payload.emoji}")
    except Exception as e: 
        raise e
    
@bot.command()
async def help(ctx):
    await ctx.message.delete()
    try:
        cursor.execute(f"SELECT server_prefix FROM prefix WHERE server_id = %s",(ctx.guild.id, ))
        prefix = cursor.fetchone()
        embed = discord.Embed(title = "Menu de ayuda", description = f"El prefix del servidor es: **{prefix[0]}**")
        await ctx.send(embed=embed)
    except:
        embed = discord.Embed(title = "Menu de ayuda", description = f"El prefix del servidor es: **{DEFAULT_PREFIX}**")
        await ctx.send(embed=embed)

class Select2(discord.ui.Select):
    def __init__(self, ctx):
        option = []
        for category in ctx.guild.categories:
            option.append(discord.SelectOption(label=f"{category.name}", value=category.id))
        discord.SelectOption(label=f"Sin categoria", value=0)
        super().__init__(custom_id="Elije tu categoria", placeholder="Elije la categoria de tus tickets...", min_values=1, max_values=1, options=option)

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, id=int(self.values[0]))
        try:
            cursor.execute(f"UPDATE ticket_config SET id_category_close = %s WHERE id_panel = %s",(category.id, interaction.message.id))
            db.commit()
        except Exception as e:
            raise e
        await interaction.response.send_message("La categoria de cierre a sido registrada con exito", ephemeral=True)
        self.view.stop()

class SelectView2(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Select2(ctx))

class Select(discord.ui.Select):
    def __init__(self, ctx):
        option = []
        for category in ctx.guild.categories:
            option.append(discord.SelectOption(label=f"{category.name}", value=category.id))
        discord.SelectOption(label=f"Sin categoria", value=0)
        super().__init__(custom_id="Elije tu categoria", placeholder="Elije la categoria de tus tickets...", min_values=1, max_values=1, options=option)

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, id=int(self.values[0]))
        try:
            cursor.execute(f"INSERT INTO ticket_config (id_server, id_panel, id_category_open, id_category_close) VALUES (%s, %s, %s, %s)", (interaction.guild.id, interaction.message.id, category.id, 0))
            db.commit()
        except Exception as e:
            raise e
        await interaction.response.send_message("La categoria de apertura a sido registrada con exito", ephemeral=True)
        self.view.stop()

class SelectView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Select(ctx))

@bot.command()
async def panel(ctx, canal: discord.TextChannel = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if canal == None:
            await ctx.send("Se te olvido especificar el canal donde ira el panel de tickets")
        else:

            await ctx.message.delete()

            embed = discord.Embed(
                title="Dime el titulo del panel.",
                description="Ejemplo: **Sistema de tickets**",
                color=0x012B54
            )
            message = await ctx.send(embed=embed)
            
            titulo = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await titulo.delete()
            embed = discord.Embed(
                title="Dime la descripcion de tu embed.",
                description="Ejemplo: **Para abrir un ticket pulse en X**.",
                color=0x012B54
            )
            await message.edit(embed=embed)
            descripcion = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await descripcion.delete()

            embed = discord.Embed(
                title="Dime el color en Hexacode.",
                description="Ejemplo: **0x012B54**, importante poner **0x antes** del codigo y **quitar** el **#**. pagina para verlos: https://htmlcolorcodes.com/es/ ",
                color=0x012B54
            )
            await message.edit(embed=embed)
            color = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            await color.delete()
            await message.delete()
            embed = discord.Embed(
                title = "Selecciona una categoria",
                description = "Selecciona la categoria en la cual se crearan los tickets (si tiene más de 25 categorias puede haber errores, se modificara en proximas updates)",
                color = int(color.content,0)
            )
            view = SelectView(ctx)
            message = await ctx.send(embed = embed, view = view)
            await view.wait()
            
            embed = discord.Embed(
                title = "Selecciona una categoria",
                description = "Selecciona la categoria en la cual se enviaran los tickets cerrados (si tiene más de 25 categorias puede haber errores, se modificara en proximas updates)",
                color = int(color.content,0)
            )
            view = SelectView2(ctx)
            await message.edit(embed = embed, view = view)
            await view.wait()

            embed = discord.Embed(
                title = titulo.content,
                description = descripcion.content,
                color = int(color.content, 0)
            )
            view = button()
            mensaje = await canal.send(embed = embed, view = view)

            cursor.execute(f"UPDATE ticket_config SET id_panel = %s WHERE id_panel = %s", (mensaje.id, message.id))
            db.commit()

@bot.command()
async def addmention (ctx, role:discord.Role = None, mensaje: discord.Message = None):
    rol = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( rol not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.message.delete()
        if role != None:
            if mensaje != None:
                cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id,"mention",role.id))
                ids = cursor.fetchall()
                if ids == []:
                    cursor.execute("INSERT INTO ticket_config_2 (id_panel, type, id) VALUES (%s, %s, %s)",(mensaje.id, "mention", role.id))
                    db.commit()
                    await ctx.send(f"Rol {role.name} añadido con exito")
                else:
                    await ctx.send("Ya habias añadido es rol a las menciones de este panel", delete_after = 4)
            else:
                await ctx.send("Te falta adjuntar el link del panel")
        else:
                await ctx.send("Te falta mencionar el rol que quieres añadir")

@bot.command()
async def addpermision (ctx, role:discord.Role = None, mensaje: discord.Message = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    await ctx.message.delete()
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if role != None:
            if mensaje != None:
                cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id, "permision",role.id))
                ids = cursor.fetchall()
                if ids == []:
                    cursor.execute("INSERT INTO ticket_config_2 (id_panel, type, id) VALUES (%s, %s, %s)",(mensaje.id, "permision", role.id))
                    db.commit()
                    await ctx.send(f"Rol {role.name} añadido con exito")
                else:
                    await ctx.send("Ya habias añadido es rol a los permisos de este panel", delete_after = 4)
            else:
                await ctx.send("Te falta adjuntar el link del panel")
        else:
                await ctx.send("Te falta mencionar el rol que quieres añadir")


@bot.command()
async def delmention (ctx, role:discord.Role = None, mensaje: discord.Message = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    await ctx.message.delete()
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if role != None:
            if mensaje != None:
                cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id,"mention",role.id))
                ids = cursor.fetchall()
                if ids != []:
                    cursor.execute(f"DELETE FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id, "mention",role.id))
                    db.commit()
                    await ctx.send(f"Rol {role.name} eliminado con exito")
                else:
                    await ctx.send("Ese rol no se mencionaba en este panel", delete_after = 4)
            else:
                await ctx.send("Te falta adjuntar el link del panel")
        else:
                await ctx.send("Te falta mencionar el rol que quieres añadir")

@bot.command()
async def delpermision (ctx, role:discord.Role = None, mensaje: discord.Message = None):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    await ctx.message.delete()
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        if role != None:
            if mensaje != None:
                cursor.execute(f"SELECT id FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id, "permision",role.id))
                ids = cursor.fetchall()
                if ids != []:
                    cursor.execute(f"DELETE FROM ticket_config_2 WHERE id_panel = %s and type = %s and id = %s",(mensaje.id, "permision",role.id))
                    db.commit()
                    await ctx.send(f"Rol {role.name} eliminado con exito")
                else:
                    await ctx.send("Ese rol no tiene permisos en este panel", delete_after = 4)
            else:
                await ctx.send("Te falta adjuntar el link del panel")
        else:
                await ctx.send("Te falta mencionar el rol que quieres añadir")


@bot.command()
async def adduser(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.channel.set_permissions(member, read_messages=True,send_messages=True, read_message_history=True, attach_files=True, add_reactions=True)
        await ctx.send(f"{member.display_name} añadido con exito", delete_after = 4)

@bot.command()
async def deluser(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.channel.set_permissions(member, read_messages=False,send_messages=False, read_message_history=False, attach_files=False, add_reactions=False)
        await ctx.send(f"{member.display_name} eliminado con exito", delete_after = 4)

@bot.command()
async def addrole(ctx, role: discord.Role):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.channel.set_permissions(role, read_messages=True,send_messages=True, read_message_history=True, attach_files=True, add_reactions=True)
        await ctx.send(f"{role.name} añadido con exito", delete_after = 4)

@bot.command()
async def delrole(ctx, role: discord.Role):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.channel.set_permissions(role, read_messages=False,send_messages=False, read_message_history=False, attach_files=False, add_reactions=False)
        await ctx.send(f"{role.name} eliminado con exito", delete_after = 4)



@bot.command()
async def capcha(ctx, role: discord.Role):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.message.delete()
        cursor.execute("SELECT id_server FROM capcha")
        lista = cursor.fetchall()
        if ctx.guild.id in lista:
            await ctx.send("")


@bot.command()
@has_permissions(kick_members=True)
async def kick(ctx, member : discord.User):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.send("Porfavor, especifique la razon de la expulsion", delete_after = 10)
        razon = await bot.wait_for('message', check=lambda message: message.author == ctx.author)

        try:
            await ctx.guild.kick(member, reason=razon.content)
            await ctx.send(f"El usuario {member.name} a sido expulsado")
        except Exception as e:
            raise e

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Lo siento {}, no tienes permisos para hacer eso!".format(ctx.message.author.display_name)
        await bot.send_message(ctx.message.channel, text)

@bot.command()
@has_permissions(ban_members=True)
async def ban(ctx, member : discord.User):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.send("Porfavor, especifique la razon del ban", delete_after = 10)
        razon = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout = 30)
        await ctx.send("¿quiere borrar los mensajes? especifique la cantidad de dias, MAX = 7", delete_after = 10)
        dias = await bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout = 30)

        if int(dias.content) > 7:
            await ctx.send("El maximo de dias a borrar es 7, se borraran los ultimos 7 dias de mensajes", delete_after = 10)
            dias = 7
        else:
            dias = int(dias.content)

        try:
            await ctx.guild.ban(member, reason=razon.content, delete_message_days=int(dias))
            await ctx.send(f"El usuario {member.name} a sido baneado")
        except Exception as e:
            raise e

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Lo siento {}, no tienes permisos para hacer eso!".format(ctx.message.author.display_name)
        await bot.send_message(ctx.message.channel, text)

@bot.command()
@has_permissions(ban_members=True)
async def unban(ctx, member : discord.User):
    role = discord.utils.get(ctx.guild.roles, id=ID_PLMM)
    if ( role not in ctx.author.roles):
        await ctx.send("No eres PLMM")
    else:
        await ctx.send("Porfavor, especifique la razon del unban", delete_after = 10)
        razon = await bot.wait_for('message', check=lambda message: message.author == ctx.author)

        try:
            await ctx.guild.unban(member, reason=razon.content)
            await ctx.send(f"El usuario {member.name} a sido desbaneado")
        except Exception as e:
            raise e

@ban.error
async def unban_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Lo siento {}, no tienes permisos para hacer eso!".format(ctx.message.author.display_name)
        await bot.send_message(ctx.message.channel, text)
        
        
        
        
        
async def send_message_at_9():
    await bot.wait_until_ready()
    channel = bot.get_channel(ID_CANAL_MIEMBROS)  
    while not bot.is_closed():
        now = datetime.now()
        print(now.hour)
        print(now.minute)
        if now.hour == 10 and now.minute == 30:
            await channel.send("""¡Buenos días! Es hora de comenzar el día.""")
            # Añadir una pausa para evitar múltiples envíos si el bucle se ejecuta varias veces cerca de la misma hora
            await asyncio.sleep(60)  
        else:
            # Espera 1 segundo antes de verificar nuevamente la hora
            await asyncio.sleep(60)
            
           
# Directorio deseado desde donde ejecutar el archivo .bat
directorio_trabajo = "D:/A3Master/MODSINSTALL/"

# Diccionario para almacenar los PIDs de los procesos
server_processes = {
    "base": None,
    "entrenamientos": None
}

#@bot.command()
#async def server(ctx, server):
#    if discord.utils.get(ctx.guild.roles, id=ID_MIEMBRO) in ctx.author.roles:
#        if server in server_processes:
#            pid = server_processes[server]
#            if pid is not None and proceso_activo(pid):
#                await ctx.send(f"El proceso del servidor '{server}' ya está activo con PID {pid}.")
#            else:
#                await ejecutar_bat(ctx, server)
#        else:
#            await ctx.send("No se reconoció el servidor, recuerda usar: 'base' o 'entrenamientos' como nombre del servidor")
#    else:
#        await ctx.send("No eres miembro de la CAP")

#async def ejecutar_bat(ctx, server):
#    try:
#        # Cambiar el directorio de trabajo
#        os.chdir(directorio_trabajo)
#        
#        # Verificar si ya hay un proceso activo con el nombre y puerto específico
#        pid = buscar_proceso_por_nombre_y_puerto(server)
#        
#        if pid:
#            await ctx.send(f"El servidor '{server}' ya está activo con PID {pid}.")
#        else:
#            # Iniciar el proceso y obtener el PID inicial
#            proceso = subprocess.Popen([f"{server}.bat"], shell=True)
#            await ctx.send(f"Iniciando servidor {server}..., el inicio puede tardar entre 20 y 60 segundos, en caso de que no se complete notifique a un PLMM conectado, prefireblemente a Tigre")
#            
#            # Esperar un tiempo suficiente para que el proceso se inicie completamente
#            await asyncio.sleep(20)  # Ajusta el tiempo según sea necesario
#            
#            # Obtener el PID del proceso que iniciamos
#            pid = buscar_proceso_por_nombre_y_puerto(server)
#            if pid:
#                server_processes[server] = pid
#                await ctx.send(f"Servidor {server} iniciado, Espera de 30 a 60 segundos mientras carga la mision.")
#            else:
#                await ctx.send(f"No se pudo obtener el PID del servidor '{server}' después de iniciarlo.")
#    except Exception as e:
#        await ctx.send(f"Error al ejecutar el archivo .bat: {e}")

#def buscar_proceso_por_nombre_y_puerto(nombre_servidor):
#    try:
#        # Obtener todos los procesos
#        procesos = psutil.process_iter(['pid', 'cmdline'])
#
#        # Iterar a través de los procesos y buscar el puerto específico en el cmdline
#        for proceso in procesos:
#            try:
#                cmdline = " ".join(proceso.cmdline())  # Convertir cmdline a una cadena de texto
#                if f"-port={get_puerto(nombre_servidor)}" in cmdline:
#                    return proceso.pid
#            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#                pass
#        
#        return None
#    except Exception as e:
#        print(f"Error al buscar proceso por nombre y puerto: {e}")
#        return None

#def get_puerto(nombre_servidor):
#    if nombre_servidor == "base":
#        return 2302
#    elif nombre_servidor == "entrenamientos":
#        return 2502
#    else:
#        return None

#def proceso_activo(pid):
#    try:
#        # Obtener el proceso por PID y comprobar si está activo
#        proc = psutil.Process(pid)
#        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
#    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#        return False


bot.run(TOKEN)
