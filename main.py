import os
import json
import time
import datetime
from discord_components import DiscordComponents
from discord_components import SelectOption, Select
from discord import Embed
from discord_slash import SlashCommand
import string
import secrets
from discord.ext import commands, tasks
from keep_alive import keep_alive
import discord
from errors import UserErrors
from get_users import Get_User
from embed_manager import User_Embed_Manager


# Clear shortcut function
def clear():
    os.system("clear")


"""####################### System Variables #################################"""
intents = discord.Intents().all()
client = commands.Bot(command_prefix=".", intents=intents)
slash = SlashCommand(client, sync_commands=True)


# ON READY
@client.event
async def on_ready():
    DiscordComponents(client)
    clear()
    get_poll.start()
    clear_data.start()
    print(f"Logged in as {client.user}")
    print(f"Ping (ms): {round(client.latency * 1000)}")


guild_id = [892084983072718918]
bot_color = 0x642589


# GENERATE RANDOM STRING
def generate_random_string(length):
    characters = string.ascii_letters + string.digits

    r = "".join(secrets.choice(characters) for i in range(length))

    return r


# GENERATE TRANSACTION ID
def generate_code(length: int = 1, length_l: int = 5):
    code = ""
    for i in range(length):
        if i == length - 1:
            code += f"{generate_random_string(length_l)}"
        else:
            code += f"{generate_random_string(length_l)}-"

    return code


def get_timestamp_now(date: str):
    dt = datetime.datetime.strptime(date, "%d.%m.%Y")
    timestamp = datetime.datetime.timestamp(dt)
    return timestamp


async def slash_button_ctx(ctx, client):
    empty = await ctx.send(content="᲼")
    # msg= await dc.fetch_component_message(empty)
    ctx = await client.get_context(empty)
    await empty.delete()
    return ctx


# FIND USER BY COORDINATES
options = [
    {
        "name": "coordx",
        "description": "Coordonnées de l'utilisateur en X",
        "type": 4,
        "required": True,
    },
    {
        "name": "coordy",
        "description": "Coordonnées de l'utilisateur en Y",
        "type": 4,
        "required": True,
    },
]


@slash.slash(  # DECALARING AND SETTING SLASH COMMAND
    name="Find_User_By_Coordinates",
    description="Trouve un utilisateur ainsi que son discord avec ses coordonnées",
    guild_ids=guild_id,
    options=options,
)
async def Find_User_By_Coordonates(sctx, coordx, coordy):
    try:
        user = await Get_User(sctx.guild).get_user_by_coordonates([coordx, coordy])
    except UserErrors.UserNotFound:
        em = Embed(title="Cet utilisateur n'a pas pu être trouvé", description="Avez-vous tapé les bonnes coordonnées ?", color=bot_color)
        await sctx.send(embed=em, hidden=True)
        return

    msg = await sctx.send(
        "Your request is being processed... (It can take up to 3 minutes)"
    )

    neighbors = await Get_User(sctx.guild).get_neighbors([coordx, coordy])

    user_embed = User_Embed_Manager(user, neighbors).simple_user_embed(neighbors=True)

    await msg.delete()
    await sctx.send(embed=user_embed, hidden=True)


# FIND USER BY USERNAME
options = [
    {
        "name": "usrnm",
        "description": "Le pseudo de l'utilisateur",
        "type": 3,
        "required": True,
    }
]


@slash.slash(  # DECLARING AND SETTING SLASH COMMAND
    name="Find_User_By_Username",
    description="Trouve un utilisateur et ses coordonnées par pseudo.",
    guild_ids=guild_id,
    options=options,
)
async def find_user_by_username(sctx, usrnm: str):
    try:
        user = await Get_User(sctx.guild).get_user_by_username(usrnm)  # Getting user object
    except UserErrors.UserNotFound:
        em = Embed(
            title="Cet utilisateur n'a pas pu être trouvé",
            description="Avez-vous tapé le bon nom d'utilisateur ?",
            color=bot_color,
        )
        await sctx.send(embed=em, hidden=True)
        return

    msg = await sctx.send(
        "Your request is being processed... (It can take up to 3 minutes)"
    )

    neighbors = await Get_User(sctx.guild).get_neighbors([user.coord[0], user.coord[1]])

    # USER
    user_embed = User_Embed_Manager(user, neighbors)

    await msg.delete()
    await sctx.send(embed=user_embed, hidden=True)


