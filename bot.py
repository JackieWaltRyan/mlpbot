import sys
from asyncio import sleep
from datetime import datetime
from os import execl, listdir
from random import choice
from threading import Timer
from traceback import format_exc

from discord import Embed, Intents, ActivityType, Activity, Member, utils
from discord.ext.commands import Bot, when_mentioned_or, has_permissions
from discord_components import DiscordComponents
from fuzzywuzzy.fuzz import token_sort_ratio
from pymongo import MongoClient
from pytz import timezone

BOT = Bot(command_prefix=when_mentioned_or("!"), help_command=None, intents=Intents.all())

DB = MongoClient("")

SET, SPAM, BLOCK = DB.server.settings.find_one({"_id": "Настройки"}), {}, []


def autores():
    try:
        Timer(1, autores).start()
        atime = int(datetime.now(timezone('Europe/Moscow')).strftime("%H%M%S"))
        print(atime)
        if atime == 80000 or atime == 200000:
            execl(sys.executable, "python", "bot.py", *sys.argv[1:])
    except Exception:
        print(format_exc())


async def messages(name, value):
    try:
        for uid in [x for x in SET["Уведомления"].values()]:
            try:
                await BOT.get_user(uid).send(embed=Embed(
                    title="Сообщение!", color=0x008000).add_field(name=name, value=value))
            except Exception:
                pass
    except Exception:
        print(format_exc())


async def alerts(name, value):
    try:
        for uid in [x for x in SET["Уведомления"].values()]:
            try:
                await BOT.get_user(uid).send(embed=Embed(
                    title="Уведомление!", color=0xFFA500).add_field(name=name, value=value))
            except Exception:
                pass
    except Exception:
        print(format_exc())


async def errors(name, value, reset=0):
    try:
        for uid in [x for x in SET["Уведомления"].values()]:
            try:
                await BOT.get_user(uid).send(embed=Embed(
                    title="Ошибка!", color=0xFF0000).add_field(name=name, value=value))
            except Exception:
                pass
        if reset == 1:
            execl(sys.executable, "python", "bot.py", *sys.argv[1:])
    except Exception:
        print(format_exc())


@BOT.event
async def on_connect():
    try:
        autores()
    except Exception:
        await errors("Таймер:", format_exc())


@BOT.event
async def on_ready():
    try:
        DiscordComponents(BOT)
    except Exception:
        await errors("DiscordComponents:", format_exc())
    try:
        await messages(BOT.user, "Запускается...")
    except Exception:
        await errors("Сообщение запуска:", format_exc())
    try:
        if BOT.user.id == SET["Принцесса Селестия"]["ID"]:
            await BOT.change_presence(activity=Activity(
                type=ActivityType.watching, name="за Эквестрией..."))
        if BOT.user.id == SET["Принцесса Луна"]["ID"]:
            await BOT.change_presence(activity=Activity(
                type=ActivityType.listening, name="тишину ночи..."))
    except Exception:
        await errors("Установка статуса:", format_exc())
    try:
        for member in BOT.get_all_members():
            user = DB.server.users.find_one({"_id": member.id})
            if user is None:
                DB.server.users.insert_one({"_id": int(member.id),
                                            "Имя аккаунта": member.name,
                                            "Статус": "Активный",
                                            "Время последнего сообщения": datetime.now(),
                                            "Уведомления": "Нет",
                                            "Радуга": "Нет",
                                            "Страница": "p0",
                                            "Концовки": [],
                                            "Сыграно игр в Крестики-нолики": 0,
                                            "Побед в Крестики-нолики": 0,
                                            "Поражений в Крестики-нолики": 0,
                                            "Процент побед в Крестики-нолики": 0,
                                            "Сыграно игр в Тетрис": 0,
                                            "Лучший счет в Тетрис": 0})
            else:
                if member.bot:
                    DB.server.users.update_one({"_id": member.id}, {"$set": {"Бот": "Да"}})
                delta = datetime.now() - user["Время последнего сообщения"]
                if delta.days >= 7:
                    DB.server.users.update_one({"_id": member.id}, {"$set": {"Статус": "Неактивный"}})
                    try:
                        await member.add_roles(utils.get(member.guild.roles, id=int(
                            DB.server.roles.find_one({"Название": "🦄 Неактивные"})["_id"])))
                    except Exception:
                        pass
    except Exception:
        await errors("Обновление пользователей:", format_exc())
    try:
        for channel in BOT.get_all_channels():
            ch = DB.server.channels.find_one({"_id": channel.id})
            if ch is None:
                DB.server.channels.insert_one({"_id": int(channel.id), "Название": channel.name})
            else:
                DB.server.channels.update_one({"_id": channel.id}, {"$set": {"Название": channel.name}})
    except Exception:
        await errors("Обновление каналов:", format_exc())
    try:
        for guild in BOT.guilds:
            for role in guild.roles:
                r = DB.server.roles.find_one({"_id": role.id})
                if r is None:
                    DB.server.roles.insert_one({"_id": int(role.id), "Название": role.name})
                else:
                    DB.server.roles.update_one({"_id": role.id}, {"$set": {"Название": role.name}})
    except Exception:
        await errors("Обновление ролей:", format_exc())
    try:
        ok, error, cogs, modules = [], [], SET["Отключенные модули"], ""
        for filename in listdir("./modules"):
            if filename.endswith(".py"):
                cog = filename[:-3]
                if cog not in cogs:
                    try:
                        BOT.load_extension(f"modules.{cog.lower()}")
                        ok.append(cog.title())
                    except Exception:
                        error.append(cog.title())
        ok.sort()
        error.sort()
        cogs.sort()
        if len(ok) != 0:
            modules += "**Успешно:**\n" + "\n".join(x for x in ok)
        if len(error) != 0:
            modules += "\n\n**Неудачно:**\n" + "\n".join(x for x in error)
        if len(cogs) != 0:
            modules += "\n\n**Отключено:**\n" + "\n".join(x.title() for x in cogs)
        await messages("Загрузка модулей:", modules)
    except Exception:
        await errors("Загрузка модулей:", format_exc())
    try:
        if BOT.user.id == SET["Принцесса Селестия"]["ID"]:
            await messages(BOT.user, "Снова \"Смотрит за Эквестрией...\"")
        if BOT.user.id == SET["Принцесса Луна"]["ID"]:
            await messages(BOT.user, "Снова \"Слушает тишину ночи...\"")
    except Exception:
        await errors("Сообщение готовности:", format_exc())


