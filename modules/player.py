import sys
from asyncio import sleep
from datetime import datetime, timedelta
from json import loads
from os import execl
from re import findall, split
from traceback import format_exc

from bs4 import BeautifulSoup
from discord import Embed, FFmpegPCMAudio
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from discord_components import Button, ButtonStyle
from pytz import timezone
from requests import get
from websockets import connect

from bot import DB, SET

VOICE = int(DB.server.channels.find_one({"Название": "🦄вечеринка голосовой"})["_id"])


class Player(Cog):
    def __init__(self, bot):
        self.BOT = bot
        self.player.start()
        self.online.start()

    def cog_unload(self):
        self.player.cancel()
        self.online.cancel()

    async def messages(self, name, value):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                try:
                    await self.BOT.get_user(uid).send(embed=Embed(
                        title="Сообщение!", color=0x008000).add_field(name=name, value=value))
                except Exception:
                    pass
        except Exception:
            print(format_exc())

    async def alerts(self, name, value):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                try:
                    await self.BOT.get_user(uid).send(embed=Embed(
                        title="Уведомление!", color=0xFFA500).add_field(name=name, value=value))
                except Exception:
                    pass
        except Exception:
            print(format_exc())

    async def errors(self, name, value, reset=0):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                try:
                    await self.BOT.get_user(uid).send(embed=Embed(
                        title="Ошибка!", color=0xFF0000).add_field(name=name, value=value))
                except Exception:
                    pass
            if reset == 1:
                execl(sys.executable, "python", "bot.py", *sys.argv[1:])
        except Exception:
            print(format_exc())

    async def subscribe(self, interaction):
        try:
            user, status = DB.server.users.find_one({"_id": interaction.user.id})["Уведомления"], None
            if user == "Да":
                status = "Подписан"
            else:
                status = "Не подписан"
            e = Embed(title="Настройки:", color=0x00FFFF,
                      description="Подписатся на уведомления о прямых эфирах?")
            e.add_field(name="Текущий статус:", value=f"{status}")
            e.set_thumbnail(url="https://discord.com/assets/a6d05968d7706183143518d96c9f066e.svg")
            e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            await interaction.send(embed=e, components=[[Button(emoji="🔔", id="notifyon"),
                                                         Button(emoji="🔕", id="notifyoff")]])
        except Exception:
            await self.errors("Подписка:", format_exc())

    @loop()
    async def player(self):
        try:
            while True:
                try:
                    for x in self.BOT.voice_clients:
                        await x.disconnect()
                except Exception:
                    pass
                try:
                    vc = await self.BOT.get_channel(VOICE).connect()
                    vc.play(FFmpegPCMAudio("https://everhoof.ru/320"))
                except Exception:
                    pass
                icon, artist, title, = "//everhoof.ru/favicon.png", "Everhoof Radio", "Everhoof Radio"
                duration, delta = 0, 0
                try:
                    content = await connect("wss://everhoof.ru:443/ws")
                    track = loads(await content.recv())
                    icon, artist, title, duration = track["art"], track["artist"], track["title"], track["duration"]
                    if len(icon) == 0:
                        icon = "//everhoof.ru/favicon.png"
                    if len(artist) == 0:
                        try:
                            artist = split(" - ", track["Имя"])[0]
                        except Exception:
                            pass
                        if len(artist) == 0:
                            artist = "Everhoof Radio"
                    if len(title) == 0:
                        try:
                            title = split(" - ", track["Имя"])[1]
                        except Exception:
                            pass
                        if len(title) == 0:
                            title = "Everhoof Radio"
                    if len(str(duration)) == 0:
                        duration = 60
                    try:
                        btime = "".join(findall(r"\d{2}:\d{2}:\d{2}", track["ends_at"])[0])
                        ctime = datetime.now(timezone('Europe/Moscow')).strftime("%H:%M:%S")
                        time_1 = datetime.strptime(f'{btime}', "%H:%M:%S")
                        time_2 = datetime.strptime(f'{ctime}', "%H:%M:%S")
                        h, m, s = str(time_1 - time_2).strip().split(":")
                        delta = int(h) * 3600 + int(m) * 60 + int(s) + 1
                    except Exception:
                        delta = 60
                    if duration == 0:
                        if track["starts_at"] == track["ends_at"]:
                            try:
                                content = loads(get("https://everhoof.ru/api/calendar/nogard").text)[0]
                                starts_at = int("".join(findall(r"\d+", content["starts_at"])[:6]))
                                ends_at = int("".join(findall(r"\d+", content["ends_at"])[:6]))
                                dtime = int(datetime.now(timezone('Europe/Moscow')).strftime("%Y%m%d%H%M%S"))
                                if starts_at <= dtime <= ends_at:
                                    artist, title, delta = "В эфире", content["summary"], 60
                            except Exception:
                                delta = 60
                        else:
                            delta = 60
                except Exception:
                    pass
                d = str(timedelta(seconds=duration))[2:]
                channel = DB.server.channels.find_one({"Название": "🦄вечеринка"})
                try:
                    post = await self.BOT.get_channel(int(channel["_id"])).fetch_message(int(channel["Плеер"]))
                    await post.delete()
                except Exception:
                    pass
                e = Embed(title="Сейчас играет:", color=0x00FFFF)
                e.set_thumbnail(url=f"https:{icon}")
                e.add_field(name=title, inline=False,
                            value=f"Исполнитель: {artist}\nДлительность: {d}\nСсылка: https://everhoof.ru")
                e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
                try:
                    mes = await self.BOT.get_channel(int(channel["_id"])).send(embed=e, components=[
                        [Button(label="История", style=ButtonStyle.green),
                         Button(emoji="⚙", style=ButtonStyle.blue, id="settings")]])
                    DB.server.channels.update_one({"Название": "🦄вечеринка"}, {"$set": {"Плеер": mes.id}})
                except Exception:
                    pass
                await sleep(int(delta))
        except Exception:
            await self.errors("Плеер:", format_exc())

    @loop(minutes=1)
    async def online(self):
        try:
            content = await connect("wss://everhoof.ru:443/ws")
            track = loads(await content.recv())
            if track["duration"] == 0:
                if track["starts_at"] == track["ends_at"]:
                    content = loads(get("https://everhoof.ru/api/calendar/nogard").text)[0]
                    starts_at = int("".join(findall(r"\d+", content["starts_at"])[:6]))
                    ends_at = int("".join(findall(r"\d+", content["ends_at"])[:6]))
                    if starts_at <= int(datetime.now(timezone('Europe/Moscow')).strftime("%Y%m%d%H%M%S")) <= ends_at:
                        if int(DB.server.settings.find_one({"_id": "Настройки"})["Триггер"]) < starts_at:
                            members = ""
                            for user in [user["_id"] for user in DB.server.users.find({"Уведомления": "Да"})]:
                                members += f"<@{user}>, "
                            await self.BOT.get_channel(
                                int(DB.server.channels.find_one({"Название": "🦄вечеринка"})["_id"])).send(
                                f"{members}\nСейчас в прямом эфире \"{content['summary']}\"!")
                            DB.server.settings.update_one({"_id": "Настройки"}, {"$set": {"Триггер": ends_at}})
        except Exception:
            await self.errors("Онлайн:", format_exc())

    @Cog.listener()
    async def on_button_click(self, interaction):
        try:
            if interaction.component.label == "История":
                e = Embed(title="История:", color=interaction.user.color)
                try:
                    soup = BeautifulSoup(get("https://everhoof.ru/").text, "html.parser")("li", "history-modal__item")
                    for s in soup:
                        track = str(s.get_text(strip=True))
                        a = track.split(". ")
                        b = a[1].split(" - ")
                        e.add_field(name=f"{a[0]}. {b[1]}", value=f"Исполнитель: {b[0]}", inline=False)
                except Exception:
                    e.add_field(name="Ошибка!", value="Не удалось получить список, попробуйте позже...", inline=False)
                e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
                await interaction.send(embed=e)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if interaction.component.id == "settings":
                await self.subscribe(interaction)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.id}:", format_exc())
        try:
            if interaction.component.id == "notifyon":
                DB.server.users.update_one({"_id": interaction.user.id}, {"$set": {"Уведомления": "Да"}})
                await self.subscribe(interaction)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.id}:", format_exc())
        try:
            if interaction.component.id == "notifyoff":
                DB.server.users.update_one({"_id": interaction.user.id}, {"$set": {"Уведомления": "Нет"}})
                await self.subscribe(interaction)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.id}:", format_exc())


def setup(bot):
    bot.add_cog(Player(bot))