# POLL
# POLL BAR
def poll_bar(msg_id, hidden=False):
    with open("polls.json", "r") as f:
        polls = json.load(f)

    desc = ""

    poll = polls[str(msg_id)]

    total = poll["total"]

    if hidden:
        for option in poll["options"].keys():
            desc += f"**{option.capitalize()}**\n\n"

        desc += f"Total Votes: {total}"

    else:
        for option in poll["options"].keys():
            option_count = poll["options"][option]

            try:
                option_pct = int((option_count * 100) / total)

                option_bar_count = int(option_pct / 2.5)

                option_bar = "\u258c" * option_bar_count

                desc += f"**{option.capitalize()}**\n{option_bar} **{option_pct}%**\n\n"

            except ZeroDivisionError:
                desc += f"**{option.capitalize()}**\n**0%**\n\n"

    return desc


# COMMAND
options = [
    {"name": "title", "description": "Le titre du vote", "type": 3, "required": True},
    {
        "name": "choices",
        "description": "Les choix (séparez avec '&')",
        "type": 3,
        "required": True,
    },
    {
        "name": "locked",
        "description": "Si Vrai les participants ne peuvent pas modifier leur vote",
        "type": 5,
        "required": False,
    },
    {
        "name": "hidden",
        "description": "Si Vrai les participants ne peuvent pas voir les résultats avant la fin",
        "type": 5,
        "required": False,
    },
]


@slash.slash(
    name="Poll", description="Create Polls", guild_ids=guild_id, options=options
)
async def poll(ctx, title, choices, locked=False, hidden=False):
    sctx = ctx
    ctx = await slash_button_ctx(ctx, client)
    opt = []
    new_poll = {
        "channel_id": sctx.channel.id,
        "title": title,
        "options": {},
        "total": 0,
        "users": {},
        "locked": locked,
        "hidden": hidden,
    }

    o = 0
    for option in choices.split("&"):
        o += 1
        opti = SelectOption(label=option, value=option.lower())

        new_poll["options"][str(option.lower())] = 0
        opt.append(opti)

    components = [
        Select(placeholder="Select your choice here", options=opt, max_values=1)
    ]

    desc = ""
    if hidden:
        for option in new_poll["options"].keys():
            desc += f"**{option.capitalize()}**\n\n"
        desc += "Total Votes: 0"

    else:
        for option in new_poll["options"].keys():
            desc += f"**{option.capitalize()}**\n**0%**\n\n"

    em = Embed(title=title, description=desc, color=bot_color)

    if locked:
        em.set_footer(text="Une fois que vous avez fait votre choix vous ne pourrez plus le modifier. Réfléchissez !")

    try:
        msg = await ctx.send(embed=em, components=components)
    except discord.errors.HTTPException:
        em = Embed(title="You can't put the same choice twice.", color=bot_color)
        await sctx.send(embed=em, hidden=True)
        return

    with open("polls.json", "r") as f:
        polls = json.load(f)

    polls[str(msg.id)] = new_poll

    with open("polls.json", "w") as f:
        json.dump(polls, f, indent=4)

    get_poll.restart()


# STOP POLL
async def fetch_poll_options():
    with open("polls.json", "r") as f:
        polls = json.load(f)

    options = []

    for key in polls.keys():
        msg_id = key
        poll = polls[key]
        title = poll["title"]
        options.append(SelectOption(label=title, value=msg_id))

    return options


@slash.slash(name="End_Poll", description="Stop a poll", guild_ids=guild_id)
async def end_poll(ctx):
    sctx = ctx
    ctx = await slash_button_ctx(ctx, client)

    with open("polls.json", "r") as f:
        polls = json.load(f)

    if polls == {}:
        em = Embed(title="There is no polls to end", color=bot_color)
        await sctx.send(embed=em, hidden=True)
        return

    em = Embed(title="Chose a poll to end", color=bot_color)
    options = await fetch_poll_options()
    components = [Select(placeholder="Select a poll to end", options=options)]

    msg = await ctx.send(embed=em, components=components)
    res = await client.wait_for(
        "select_option",
        check=lambda i: i.author == sctx.author and i.channel == sctx.channel,
    )
    await msg.delete()

    values = res.values
    key = values[0]
    poll = polls[key]
    message_id = key
    channel = client.get_channel(poll["channel_id"])
    desc = poll_bar(key)

    p_msg = await channel.fetch_message(message_id)
    await p_msg.delete()

    em = Embed(
        title=f"Result For Poll | {poll['title']}",
        description=desc,
        color=bot_color,
        timestamp=datetime.datetime.utcnow(),
    )
    em.add_field(name="Total Sigular Answers", value=poll["total"])

    del polls[key]

    with open("polls.json", "w") as f:
        json.dump(polls, f, indent=4)

    await channel.send(embed=em)
    await sctx.send(f"'{poll['title']}' Poll ended", hidden=True)
    get_poll.restart()