@BOT.event
async def on_message(message):
    try:
        await BOT.process_commands(message)
    except Exception:
        await errors("process_commands:", format_exc())
    try:
        if message.author.id in BLOCK:
            try:
                await message.delete()
            except Exception:
                pass
        else:
            if message.author.id not in [SET["Принцесса Селестия"]["ID"], SET["Принцесса Луна"]["ID"]]:
                if SPAM.get(message.author.id) is None:
                    SPAM.update({message.author.id: [message.content]})
                else:
                    SPAM[message.author.id].insert(0, message.content)
                if len(SPAM[message.author.id]) >= 3:
                    if token_sort_ratio(SPAM[message.author.id][0], SPAM[message.author.id][1]) >= 90:
                        if token_sort_ratio(SPAM[message.author.id][1], SPAM[message.author.id][2]) >= 90:
                            try:
                                await message.delete()
                            except Exception:
                                pass
                            await message.author.send(embed=Embed(title="Уведомление!", color=0xFFA500).add_field(
                                name="Блокировка за спам!", value="Вы были заблокированы на 60 секунд за спам!"))
                            BLOCK.append(message.author.id)
                            SPAM[message.author.id].clear()
                            await alerts(message.author, "Заблокирован за спам!")
                            await sleep(60)
                            BLOCK.remove(message.author.id)
    except Exception:
        await errors("Антиспам:", format_exc())
    try:
        if message.content.startswith("!cogs"):
            if message.author.bot:
                if message.content.endswith("cjlkzrwuqxcnaznzsx"):
                    await message.delete(delay=1)
                    BOT.unload_extension(f"modules.rainbow")
                    BOT.load_extension(f"modules.rainbow")
    except Exception:
        await errors("Перезагрузка модуля \"rainbow\":", format_exc())
    try:
        DB.server.users.update_one({"_id": message.author.id},
                                   {"$set": {"Статус": "Активный", "Время последнего сообщения": message.created_at}})
        try:
            await message.author.remove_roles(utils.get(message.author.guild.roles, id=int(
                DB.server.roles.find_one({"Название": "🦄 Неактивные"})["_id"])))
        except Exception:
            pass
    except Exception:
        await errors("Обновление актива:", format_exc())


