import asyncio
from twitchio.ext import commands
from utils import CONFIG


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=CONFIG['ACCESS_TOKEN'],
            prefix='?',
            initial_channels=['klork05']
        )

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        print(message.content)
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!')


if __name__ == '__main__':
    # Создаем новый event loop и устанавливаем его как текущий
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bot = Bot()
    bot.run()  # bot.run() блокирует основной поток
