import sys
from asyncio import sleep
from json import loads
from os import execl
from random import choice, randint
from re import findall
from traceback import format_exc

from discord import Embed
from discord.ext.commands import command, has_permissions, Cog
from discord.ext.tasks import loop
from requests import get

from bot import DB, SET

ARTS = DB.server.channels.find_one({"Название": "🦄арты"})["_id"]
DARTS = DB.server.channels.find_one({"Название": "🦄тёмные_арты"})["_id"]


class Arts(Cog):
    def __init__(self, bot):
        self.BOT = bot
        self.checkarts.start()
        self.sendarts.start()
        self.darkarts.start()

    def cog_unload(self):
        self.checkarts.cancel()
        self.sendarts.cancel()
        self.darkarts.cancel()

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

    @loop(count=1)
    async def checkarts(self):
        try:
            headers = ({"apikey": "fbd30ba0-56be-11ec-9fc5-07d4cf167e6b"},
                       {"apikey": "739ddd40-56c4-11ec-83af-4306261ca458"},
                       {"apikey": "1eaa41e0-6e48-11ec-befe-ad3a1f46b0f6"})
            params = (("url", "https://4pda.to/forum/index.php?showtopic=403239&view=getnewpost"), ("render", "true"),
                      ("location", "eu"), ("device_type", "mobile"))
            rget = get("https://app.zenscrape.com/api/v1/get", headers=choice(headers), params=params).content
            url = "//4pda.to/forum/dl/post/"
            counts = len(findall(rf"{url}(\d*)/(?:[_\-]*\w+[_\-]+){{2,}}\w+[(\d+)%]*\.(?:jpg|png|gif|jpeg)",
                                 f"{rget}"))
            if counts != 0:
                news = int(findall(rf"{url}(\d*)/(?:[_\-]*\w+[_\-]+){{2,}}\w+[(\d+)%]*\.(?:jpg|png|gif|jpeg)",
                                   f"{rget}")[-1][:-3])
                posts1 = findall(
                    rf"{url}((?:{news - 1}\d{{3}})/(?:[_\-]*\w+[_\-]+){{2,}}\w+[(\d+)%]*\.(?:jpg|png|gif|jpeg))",
                    f"{rget}")
                posts2 = findall(
                    rf"{url}((?:{news}\d{{3}})/(?:[_\-]*\w+[_\-]+){{2,}}\w+[(\d+)%]*\.(?:jpg|png|gif|jpeg))",
                    f"{rget}")
                arts = DB.server.warts.find_one({"_id": "Арты"})
                if int(news) > int(arts["ID"]):
                    DB.server.warts.update_one({"_id": "Арты"}, {"$set": {"ID": news}})
                    DB.server.warts.update_one({"_id": "Арты"},
                                               {"$push": {"Арты": {"$each": posts1 + posts2, "$position": 0}}})
                    await self.messages("Проверка артов:", f"{len(posts1) + len(posts2)} артов загружены в БД!\n"
                                                           f"На данный момент в базе данных {len(arts['Арты'])} артов!")
        except Exception:
            await self.errors("Загрузка артов:", format_exc())

    @loop()
    async def sendarts(self):
        try:
            while True:
                arts = DB.server.warts.find_one({"_id": "Арты"})
                await self.BOT.get_channel(int(ARTS)).send(f"https://4pda.to/forum/dl/post/{arts['Арты'][0]}")
                DB.server.warts.update_one({"_id": "Арты"}, {"$pop": {"Арты": -1}})
                await sleep(int(arts["Таймер"]) * 60)
        except Exception:
            await self.errors("Отправка артов:", format_exc())

    @loop()
    async def darkarts(self):
        try:
            while True:
                dark = DB.server.warts.find_one({"_id": "Темные Арты"})
                for tag in dark["Теги"]:
                    try:
                        request = loads(get(f"https://derpibooru.org/api/v1/json/search/images?page=1&per_page=50&"
                                            f"filter_id=2&q={tag}").text)["images"]
                        await self.BOT.get_channel(int(DARTS)).send(f"{request[randint(1, 50)]['view_url']}")
                    except Exception:
                        pass
                await sleep(int(dark["Таймер"]) * 60)
        except Exception:
            await self.errors("Отправка темных артов:", format_exc())

    @command(description="8", name="arts", help="Настройки модуля Arts",
             brief="Ничего / `Параметр` / `Время в минутах`", usage="!arts dark 60")
    @has_permissions(administrator=True)
    async def arts(self, ctx, trigger: str = None, timetag: str = None):
        try:
            if ctx.channel.id == int(ARTS) or ctx.channel.id == int(DARTS):
                await ctx.message.delete(delay=1)
                arts, dark = DB.server.warts.find_one({"_id": "Арты"}), DB.server.warts.find_one({"_id": "Темные Арты"})
                e = None
                if trigger is None and timetag is None:
                    e = Embed(title="Настройки модуля \"Arts\":", color=ctx.author.color)
                    e.add_field(name="Команды канала \"Арты\":", inline=False,
                                value="Изменить частоту публикации: **!arts `время в минутах`**")
                    e.add_field(name="Команды канала \"Темные Арты\":", inline=False,
                                value="Изменить частоту публикации: **!arts dark `время в минутах`**\n"
                                      "Добавить тег для поиска: **!arts +tag `название тега`**\n"
                                      "Удалить тег из поиска: **!arts -tag `название тега`**")
                    e.add_field(name="Настройки канала \"Арты\":", inline=False,
                                value=f"Артов в базе данных: {len(arts['Арты'])}\n"
                                      f"Частота публикации артов: {arts['Таймер']} минут")
                    e.add_field(name="Настройки канала \"Темные Арты\":", inline=False,
                                value=f"Теги для поиска: {', '.join(dark['Теги'])}\n"
                                      f"Частота публикации артов: {dark['Таймер']} минут")
                if trigger is not None:
                    if trigger == "+tag":
                        if timetag is not None:
                            e = Embed(title="Добавление тега:", color=ctx.author.color)
                            check = loads(get(f"https://derpibooru.org/api/v1/json/search/images?per_page=50&"
                                              f"filter_id=2&q={timetag.lower()}").text)["images"]
                            if len(check) == 50:
                                if timetag.lower() not in dark["Теги"]:
                                    DB.server.warts.update_one({"_id": "Темные Арты"},
                                                               {"$push": {"Теги": timetag.lower()}})
                                    e.add_field(name="Успешно:", inline=False, value=f"{timetag.lower()}")
                                else:
                                    e.add_field(name="Ошибка:", inline=False,
                                                value=f"Тег **{timetag.lower()}** уже есть в списке!")
                            else:
                                e.add_field(name="Ошибка:", inline=False,
                                            value=f"По тегу **{timetag.lower()}** слишком мало результатов!")
                    elif trigger == "-tag":
                        if timetag is not None:
                            e, tags = Embed(title="Удаление тега:", color=ctx.author.color), dark["Теги"]
                            try:
                                tags.remove(str(timetag.lower()))
                                e.add_field(name="Успешно:", inline=False, value=f"{timetag.lower()}")
                            except Exception:
                                e.add_field(name="Ошибка:", inline=False,
                                            value=f"Тег **{timetag.lower()}** не найден в списке добавленных!")
                            DB.server.warts.update_one({"_id": "Темные Арты"}, {"$set": {"Теги": tags}})
                    elif trigger == "dark":
                        if timetag is not None:
                            if len(findall(r"\d+", timetag)) != 0:
                                time = int("".join(findall(r"\d+", timetag)))
                                DB.server.warts.update_one({"_id": "Темные Арты"}, {"$set": {"Таймер": time}})
                                e = Embed(title="Изменение времени:", color=ctx.author.color,
                                          description=f"Частота публикации в канале \"Темные Арты\" "
                                                      f"изменена на **{time}** минут!")
                    else:
                        if len(findall(r"\d+", trigger)) != 0:
                            time = int("".join(findall(r"\d+", trigger)))
                            DB.server.warts.update_one({"_id": "Арты"}, {"$set": {"Таймер": time}})
                            e = Embed(title="Изменение времени:", color=ctx.author.color,
                                      description=f"Частота публикации в канале \"Арты\" изменена на **{time}** минут!")
                e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
                await ctx.send(embed=e, delete_after=60)
                await self.alerts(ctx.author, f"Использовал команду: {ctx.command.name} {trigger} {timetag}\n"
                                              f"Канал: {ctx.message.channel}")
        except Exception:
            await self.errors(f"Команда {ctx.command.name}:", format_exc())


def setup(bot):
    bot.add_cog(Arts(bot))