@BOT.event
async def on_raw_reaction_add(payload):
    try:
        post = await BOT.get_channel(payload.channel_id).fetch_message(payload.message_id)
        like, dlike = 0, 0
        for reaction in post.reactions:
            if reaction.emoji == "👍":
                like = int(reaction.count)
            if reaction.emoji == "👎":
                dlike = int(reaction.count)
        bots = DB.server.users.count_documents({"Бот": "Да"})
        ratio = int((DB.server.users.count_documents({"Статус": "Активный"}) - bots) / 3)
        if like - dlike >= ratio:
            await post.pin()
        if dlike - like >= ratio:
            await post.delete()
    except Exception:
        await errors(f"Пользовательская модерация:", format_exc())


@BOT.event
async def on_member_join(member):
    try:
        e = Embed(title="В наш клуб присоединилась милая поняшка!", color=0xBA55D3,
                  description=f"Поприветствуем: {member.mention}!")
        e.set_thumbnail(url=member.avatar_url)
        e.set_image(url=choice(DB.server.settings.find_one({"_id": "Настройки"})["Арты приветствия"]))
        e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
        await BOT.get_channel(int(DB.server.channels.find_one({"Название": "🦄болталка"})["_id"])).send(embed=e)
        user = DB.server.users.find_one({"_id": member.id})
        if user is None:
            DB.server.users.insert_one({"_id": int(member.id),
                                        "Имя аккаунта": member.name,
                                        "Статус": "Активный",
                                        "Время последнего сообщения": datetime.now(),
                                        "Уведомления": "Нет",
                                        "Радуга": "Нет",
                                        "Страница": "p0",
                                        "Концовки": [],
                                        "Сыграно игр в Крестики-нолики": 0,
                                        "Побед в Крестики-нолики": 0,
                                        "Поражений в Крестики-нолики": 0,
                                        "Процент побед в Крестики-нолики": 0,
                                        "Сыграно игр в Тетрис": 0,
                                        "Лучший счет в Тетрис": 0})
    except Exception:
        await errors("Новый участник:", format_exc())


# команды пользователей
@BOT.command(description="0", name="help", help="Показать список всех команд бота", brief="Не применимо", usage="!help")
async def helpmenu(ctx):
    try:
        await ctx.message.delete(delay=1)
        e = Embed(title="Список всех команд:", color=ctx.author.color)
        list1 = [[x.description for x in BOT.commands], [x.name for x in BOT.commands],
                 [x.help for x in BOT.commands], [x.brief for x in BOT.commands], [x.usage for x in BOT.commands]]
        list2 = []
        i = 0
        while i < len(list1[0]):
            sor = [list1[0][i], list1[1][i], list1[2][i], list1[3][i], list1[4][i]]
            list2.append(sor)
            i += 1
        list2.sort()
        ii = 0
        while ii < len(list2):
            if ctx.message.author.id in [x for x in SET["Уведомления"].values()]:
                if int(list2[ii][0]) <= 9:
                    e.add_field(name=f"{list2[ii][1]}", inline=False,
                                value=f"Описание: {list2[ii][2]}\nПараметр: {list2[ii][3]}\nПример: {list2[ii][4]}")
            elif ctx.message.author.guild_permissions.administrator:
                if int(list2[ii][0]) <= 8:
                    e.add_field(name=f"{list2[ii][1]}", inline=False,
                                value=f"Описание: {list2[ii][2]}\nПараметр: {list2[ii][3]}\nПример: {list2[ii][4]}")
            elif ctx.message.author.guild_permissions.manage_messages:
                if int(list2[ii][0]) <= 7:
                    e.add_field(name=f"{list2[ii][1]}", inline=False,
                                value=f"Описание: {list2[ii][2]}\nПараметр: {list2[ii][3]}\nПример: {list2[ii][4]}")
            else:
                if int(list2[ii][0]) <= 6:
                    e.add_field(name=f"{list2[ii][1]}", inline=False,
                                value=f"Описание: {list2[ii][2]}\nПараметр: {list2[ii][3]}\nПример: {list2[ii][4]}")
            ii += 1
        e.set_footer(text=f"В качестве префикса можно использовать знак ! или упоминание бота @{BOT.user.name}")
        await ctx.send(embed=e, delete_after=60)
        await alerts(ctx.author, f"Использовал команду: {ctx.command.name}\nКанал: {ctx.message.channel}")
    except Exception:
        await errors(f"Команда {ctx.command.name}:", format_exc())


# команды администраторов
@BOT.command(description="8", name="mods", help="Управление модулями",
             brief="Ничего / `Параметр` / `Название модуля`", usage="!mods on commands")
