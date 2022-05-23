import sys
from os import execl
from re import findall
from traceback import format_exc

from discord import Embed
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from discord_components import Button, ButtonStyle
from pymongo import DESCENDING

from bot import DB, SET

PAGES = [page for page in DB.server.game.find()]


class Game(Cog):
    def __init__(self, bot):
        self.BOT = bot
        self.post.start()

    def cog_unload(self):
        self.post.cancel()

    async def messages(self, name, value):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                await self.BOT.get_user(uid).send(embed=Embed(
                    title="Сообщение!", color=0x008000).add_field(name=name, value=value))
        except Exception:
            print(format_exc())

    async def alerts(self, name, value):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                await self.BOT.get_user(uid).send(embed=Embed(
                    title="Уведомление!", color=0xFFA500).add_field(name=name, value=value))
        except Exception:
            print(format_exc())

    async def errors(self, name, value, reset=0):
        try:
            for uid in [x for x in SET["Уведомления"].values()]:
                await self.BOT.get_user(uid).send(embed=Embed(
                    title="Ошибка!", color=0xFF0000).add_field(name=name, value=value))
            if reset == 1:
                execl(sys.executable, "python", "bot.py", *sys.argv[1:])
        except Exception:
            print(format_exc())

    async def pages(self, interaction, page):
        try:
            pid = int(findall(r"p(\d+)", page)[0]) - 1
            e = Embed(title="Похищенная пони", color=int(PAGES[pid]["Цвет"], 0), description=PAGES[pid]["Текст"])
            if "Изображение" in PAGES[pid]:
                e.set_image(url=PAGES[pid]["Изображение"])
            user = DB.server.users.find_one({"_id": interaction.user.id})
            if "Скрытые кнопки" in PAGES[pid] and len(set(user["Концовки"])) >= 17:
                await interaction.send(embed=e, components=eval(PAGES[pid]["Скрытые кнопки"]))
            else:
                await interaction.send(embed=e, components=eval(PAGES[pid]["Кнопки"]))
            DB.server.users.update_one({"_id": interaction.user.id}, {"$set": {"Страница": page}})
            if "Концовка" in PAGES[pid]:
                DB.server.users.update_one({"_id": interaction.user.id},
                                           {"$push": {"Концовки": PAGES[pid]["Концовка"]}})
        except Exception:
            await self.errors(f"Страница {page}:", format_exc())

    @loop(count=1)
    async def post(self):
        channel = DB.server.channels.find_one({"Название": "🦄похищенная_пони"})
        try:
            try:
                game = await self.BOT.get_channel(int(channel["_id"])).fetch_message(int(channel["Похищенная пони"]))
                await game.delete()
            except Exception:
                pass
            e = Embed(title="Похищенная пони: интерактивная игра-новелла", color=0xFF8C00,
                      description="Привет! Если ты первый раз сталкиваешься с такой игрой, обязательно прочита"
                                  "й этот раздел. Ну а если тебе не впервой, то можешь сразу начинать игру и о"
                                  "тправляться в путешествие!\n\nТо, как будет развиваться сюжет игры, зависит"
                                  " только от тебя. В этой истории тебе предстоит посмотреть на мир глазами Кэ"
                                  "ррот Топ, молодой земной пони, живущей на окраине Понивилля. По мере чтения"
                                  " тебе придётся время от времени принимать решения.\n\nИногда мелкие, иногда"
                                  " - важные, все они, так или иначе, повлияют на сюжет. Каждый раз в момент в"
                                  "ыбора тебе будет предложено два или больше вариантов. Просто щёлкай по кноп"
                                  "ке и читай, что случилось дальше. В книге есть 19 различных концовок, некот"
                                  "орые - счастливые, некоторые - не очень, но каждая уникальна. Историю можно"
                                  " проходить несколько раз, и сюжет ни разу не повторится!\n\nТеперь, когда т"
                                  "ы знаешь, как играть, смело жми на кнопку \"Начать новую игру\" и начинай с"
                                  "вое приключение. Удачи!\n\nИгра сохраняется автоматически после каждого дей"
                                  "ствия!\n\n**Автор**: Chris **Перевод**: Многорукий Удав **Вычитка**: Orhide"
                                  "ous, Hariester, Haveglory **Оформление**: ponyPharmacist")
            e.set_image(url="https://projects.everypony.ru/purloined-pony/pics/pp000.png")
            e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
            gameid = await self.BOT.get_channel(int(channel["_id"])).send(embed=e, components=[
                [Button(label="Начать новую игру", style=ButtonStyle.green),
                 Button(label="Продолжить игру", style=ButtonStyle.blue),
                 Button(label="Статистика")]])
            DB.server.channels.update_one({"Название": "🦄похищенная_пони"}, {"$set": {"Похищенная пони": gameid.id}})
        except Exception:
            await self.errors("Пост Игра:", format_exc())

    @Cog.listener()
    async def on_button_click(self, interaction):
        try:
            if interaction.component.label == "Начать новую игру":
                user = DB.server.users.find_one({"_id": interaction.user.id})
                if user["Страница"] == "p0":
                    await self.pages(interaction, "p1")
                else:
                    await interaction.send(
                        f"У вас обнаружена сохраненная игра! Хотите удалить ее и начать заново, или продолжить?",
                        components=[[Button(label="Продолжить игру", style=ButtonStyle.green),
                                     Button(label="Начать заново", id="p1", style=ButtonStyle.red)]])
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if interaction.component.label == "Продолжить игру":
                user = DB.server.users.find_one({"_id": interaction.user.id})
                if user["Страница"] != "p0":
                    await self.pages(interaction, user["Страница"])
                else:
                    await interaction.send(f"У вас нет сохраненной игры! Хотите начать новую?",
                                           components=[Button(label="Начать новую игру", style=ButtonStyle.green)])
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if interaction.component.label == "Статистика":
                users1 = DB.server.users.find()
                for user1 in users1:
                    try:
                        old = set(user1["Концовки"])
                        new = list(old)
                        DB.server.users.update_one({"_id": user1["_id"]}, {"$set": {"Концовки": new}})
                    except Exception:
                        pass
                sts = []
                users2 = DB.server.users.find().sort("Концовки", DESCENDING)
                for user2 in users2:
                    if len(user2["Концовки"]) != 0:
                        sts.append(f"<@{user2['_id']}>: Пройдено {len(user2['Концовки'])} из 19 концовок.")
                e = Embed(title="Статистика прохождения:", color=interaction.user.color,
                          description="\n\n".join([x for x in sts]))
                e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
                await interaction.send(embed=e)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.label}:", format_exc())
        try:
            if len(findall(r"p\d+", interaction.component.id)) != 0:
                await self.pages(interaction, interaction.component.id)
        except Exception:
            await self.errors(f"Кнопка {interaction.component.id}:", format_exc())


def setup(bot):
    bot.add_cog(Game(bot))