# SEE POLLS
async def fetch_polls():
    with open("polls.json", "r") as f:
        polls = json.load(f)

    polls_list = ""

    for key in polls.keys():
        poll = polls[key]
        title = poll["title"]
        msg_id = key
        channel = client.get_channel(poll["channel_id"])
        msg = await channel.fetch_message(msg_id)
        url = str(msg.jump_url)
        total = poll["total"]
        choices = len(poll["options"])
        polls_list += f"[**{title}**]({url} 'See The Poll') | Total Choices: `{choices}` | Total Votes: `{total}`\n"

    if polls_list == "":
        polls_list = None

    return polls_list


@slash.slash(name="See_Polls", description="See all active polls", guild_ids=guild_id)
async def see_polls(ctx):
    polls_list = await fetch_polls()

    if polls_list is None:
        em = Embed(title="There is no polls", color=bot_color)
        await ctx.send(embed=em, hidden=True)
        return

    em = Embed(title="Polls", description=polls_list, color=bot_color)
    await ctx.send(embed=em, hidden=True)


# GET POLL
@tasks.loop(minutes=60)
async def get_poll():
    while True:
        with open("polls.json", "r") as f:
            polls = json.load(f)

        res = await client.wait_for(
            "select_option",
            check=lambda i: any(str(i.message.id) == key for key in polls.keys()),
        )
        values = res.values

        if str(res.message.id) in polls.keys():

            poll = polls[str(res.message.id)]
            users = polls[str(res.message.id)]["users"]
            locked = polls[str(res.message.id)]["locked"]
            hidden = polls[str(res.message.id)]["hidden"]

            if str(res.author.id) in users.keys():
                if locked:
                    await res.send(content="You can't change your vote. Sorry !")
                    continue

                await res.send(
                    content=f"You selected '**{res.values[0].capitalize()}**'"
                )

                user_choice = users[str(res.author.id)]

                poll["options"][user_choice] -= 1
                poll["options"][values[0]] += 1
                # del users[str(res.author.id)]
                users[str(res.author.id)] = values[0]

            else:
                await res.send(
                    content=f"You selected '**{res.values[0].capitalize()}**'"
                )

                poll["users"][str(res.author.id)] = values[0]
                poll["options"][values[0]] += 1
                poll["total"] += 1

            with open("polls.json", "w") as f:
                json.dump(polls, f, indent=4)

            if not hidden:
                desc = poll_bar(str(res.message.id))
            else:
                desc = poll_bar(str(res.message.id), hidden=True)

            em = Embed(title=poll["title"], description=desc, color=bot_color)

            if locked:
                em.set_footer(
                    text="Une fois que vous avez fait votre choix vous ne pourrez plus le modifier. Réfléchissez !"
                )

            await res.message.edit(embed=em)


options = [
    {
        "name": "coordx",
        "description": "Coordonnées de l'utilisateur en X",
        "type": 4,
        "required": True,
    },
    {
        "name": "coordy",
        "description": "Coordonnées de l'utilisateur en Y",
        "type": 4,
        "required": True,
    },
    {
        "name": "rayon",
        "description": "Le rayon de recherche (1 par défaut Max 3)",
        "type": 4,
        "required": False,
    },
]


