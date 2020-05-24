# queue.py

import discord
from discord.ext import commands
import asyncio


class QueueCog(commands.Cog):
    """ Cog to manage queues of players among multiple servers. """

    def __init__(self, bot):
        """ Set attributes. """
        self.bot = bot
        self.last_queue_msgs = {}

    async def queue_embed(self, guild, title=None):
        """ Method to create the queue embed for a guild. """
        queued_ids = await self.bot.db_helper.get_queued_users(guild.id)
        guild_data = await self.bot.db_helper.get_guild(guild.id)
        capacity = guild_data['capacity']

        if title:
            title += f' ({len(queued_ids)}/{capacity})'

        if len(queued_ids) == 0:  # If there are no users in the queue
            queue_str = '_The queue is empty..._'
        else:  # Users still in queue
            queue_str = ''.join(f'{num}. <@{user_id}>\n' for num, user_id in enumerate(queued_ids, start=1))

        embed = self.bot.embed_template(title=title, description=queue_str)
        embed.set_footer(text='Players will receive a notification when the queue fills up')
        return embed

    async def update_last_msg(self, ctx, embed):
        """ Send embed message and delete the last one sent. """
        msg = self.last_queue_msgs.get(ctx.guild)

        if msg is not None:
            await msg.delete()

        self.last_queue_msgs[ctx.guild] = await ctx.send(embed=embed)

    @commands.command(brief='Join the queue')
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=True)  # Only process one command per guild at once
    async def join(self, ctx):
        """ Check if the member can be added to the guild queue and add them if so. """
        name = ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name

        if not await self.bot.api_helper.is_linked(ctx.author.id):  # Message author isn't linked
            title = f'Unable to add **{name}**: Their account is not linked'
        else:  # Message author is linked
            awaitables = [
                self.bot.api_helper.get_player(ctx.author.id),
                self.bot.db_helper.insert_users(ctx.author.id),
                self.bot.db_helper.get_queued_users(ctx.guild.id),
                self.bot.db_helper.get_guild(ctx.guild.id)
            ]
            results = await asyncio.gather(*awaitables, loop=self.bot.loop)
            player = results[0]
            queue_ids = results[2]
            capacity = results[3]['capacity']

            if ctx.author.id in queue_ids:  # Author already in queue
                title = f'Unable to add **{name}**: Already in the queue'
            elif len(queue_ids) >= capacity:  # Queue full
                title = f'Unable to add **{name}**: Queue is full'
            elif not player:  # ApiHelper couldn't get player
                title = f'Unable to add **{name}**: Cannot verify match status'
            elif player.in_match:  # User is already in a match
                title = f'Unable to add **{name}**: They are already in a match'
            else:  # User can be added
                await self.bot.db_helper.insert_queued_users(ctx.guild.id, ctx.author.id)
                queue_ids += [ctx.author.id]
                title = f'**{name}** has been added to the queue'

                # Check and burst queue if full
                if len(queue_ids) == capacity:
                    queue_users = [self.bot.get_user(user_id) for user_id in queue_ids]
                    match_cog = self.bot.get_cog('MatchCog')

                    try:
                        all_readied = await match_cog.start_match(ctx, queue_users)
                    except asyncio.TimeoutError:
                        return

                    if all_readied:
                        await self.bot.db_helper.delete_queued_users(ctx.guild.id, *queue_ids)

                    return

        embed = await self.queue_embed(ctx.guild, title)

        # Delete last queue message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Leave the queue (or the bursted queue)')
    async def leave(self, ctx):
        """ Check if the member can be remobed from the guild and remove them if so. """
        removed = await self.bot.db_helper.delete_queued_users(ctx.guild.id, ctx.author.id)
        name = ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name

        if ctx.author.id in removed:
            title = f'**{name}** has been removed from the queue'
        else:
            title = f'**{name}** isn\'t in the queue'

        embed = await self.queue_embed(ctx.guild, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(brief='Display who is currently in the queue')
    async def view(self, ctx):
        """ Display the queue as an embed list of mentioned names. """
        title = 'Players in queue for 10-mans'
        embed = await self.queue_embed(ctx.guild, title)

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @commands.command(usage='remove <user mention>',
                      brief='Remove the mentioned user from the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def remove(self, ctx):
        """ Remove the specified user from the queue. """
        try:
            removee = ctx.message.mentions[0]
        except IndexError:
            embed = discord.Embed(title='Mention a player in the command to remove them', color=self.bot.color)
            await ctx.send(embed=embed)
        else:
            removed = await self.bot.db_helper.delete_queued_users(ctx.guild.id, removee.id)
            name = removee.nick if removee.nick is not None else removee.display_name

            if removee.id in removed:
                title = f'**{name}** has been removed from the queue'
            else:
                title = f'**{name}** is not in the queue'

            embed = await self.queue_embed(ctx.guild, title)

            # Update queue display message
            await self.update_last_msg(ctx, embed)

    @commands.command(brief='Empty the queue (must have server kick perms)')
    @commands.has_permissions(kick_members=True)
    async def empty(self, ctx):
        """ Reset the guild queue list to empty. """
        await self.bot.db_helper.delete_all_queued_users(ctx.guild.id)
        embed = await self.queue_embed(ctx.guild, 'The queue has been emptied')

        # Update queue display message
        await self.update_last_msg(ctx, embed)

    @remove.error
    @empty.error
    async def remove_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot remove players without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.bot.color)
            await ctx.send(embed=embed)

    @commands.command(brief='Set the capacity of the queue (Must have admin perms)')
    @commands.has_permissions(administrator=True)
    async def cap(self, ctx, *args):
        """ Set the queue capacity. """
        guild_data = await self.bot.db_helper.get_guild(ctx.guild.id)
        capacity = guild_data['capacity']

        if len(args) == 0:  # No size argument specified
            embed = discord.Embed(title=f'The current queue capacity is {capacity}', color=self.bot.color)
        else:
            new_cap = args[0]

            try:
                new_cap = int(new_cap)
            except ValueError:
                embed = discord.Embed(title=f'{new_cap} is not an integer', color=self.bot.color)
            else:
                if new_cap == capacity:
                    embed = discord.Embed(title=f'Capacity is already set to {capacity}', color=self.bot.color)
                elif new_cap < 2 or new_cap > 100:
                    embed = discord.Embed(title='Capacity is outside of valid range', color=self.bot.color)
                else:
                    await self.bot.db_helper.delete_all_queued_users(ctx.guild.id)
                    await self.bot.db_helper.update_guild(ctx.guild.id, capacity=new_cap)
                    embed = discord.Embed(title=f'Queue capacity set to {new_cap}', color=self.bot.color)
                    embed.set_footer(text='The queue has been emptied because of the capacity change')

        await ctx.send(embed=embed)

    @cap.error
    async def cap_error(self, ctx, error):
        """ Respond to a permissions error with an explanation message. """
        if isinstance(error, commands.MissingPermissions):
            await ctx.trigger_typing()
            missing_perm = error.missing_perms[0].replace('_', ' ')
            title = f'Cannot change queue capacity without {missing_perm} permission!'
            embed = discord.Embed(title=title, color=self.bot.color)
            await ctx.send(embed=embed)