@has_permissions(administrator=True)
async def mods(ctx, trigger: str = None, name: str = None):
    try:
        await ctx.message.delete(delay=1)
        arts = DB.server.channels.find_one({"Название": "🦄арты"})["_id"]
        darkarts = DB.server.channels.find_one({"Название": "🦄тёмные_арты"})["_id"]
        party = DB.server.channels.find_one({"Название": "🦄вечеринка"})["_id"]
        welcome = DB.server.channels.find_one({"Название": "Добро пожаловать!"})["_id"]
        desc = {"arts": f"Модуль отвечает публикацию новых артов в канале <#{arts}> и <#{darkarts}>.\n\nКоманды в "
                        f"модуле: !arts",
                "commands": "Модуль отвечает за все команды бота кроме административных. Даже если модуль отключен, "
                            "команда \"!help\", команды управления модулями (!mods), и команда перезагрузки бота (!res)"
                            " по прежнему будут работать.",
                "game": "Модуль отвечает за игру \"Похищенная пони\" и все что с ней связанно.",
                "player": f"Модуль отвечает за музыкальный плеер в канале <#{party}> и все что с ним связанно.",
                "posts": f"Модуль отвечает за автоматическое обновление постов в категории <#{welcome}>, обработку их "
                         f"кнопок и выдачу ролей.",
                "rainbow": "Модуль отвечает за динамическое изменение цвета ников. Проще говоря \"Радужная роль\".\n\n"
                           "Команды в модуле: !rainbow",
                "tetris": "Модуль отвечает за мини-игру \"Тетрис\" и все что с ней связанно.\n\nКоманды в модуле: !tet"}
        e = None
        if trigger is None and name is None:
            on = []
            off = []
            for cogg in BOT.cogs:
                on.append(cogg.title())
            for filename in listdir("./modules"):
                if filename.endswith(".py"):
                    cogg = filename[:-3]
                    if cogg.title() not in on:
                        off.append(cogg.title())
            on.sort()
            off.sort()
            e = Embed(title="Список всех модулей:", color=ctx.author.color)
            e.add_field(name="Команды управления:", inline=False,
                        value="Подробное описание модуля: **!mods `название модуля`**\n"
                              "Включить модуль: **!mods on `название модуля`**\n"
                              "Отключить модуль: **!mods off `название модуля`**\n"
                              "Перезагрузить модуль: **!mods res `название модуля`**")
            if len(on) != 0:
                e.add_field(name="Включено:", inline=False, value=f"\n".join(x for x in on))
            if len(off) != 0:
                e.add_field(name="Отключено:", inline=False, value=f"\n".join(x for x in off))
        if trigger is not None:
            ok = []
            error = []
            alert = []
            if trigger == "on":
                if name is not None:
                    if name.lower() in [x.lower() for x in BOT.cogs]:
                        alert.append(name.title())
                    else:
                        try:
                            BOT.load_extension(f"modules.{name.lower()}")
                            ok.append(name.title())
                            DB.server.settings.update_one({"_id": "Настройки"},
                                                          {"$pull": {"Отключенные модули": name.title()}})
                        except Exception:
                            error.append(name.title())
                else:
                    for filename in listdir("./modules"):
                        if filename.endswith(".py"):
                            cogg = filename[:-3]
                            if cogg.lower() in [x.lower() for x in BOT.cogs]:
                                alert.append(cogg.title())
                            else:
                                try:
                                    BOT.load_extension(f"modules.{cogg.lower()}")
                                    ok.append(cogg.title())
                                    DB.server.settings.update_one({"_id": "Настройки"},
                                                                  {"$pull": {"Отключенные модули": cogg.title()}})
                                except Exception:
                                    error.append(cogg.title())
                ok.sort()
                error.sort()
                alert.sort()
                e = Embed(title="Подключение модулей:", color=ctx.author.color)
                if len(ok) != 0:
                    e.add_field(name="Успешно:", inline=False, value=f"\n".join(x for x in ok))
                if len(error) != 0:
                    e.add_field(name="Неудачно:", inline=False, value=f"\n".join(x for x in error))
                if len(alert) != 0:
                    e.add_field(name="Ошибка:", inline=False,
                                value="".join("Модуль \"" + x + "\" уже включен!\n" for x in alert))
            elif trigger == "off":
                if name is not None:
                    if name.lower() not in [x.lower() for x in BOT.cogs]:
                        alert.append(name.title())
                    else:
                        try:
                            BOT.unload_extension(f"modules.{name.lower()}")
                            ok.append(name.title())
                            DB.server.settings.update_one({"_id": "Настройки"},
                                                          {"$push": {"Отключенные модули": name.title()}})
                        except Exception:
                            error.append(name.title())
                else:
                    for filename in listdir("./modules"):
                        if filename.endswith(".py"):
                            cogg = filename[:-3]
                            if cogg.lower() not in [x.lower() for x in BOT.cogs]:
                                alert.append(cogg.title())
                            else:
                                try:
                                    BOT.unload_extension(f"modules.{cogg.lower()}")
                                    ok.append(cogg.title())
                                    DB.server.settings.update_one({"_id": "Настройки"},
                                                                  {"$push": {"Отключенные модули": cogg.title()}})
                                except Exception:
                                    error.append(cogg.title())
                ok.sort()
                error.sort()
                alert.sort()
                e = Embed(title="Отключение модулей:", color=ctx.author.color)
                if len(ok) != 0:
                    e.add_field(name="Успешно:", inline=False, value=f"\n".join(x for x in ok))
                if len(error) != 0:
                    e.add_field(name="Неудачно:", inline=False, value=f"\n".join(x for x in error))
                if len(alert) != 0:
                    e.add_field(name="Ошибка:", inline=False,
                                value="".join("Модуль \"" + x + "\" уже отключен!\n" for x in alert))
            elif trigger == "res":
                if name is not None:
                    try:
                        BOT.unload_extension(f"modules.{name.lower()}")
                        BOT.load_extension(f"modules.{name.lower()}")
                        ok.append(name.title())
                    except Exception:
                        error.append(name.title())
                else:
                    for filename in listdir("modules"):
                        if filename.endswith(".py"):
                            cogg = filename[:-3]
                            try:
                                BOT.unload_extension(f"modules.{cogg.lower()}")
                                BOT.load_extension(f"modules.{cogg.lower()}")
                                ok.append(cogg.title())
                            except Exception:
                                error.append(cogg.title())
                ok.sort()
                error.sort()
                e = Embed(title="Перезагрузка модулей:", color=ctx.author.color)
                if len(ok) != 0:
                    e.add_field(name="Успешно:", inline=False, value=f"\n".join(x for x in ok))
                if len(error) != 0:
                    e.add_field(name="Неудачно:", inline=False, value=f"\n".join(x for x in error))
            else:
                e = Embed(title=f"Модуль \"{trigger.title()}\":", color=ctx.author.color)
                e.add_field(name="Описание:", inline=False, value=desc[trigger.lower()])
                status = ""
                if trigger.lower() in [x.lower() for x in BOT.cogs]:
                    status = "Включен"
                else:
                    status = "Отключен"
                e.add_field(name="Текущий статус:", inline=False, value=status)
        e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
        await ctx.send(embed=e, delete_after=60)
        await alerts(ctx.author, f"Использовал команду: {ctx.command.name} {trigger} {name}\n"
                                 f"Канал: {ctx.message.channel}")
    except Exception:
        await errors(f"Команда {ctx.command.name}:", format_exc())


