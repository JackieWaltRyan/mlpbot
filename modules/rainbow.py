import sys
from asyncio import sleep
from os import execl
from traceback import format_exc

from discord import Embed, utils
from discord.ext.commands import Cog, command
from discord.ext.tasks import loop

from bot import DB, SET


class Rainbow(Cog):
    def __init__(self, bot):
        self.BOT = bot
        self.members = []
        users = DB.server.users.find({"Радуга": "Да"})
        for user in users:
            member = self.BOT.get_guild(798851582800035841).get_member(int(user["_id"]))
            self.members.append(member)
        self.rainbow.start()

    def cog_unload(self):
        self.rainbow.cancel()

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

    @loop()
    async def rainbow(self):
        try:
            roles, a, b = [role["_id"] for role in DB.server.roles.find({"Категория": "Радуга"})], 1, 0
            while True:
                for member in self.members:
                    try:
                        await member.add_roles(utils.get(member.guild.roles, id=int(roles[a])))
                        await member.remove_roles(utils.get(member.guild.roles, id=int(roles[b])))
                    except Exception:
                        pass
                a += 1
                b += 1
                if a == 6:
                    a = 0
                if b == 6:
                    b = 0
                await sleep(3)
        except Exception:
            await self.errors("Радуга:", format_exc())

    @command(description="4", name="rainbow", help="Сделать себе радужный ник", brief="`On` / `Off`",
             usage="!rainbow on")
    async def rainbowcommand(self, ctx, trigger: str = "on"):
        try:
            if trigger.lower() == "on" or trigger.lower() == "off":
                await ctx.message.delete(delay=1)
                e = None
                if trigger.lower() == "on":
                    DB.server.users.update_one({"_id": ctx.author.id}, {"$set": {"Радуга": "Да"}})
                    e = Embed(title="Радужная роль:", color=ctx.author.color,
                              description="Вы включили себе радужный ник!")
                if trigger.lower() == "off":
                    DB.server.users.update_one({"_id": ctx.author.id}, {"$set": {"Радуга": "Нет"}})
                    e = Embed(title="Радужная роль:", color=ctx.author.color,
                              description="Вы отключили себе радужный ник!")
                e.set_footer(text=SET["Футер"]["Текст"], icon_url=SET["Футер"]["Ссылка"])
                await ctx.send(embed=e, delete_after=60)
                await ctx.send("!cogs cjlkzrwuqxcnaznzsx")
        except Exception:
            await self.errors(f"Команда {ctx.command.name}:", format_exc())


def setup(bot):
    bot.add_cog(Rainbow(bot))
