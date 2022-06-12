import sys
from os import execl
from re import findall
from traceback import format_exc

from discord import Embed, utils
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from discord_components import Button, ButtonStyle, Select, SelectOption
from pymongo import ASCENDING

from bot import DB, SET

GHOST = int(DB.server.roles.find_one({"Название": "🦄 Духи"})["_id"])
PONY = int(DB.server.roles.find_one({"Название": "🦄 Пони"})["_id"])
NSFW = int(DB.server.roles.find_one({"Название": "🦄 18+"})["_id"])
RASES = [role for role in DB.server.roles.find({"Категория": "Расы"}).sort("Название", ASCENDING)]
MINIS = [minis for minis in DB.server.roles.find({"Категория": "Министерства"}).sort("Название", ASCENDING)]


class Posts(Cog):
    def __init__(self, bot):
        self.BOT = bot
        self.posts.start()

    def cog_unload(self):
        self.posts.cancel()

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
    async def posts(self):
        channel1 = DB.server.channels.find_one({"Название": "🦄добро_пожаловать"})
        try:
            try:
                rules = await self.BOT.get_channel(int(channel1["_id"])).fetch_message(int(channel1["Правила"]))
                await rules.delete()
            except Exception:
                pass
            e1 = Embed(title="Приветствуем тебя милая поняшка в нашем клубе!", color=0x008000,
                       description="Несмотря на название, этот клуб создан для простого и дружественного общения всех "
                                   "участников на любые возможные темы. Но тем не менее, для поддержания уютной и "
                                   "комфортной атмосферы, у нас есть несколько правил:")
            e1.add_field(name="Правила:",
                         value=":one: Не оскорблять других участников! Не обсуждать и не указывать на внешность, "
                               "голос, и подобные особенности других участников!\n\n"
                               ":two: Не обсуждать религию, политику, расовые особенности, и другие подобные темы, "
                               "которые могут задеть и оскорбить чувства других участников!\n\n"
                               ":three: В нашем клубе действует главный закон Эквестрии: Дружба - это чудо! И мы "
                               "искренне надеемся на поддержание этого всеми участниками клуба!")
            e1.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/915008263253266472/915419331804954634/PPWHY.png")
            e1.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            rulesid = await self.BOT.get_channel(int(channel1["_id"])).send(embed=e1, components=[[
                Button(label="Согласен!", style=ButtonStyle.green),
                Button(label="Не согласен!", style=ButtonStyle.red)]])
            DB.server.channels.update_one({"Название": "🦄добро_пожаловать"}, {"$set": {"Правила": rulesid.id}})
        except Exception:
            await self.errors("Пост Правила:", format_exc())
        channel2 = DB.server.channels.find_one({"Название": "🦄роли_сервера"})
        try:
            try:
                roles = await self.BOT.get_channel(int(channel2["_id"])).fetch_message(int(channel2["Роли"]))
                await roles.delete()
            except Exception:
                pass
            e2 = Embed(title="На нашем сервере есть 5 основные роли:", color=0xFFFF00,
                       description="<@&798875106868854804> - пони, которые управляют сервером.\n\n"
                                   "<@&798878290437603369> - основной табун, добрые пони сервера.\n\n"
                                   "<@&907438760663322634> - кто несогласен с правилами, наблюдают.\n\n"
                                   "<@&967109081733148693> - кто забыл об этом клубе, невидимы.\n\n"
                                   "<@&798880441390202891> - открывает доступ в мир Дискорда. Чтобы получить "
                                   "эту роль, нажмите на кнопку под этим сообщением.")
            e2.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/915008263253266472/915449826731257956/Cheer.png")
            e2.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            rolesid = await self.BOT.get_channel(int(channel2["_id"])).send(embed=e2,
                                                                            components=[[Button(label="18+")]])
            DB.server.channels.update_one({"Название": "🦄роли_сервера"}, {"$set": {"Роли": rolesid.id}})
        except Exception:
            await self.errors("Пост Роли:", format_exc())
        try:
            try:
                rases = await self.BOT.get_channel(int(channel2["_id"])).fetch_message(int(channel2["Расы"]))
                await rases.delete()
            except Exception:
                pass
            r1, r2 = [], [SelectOption(label="Без расы (убрать роль)", value="Без расы")]
            r3 = [SelectOption(label="Без расы (убрать роль)", value="Без расы")]
            for item1 in RASES:
                r1.append(f"<@&{item1['_id']}>\n\n")
                if len(r2) < 25:
                    r2.append(SelectOption(label=f"{item1['Название']}", value=f"{item1['_id']}"))
                else:
                    r3.append(SelectOption(label=f"{item1['Название']}", value=f"{item1['_id']}"))
            e3 = Embed(title="А еще у нас есть расы:", color=0xFFA500, description="".join([x for x in r1]))
            e3.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/915008263253266472/917800054042009630/chars.png")
            e3.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            if len(r3) == 0:
                rasesid = await self.BOT.get_channel(int(channel2["_id"])).send(embed=e3,
                                                                                components=[Select(options=r2)])
            else:
                rasesid = await self.BOT.get_channel(int(channel2["_id"])).send(embed=e3,
                                                                                components=[Select(options=r2),
                                                                                            Select(options=r3)])
            DB.server.channels.update_one({"Название": "🦄роли_сервера"}, {"$set": {"Расы": rasesid.id}})
        except Exception:
            await self.errors("Пост Расы:", format_exc())
        try:
            try:
                minis = await self.BOT.get_channel(int(channel2["_id"])).fetch_message(int(channel2["Министерства"]))
                await minis.delete()
            except Exception:
                pass
            m1, m2 = [], [SelectOption(label="Без министерства (убрать роль)", value="Без министерства")]
            for item2 in MINIS:
                m1.append(f"<@&{item2['_id']}>\n\n")
                m2.append(SelectOption(label=f"{item2['Название']}", value=f"{item2['_id']}"))
            e4 = Embed(title="И министерства:", color=0xFF0000, description="".join([x for x in m1]))
            e4.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/915008263253266472/917587318930550794/mine6.png")
            e4.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            minisid = await self.BOT.get_channel(int(channel2["_id"])).send(embed=e4, components=[[Select(options=m2)]])
            DB.server.channels.update_one({"Название": "🦄роли_сервера"}, {"$set": {"Министерства": minisid.id}})
        except Exception:
            await self.errors("Пост Министества:", format_exc())
        channel3 = DB.server.channels.find_one({"Название": "🦄неактивные"})
        try:
            try:
                await self.BOT.get_channel(int(channel3["_id"])).purge()
            except Exception:
                pass
            e5 = Embed(title="Актив и Неактив:", color=0x00BFFF,
                       description="Если вы не писали сообщения на сервере в течении 7 дней, вам автоматически дается "
                                   "роль <@&967109081733148693> и скрывается доступ ко всем каналам сервера. Чтобы "
                                   "убрать эту роль, и снова получить полный доступ к серверу, достаточно написать "
                                   "одно любое сообщение!")
            e5.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/915008263253266472/973990321866305637/SLWP.png")
            e5.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            await self.BOT.get_channel(int(channel3["_id"])).send(embed=e5)
        except Exception:
            await self.errors("Пост Неактивные:", format_exc())

    @Cog.listener()
    async def on_member_update(self, before, after):
        try:
            rsa, rsb, = [], []
            for role in after.roles:
                rsa.append(role.id)
            for role in before.roles:
                rsb.append(role.id)
            if len(rsa) > len(rsb):
                for x in rsb:
                    try:
                        rsa.remove(x)
                    except Exception:
                        pass
                if findall(str(rsa[0]), str(RASES)):
                    for items1 in RASES:
                        if int(items1["_id"]) == int(rsa[0]):
                            continue
                        await after.remove_roles(utils.get(after.guild.roles, id=int(items1["_id"])))
                if findall(str(rsa[0]), str(MINIS)):
                    for items2 in MINIS:
                        if int(items2["_id"]) == int(rsa[0]):
                            continue
                        await after.remove_roles(utils.get(after.guild.roles, id=int(items2["_id"])))
        except Exception:
            await self.errors("Удаление ролей:", format_exc())

    @Cog.listener()
    async def on_button_click(self, interaction):
        try:
            if interaction.component.label == "Согласен!":
                await interaction.send(f"Поздравляем! Вам выдана роль <@&{PONY}>")
                pony = utils.get(interaction.user.guild.roles, id=PONY)
                await interaction.user.add_roles(pony)
                await interaction.user.remove_roles(utils.get(interaction.user.guild.roles, id=GHOST))
                await self.alerts(interaction.user, f"Выдана роль: {pony}")
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if interaction.component.label == "Не согласен!":
                await interaction.send(f"Поздравляем! Вам выдана роль <@&{GHOST}>")
                ghost = utils.get(interaction.user.guild.roles, id=GHOST)
                await interaction.user.add_roles(ghost)
                await interaction.user.remove_roles(utils.get(interaction.user.guild.roles, id=PONY))
                await self.alerts(interaction.user, f"Выдана роль: {ghost}")
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if interaction.component.label == "18+":
                nsfw = utils.get(interaction.user.guild.roles, id=NSFW)
                if utils.get(interaction.user.roles, id=NSFW) is None:
                    await interaction.send(f"Поздравляем! Вам выдана роль <@&{NSFW}>")
                    await interaction.user.add_roles(nsfw)
                    await self.alerts(interaction.user, f"Выдана роль: {nsfw}")
                else:
                    await interaction.send(f"Поздравляем! Вам убрана роль <@&{NSFW}>")
                    await interaction.user.remove_roles(nsfw)
                    await self.alerts(interaction.user, f"Удалена роль: {nsfw}")
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())

    @Cog.listener()
    async def on_select_option(self, interaction):
        try:
            if interaction.values[0] == "Без расы":
                await interaction.send("Поздравляем! Вам убраны все роли Рас!")
                for item1 in RASES:
                    try:
                        await interaction.user.remove_roles(utils.get(interaction.user.guild.roles,
                                                                      id=int(item1["_id"])))
                    except Exception:
                        pass
                await self.alerts(interaction.user, f"Убраны все Расы")
            elif interaction.values[0] == "Без министерства":
                await interaction.send("Поздравляем! Вам убраны все роли Министерств!")
                for item2 in MINIS:
                    try:
                        await interaction.user.remove_roles(utils.get(interaction.user.guild.roles,
                                                                      id=int(item2["_id"])))
                    except Exception:
                        pass
                await self.alerts(interaction.user, f"Убраны все Министерства")
            else:
                await interaction.send(f"Поздравляем! Вам выдана роль <@&{int(interaction.values[0])}>")
                role = utils.get(interaction.user.guild.roles, id=int(interaction.values[0]))
                await interaction.user.add_roles(role)
                await self.alerts(interaction.user, f"Выдана роль: {role}")
        except Exception:
            await self.errors(f"Кнопка {interaction.values[0]}:", format_exc())


def setup(bot):
    bot.add_cog(Posts(bot))