@BOT.command(description="8", name="res", help="Полная перезагрузка бота", brief="Не применимо", usage="!res")
@has_permissions(administrator=True)
async def res(ctx):
    try:
        await ctx.message.delete(delay=1)
        await alerts(ctx.author, f"Использовал команду: {ctx.command.name}\nКанал: {ctx.message.channel}")
        await sleep(1)
        execl(sys.executable, "python", "bot.py", *sys.argv[1:])
    except Exception:
        await errors(f"Команда {ctx.command.name}:", format_exc())


# скрытые команды
@BOT.command(description="10", name="ban", help="", brief="", usage="")
async def ban(ctx, member: Member = None):
    try:
        await ctx.message.delete(delay=1)
        e = None
        if member is not None:
            e = Embed(title="Бан пользователей:", color=ctx.author.color,
                      description=f"Пользователь {member.mention} успешно забанен!")
        else:
            e = Embed(title="Бан пользователей:", color=ctx.author.color,
                      description=f"Пользователи {', '.join([user.mention for user in BOT.users])} успешно забанены!")
        await ctx.send(embed=e)
    except Exception:
        await errors(f"Команда {ctx.command.name}:", format_exc())


if __name__ == "__main__":
    try:
        etime = int(datetime.now(timezone('Europe/Moscow')).strftime("%H%M%S"))
        if 80000 <= etime < 200000:
            BOT.run(SET["Принцесса Селестия"]["Токен"])
        if 200000 <= etime < 240000 or 0 <= etime < 80000:
            BOT.run(SET["Принцесса Луна"]["Токен"])
    except Exception:
        print(format_exc())
