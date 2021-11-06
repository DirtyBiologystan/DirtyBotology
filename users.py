import json
from typing import Union
from errors import UserErrors
import re


class User:
    """# User
    Creates a User object from identifier with database or from dict and saves to database

    ## Parameters
    ----------
    - `guild` : discord.guild
        - Guild instance of users' discord server

    - `identifier` : Union[list, str]
        - used to identify user and retreive info from database
    ----------

    ## Attributes
    ----------
    - `coord`
        - Coordinates of user on flag
    - `iteration`
        - The number of when user joined flag
    - `int_color`
        - The color of user's pixel in int (originally hex)
    - `index_in_flag`
        - index in flag of user
    - `discord_mention`
        - Mention of user's discord profile
    - `discord_id`
        - ID of user's discord profile
    ----------
    """
    async def __init__(self, guild, identifier: Union[list, str]):
        self.guild = guild

        with open("database.json", "r") as f:
            self.db = json.load(f)

        if isinstance(identifier, str):
            try:
                self.user_dict = self.db[self.username.lower()]
                self.set_attributes(self)

            except KeyError:
                raise UserErrors.UserNotFound(f"Could not find user with Username {identifier}")

        elif isinstance(identifier, list):
            if identifier in self.db.values():
                for key in self.db.keys():
                    parsed_dict = self.db[key]
                    if parsed_dict["coord"] == identifier:
                        self.user_dict = parsed_dict
                        break

                    self.set_attributes(self)

            else:
                raise UserErrors.UserNotFound(f"Could not find user with Coord {identifier}")
        else:
            raise UserErrors.UserNotFound("Type of identifier does not match any valid types")

    def set_attributes(self) -> None:
        """
        # Set Attrubutes
        Sets the attribues of the object. Can also update region and discord informations.

        ## Parameters
        ----------
        - None
        ----------

        ## Uses
        ----
        - `update_region_and_discord_info()`
            - Update the discord and region attributes informations
        ----

        ## Returns
        -------
        - None
        -------
        """
        try:
            self.coord = self.user_dict["coord"]
            self.iteration = self.user_dict["iter"]
            self.int_color = self.user_dict["color"]
            self.index_in_flag = self.user_dict["indexInFlag"]
            self.username = self.user_dict["username"]

        except KeyError as e:
            raise UserErrors.InvalidDictForm(f"Missing Key: {e.args[0]}")

        try:
            self.discord_mention = self.user_dict["mention"]
            self.discord_id = self.user_dict["member_id"]
        except KeyError:
            self.update_region_and_discord_info()

        try:
            self.region = self.user_dict["region"]
        except KeyError:
            self.update_region_and_discord_info()

    def to_dict(self) -> dict:
        """
        # To Dict
        Turns object to dictionary

        ## Parameters
        ----------
        - `None`
        ----------

        ## Returns
        -------
        - `Dict` : Dictionary of object
        -------
        """
        return {
            "username": self.username,
            "member_id": self.discord_id,
            "mention": self.discord,
            "coord": self.coord,
            "color": self.int_color,
            "iter": self.iteration,
            "indexInFlag": self.index_in_flag,
            "region": self.region
        }

    def store(self) -> None:
        """Converts self object to dict and stores dict into database file (database.json)

        uses: `reload()`"""

        self.reload(self)

        with open("database.json", "r") as f:
            self.db = json.load(f)
            f.close()

        self.db[self.username.lower()] = self.to_dict(self)

        with open("database.json", "w") as f:
            json.dump(self.db, f, indent=4)
            f.close()

        self.reload(self)

    def reload(self) -> None:
        """Reloads database file reference and all attributes of object

        uses: `set_attributes()`"""

        with open("database.json", "r") as f:
            self.db = json.load(f)
            f.close()

        self.set_attributes(self)

    def coord_match(self, member):
        member_display_name = member.display_name.lower()
        member_coord = re.search(".*?[([{]\s*(\d+)\s*[:;,]\s*(\d+)\s*[)}\]].*", member_display_name)

        coord_match = f"[{member_coord.group(1)}:{member_coord.group(2)}]" == str(self.coord)

        return coord_match

    def get_discord_user(self, username, coord):
        high_potential_match = []
        mid_potential_match = []
        low_potential_match = []
        username = username.lower()
        for member in self.guild.members:
            member_display_name = member.display_name.lower()

            member_coord = re.search(".*?[([{]\s*(\d+)\s*[:;,]\s*(\d+)\s*[)}\]].*", member_display_name)
            username_match = (username in member_display_name or username in member.name.lower())

            if member_coord is not None:
                coord_match = self.coord_match(self, member)
                if coord_match and username_match:
                    high_potential_match.append(member)
                elif username_match:
                    mid_potential_match.append(member)
                elif coord_match:
                    low_potential_match.append()
            else:
                return None, None

        if high_potential_match != []:
            match_list = sorted(high_potential_match, key=lambda x: (username in x.display_name.lower() or username in x.name.lower()) and coord_match(self, x))
            return match_list[0], "HIGH"

        elif mid_potential_match != []:
            match_list = sorted(mid_potential_match, key=lambda x: coord_match(self, x))
            return match_list[0], "MEDIUM"

        elif low_potential_match != []:
            match_list = sorted(low_potential_match, key=lambda x: username in x.display_name.lower() or username in x.name.lower())
            return match_list[0], "LOW"

        else:
            return None, None

    def get_user_region(self, coord: list) -> str:
        with open("regions.json", "r") as f:
            regions = json.load(f)

        stop = False
        for region_name in regions.keys():
            region_coord = regions[region_name]
            coord1 = region_coord[0]
            coord2 = region_coord[1]
            for x in range(coord1[1], coord2[1] + 1):
                if stop:
                    break
                for y in range(coord1[0], coord2[0] + 1):
                    if stop:
                        break
                    if str(coord) == str(list([y, x])):
                        return region_name
                        stop = True
                        break

        return None

    def update_region_and_discord_info(self):
        if "member_id" not in list(self.user_dict.keys()):
            try:
                discord_member, match_chance = self.get_discord_user(self.username, self.coord)

                self.discord_id = discord_member.id
                self.discord_mention = f"{discord_member.mention} | **Match chances:** {match_chance}"
                self.store(self)
            except AttributeError:
                pass

        if "region" not in list(self.user_dict.keys()):
            region = self.get_user_region(self.coord)

            if region is not None:
                self.user_dict["region"] = region
                self.store(self)
            else:
                pass

    @classmethod
    async def new_user(self, guild, user_dict: dict) -> "User":
        self.user_dict = user_dict
        self.set_attributes()
        self.reload()
        self.store()
        return self(self.guild, self.username)