@slash.slash(
    name="Find_Neighbors",
    description="Trouve les voisins d'une coordonnée dans un rayon défini",
    guild_ids=guild_id,
    options=options,
)
async def find_neighbors(sctx, coordx, coordy, rayon=1):
    try:
        user = await get_info_by_coordonates(sctx.guild, [coordx, coordy])
    except UserErrors.UserNotFound:
        em = Embed(
            title="Cet utilisateur n'a pas pu être trouvé",
            description="Avez-vous tapé la bonne nom coordonnée ?",
            color=bot_color,
        )
        await sctx.send(embed=em, hidden=True)
        return

    msg = await sctx.send("Your request is being processed... (It can take up to 3 minutes)")

    coord1 = [(coordx - rayon), (coordy - rayon)]
    coord2 = [(coordx + rayon), (coordy + rayon)]

    if rayon > 3:
        em = Embed(
            title="Le rayon est trop grand", description="Max 3", color=bot_color
        )
        await sctx.send(embed=em, hidden=True)
        return

    neighbors = await get_users_in_era(sctx.guild, coord1, coord2)

    desc = f"**User**: `{user.username}`\n**Discord**: {user.discord_mention}\n**Coordonnées**: `{str(user.coord).replace(', ', ':')}`\n**Region :** {region}\n**Color**: `<<` Couleur de l'embed\n=== **__NEIGHBORS__** ===\n\n"
    val = ""
    vals = []

    i = 0
    for neighbor in neighbors:
        i += 1
        n_dict = neighbor
        try:
            member_mention = n_dict["mention"]
        except KeyError:
            member_mention = "Not Found"

        try:
            region = n_dict["region"]
        except KeyError:
            region = "No Region"

        try:
            username = n_dict["username"]
            coord = n_dict["coord"]
            color = n_dict["color"]

            if len(desc) + 160 < 4000:
                desc += f"**__Username:__** `{username}`\n**Discord:** {member_mention}\n**Coordonnées:** `{coord}`\n**Region :** {region}\n\n"

            else:
                if len(val) + 160 < 1000:
                    val += f"**__Username:__** `{username}`\n**Discord:** {member_mention}\n**Coordonnées:** `{coord}`\n**Region :** {region}\n\n"
                else:
                    vals.append(val)
                    val = ""

        except KeyError:
            pass

    # USER
    try:
        member_mention = user["mention"]
    except KeyError:
        member_mention = "Not Found"

    try:
        region = user["region"]
    except KeyError:
        region = "No Region"

    username = user["username"]
    coord = user["coord"]
    color = user["color"]

    em = Embed(
        title=f"User Infos for {username} {str(list(coord)).replace(', ', ':')}",
        description=desc,
        timestamp=datetime.datetime.utcnow(),
        color=color,
    )

    for val in vals:
        em.add_field(name="=== **__NEIGHBORS__** ===", value=val)

    await msg.delete()
    await sctx.send(embed=em, hidden=True)


@tasks.loop(hours=1)
async def clear_data():
    with open("system.json") as f:
        sys = json.load(f)
        clear_time = sys["clear_time"]
        f.close()

    if clear_time > time.time():

        with open("database.json", "r") as f:
            db = json.load(f)
            f.close()

        db = {}

        with open("database.json", "w") as f:
            json.dump(db, f, indent=4)
            f.close()

        print(
            f"Data Cleared on {datetime.datetime.strftime(datetime.datetime.utcnow(), '%x at %X')}"
        )

        sys["clear_time"] = time.time() + (1 * 60 * 60)

        with open("system.json") as f:
            json.dump(sys, f, indent=4)
            f.close()


@slash.slash(
    name="Manual_Refresh",
    description="Un refresh manuel de la db (Pour de uniquement)",
    guild_ids=guild_id,
)
async def manual_refresh(sctx):
    with open("system.json") as f:
        sys = json.load(f)
        f.close()

    with open("database.json", "r") as f:
        db = json.load(f)
        f.close()

    db = {}

    with open("database.json", "w") as f:
        json.dump(db, f, indent=4)
        f.close()

    print(
        f"Data Cleared Manually on {datetime.datetime.strftime(datetime.datetime.utcnow(), '%x at %X')}"
    )

    sys["clear_time"] = time.time() + (1 * 60 * 60)

    with open("system.json") as f:
        json.dump(sys, f, indent=4)
        f.close()

    await sctx.send(
        f"Data Cleared Manually on {datetime.datetime.strftime(datetime.datetime.utcnow(), '%x at %X')}",
        hidden=True,
    )


keep_alive()
client.run(os.getenv("TOKEN"))
