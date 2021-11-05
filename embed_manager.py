from discord.embeds import EmptyEmbed, Embed
from users import User
from errors import EmbedErrors
import datetime
from typing import Union

bot_color = 0x642589


class Embed_Manager:
    def __init__(self, title: str = EmptyEmbed, description: str = EmptyEmbed, timestamp=False, color=bot_color, fields: dict = None):
        embed = Embed(title=title, description=description, color=color)

        if timestamp:
            embed.timestamp = datetime.datetime.utcnow()
        if fields is not None:
            if not isinstance(fields, dict):
                raise EmbedErrors.InvalidNeighborType(f"Excpected dict got {type(fields)}")
            for field in fields:
                if not isinstance(field, dict):
                    raise EmbedErrors.InvalidNeighborType(f"Excpected dict got {type(field)}")
                embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])

        return embed


class User_Embed_Manager:
    def __init__(self, user: User, neighbors: Union[dict, list]):
        self.user = user
        self.neighbors = neighbors

    def get_user_data(self, user: User):
        try:
            discord = user.discord_mention
        except AttributeError:
            discord = "Not Found"
        try:
            region = user.region
        except AttributeError:
            region = "No Region"

        return discord, region

    def simple_user_embed(self, neighbors=True):
        self.user_embed = Embed(title=f"Informations for {self.user.username} {self.user.coord}", description="Ces informations peuvent ne pas être exactes dû aux problèmes de TP de certaines personnes sur le drapeau et au fait que les utilisateurs peuvent mentir par rapport à leur coordonnées sur discord.", color=self.user.int_color, timestamp=datetime.datetime.utcnow())

        discord, region = self.get_user_data(self.user)

        self.user_embed.add_field(name="Username", value=f"`{self.user.username}`", inline=True)
        self.user_embed.add_field(name="Discord", value=discord)
        self.user_embed.add_field(name="Coordonnées", value=f"`{str(self.user.coord).replace(', ', ':')}`", inline=True)
        self.user_embed.add_field(name="Region", value=f"`{region}`", inline=True)
        self.user_embed.add_field(name="Citoyen", value=f"No `{self.user.iter}`", inline=True)
        self.user_embed.add_field(name="Color", value="`<<` Couleur de l'embed", inline=False)

        if neighbors is not None:
            self.user_embed.add_field(name="᲼", value="========== **__NEIGHBORS__** ==========", inline=False)
            self.user_embed = self.simple_user_neighbors_formating(self.user_embed, self.neighbors)

            return self.user_embed
        else:
            return self.user_embed

    def simple_user_neighbors_formating(self):

        if not isinstance(self.neighbors, dict):
            raise EmbedErrors.InvalidNeighborType(f"Excpected dict got {type(self.neighbors)}")

        for neighbor in self.neighbors.keys():
            if not isinstance(neighbor, User):
                raise EmbedErrors.InvalidNeighborType(f"Excpected User got {type(neighbor)}")

            user = self.neighbors[neighbor]
            member_mention, region = self.get_user_data(self.user)

            try:
                self.user_embed.add_field(name=f"**__{neighbor.capitalize()}__**", value=f"**Username:** `{neighbor.username}`\n**Discord:** {member_mention}\n**Coordonnées:** `{user.coord}`\n**Region :** {region}\n**Citoyen No:** `{user.iter}`\n**Color:** `{str(hex(user.color)).replace('0x', '#')}`", inline=False)
            except AttributeError:
                self.user_embed.add_field(neighbor.capitalize(), value="No Neighbor", inline=False)

        return self.user_embed

    def area_neighbors_embed_format(self):
        desc, vals = self.custom_rayon_neighbors_formating(self)
        self.user_embed = Embed(title=f"User Infos for {self.user.username} {str(list(self.user.coord)).replace(', ', ':')}", description=desc, timestamp=datetime.datetime.utcnow(), color=self.user.int_color)
        for val in vals:
            self.user_embed.add_field(name="=== **__NEIGHBORS__** ===", value=val)

        return self.user_embed

    def custom_rayon_neighbors_formating(self):

        if not isinstance(self.neighbors, list):
            raise EmbedErrors.InvalidNeighborType(f"Excpected list got {type(self.neighbors)}")
        try:
            member_mention = self.user.discord_mention
        except AttributeError:
            member_mention = "Not Found"
        try:
            region = self.user.region
        except AttributeError:
            region = "No Region"

        username = self.user.username
        coord = self.user.coord

        desc = f"**User**: `{username}`\n**Discord**: {member_mention}\n**Coordonnées**: `{str(coord).replace(', ', ':')}`\n**Region :** {region}\n**Color**: `<<` Couleur de l'embed\n=== **__NEIGHBORS__** ===\n\n"
        val = ""
        vals = []
        for neighbor in self.neighbors:
            if not isinstance(neighbor, User):
                raise EmbedErrors.InvalidNeighborType(f"Excpected User got {type(neighbor)}")

            try:
                member_mention = neighbor.discord_mention
            except AttributeError:
                member_mention = "Not Found"
            try:
                region = neighbor.region
            except AttributeError:
                region = "No Region"
            try:
                username = neighbor.username
                coord = neighbor.coord
                if len(desc) + 160 < 4000:
                    desc += f"**__Username:__** `{username}`\n**Discord:** {member_mention}\n**Coordonnées:** `{coord}`\n**Region :** {region}\n\n"
                else:
                    if len(val) + 160 < 1000:
                        val += f"**__Username:__** `{username}`\n**Discord:** {member_mention}\n**Coordonnées:** `{coord}`\n**Region :** {region}\n\n"
                    else:
                        vals.append(val)
                        val = ""
            except AttributeError:
                pass
        return (desc, vals)
