import requests as rq
import json
from typing import Union
from math import sqrt
from users import User, UserErrors


class Get_User:
    def __init__(self, guild):
        self.guild = guild

    def coord_to_index(self, xy: tuple):
        x = xy[0]
        y = xy[1]
        if x < 2 * y - 1:
            return 2 * (y ** 2) - 4 * y + x + 2
        else:
            return ((x + 1) // 2) ** 2 * 2 - ((x % 2) + 1) * (x + 1) // 2 + y

    def index_to_coord(self, n: int):
        epoch = int(sqrt((n - 1) // 2)) + 1
        if n <= 2 * epoch * (epoch - 1):
            x = n - 2 * (epoch - 1) ** 2
            y = epoch
        elif n <= (2 * epoch * (epoch - 1) + (2 * epoch ** 2)) // 2:
            x = 2 * epoch - 1
            y = (n - 1) % epoch + 1
        else:
            x = 2 * epoch
            y = (n - 1) % epoch + 1
        return (x, y)

    async def get_user_by_coordonates(self, coords: Union[list, Union[list, str]], multi=False) -> Union[list(User), User]:
        with open("database.json", "r") as f:
            db = json.load(f)
            f.close()

        flag_request = rq.get("https://api-flag.fouloscopie.com/flag")
        if multi:
            users = []
        for coord in coords:
            if not any(user["coord"] == coord for user in db.values()):
                user = {}
                cd = self.coord_to_index(tuple(coord))
                i = 0
                for dic in flag_request.json():
                    i += 1
                    if i == cd:
                        user_dict = dic
                        break
                try:
                    user_dict
                except NameError:
                    if multi:
                        users.append(f"{coord} Not Found")
                    else:
                        raise UserErrors.UserNotFound(f"This user could not be found with coordinates {coord}")

                user_request = rq.get(f"https://admin.fouloscopie.com/users/{user_dict['author']}")
                user["username"] = user_request.json()["data"]["last_name"]
                user["id"] = user_dict["author"]
                user["coord"] = list(coord)
                user["iter"] = cd
                user["color"] = int(f"{user_dict['hexColor'].replace('#', '0x')}", 16)
                user["indexInFlag"] = user_dict["indexInFlag"]

                if multi:
                    users.append(User.new_user(self.guild, user))
                else:
                    return User.new_user(self.guild, user)

            else:
                for d in db.values():
                    if d["coord"] == list(coord):
                        user = d
                        break
                try:
                    user
                except NameError:
                    if multi:
                        users.append(f"{coord} Not Found")
                    else:
                        raise UserErrors.UserNotFound(f"This user could not be found with coordinates {coord}")
                if multi:
                    users.append(User(self.guild, user["username"]))
                else:
                    return User(self.guild, user["username"])
        if multi:
            return users
        else:
            raise UserErrors.UserNotFound(f"This user could not be found with coordinates {coord}")

    async def get_user_by_username(self, usernames: Union[str, list]):
        if isinstance(usernames, list):
            users = []
            for username in usernames:
                try:
                    user = User(self.guild, username)
                    users.append(user)
                except UserErrors().UserNotFound:
                    pass

            return users
        elif isinstance(usernames, str):
            return User(self.guild, usernames)

    async def get_users_in_area(self, coord1: list, coord2: list):
        coords = []
        for row in range(coord1[1], coord2[1] + 1):
            for line in range(coord1[0], coord2[0] + 1):
                coords.append([line, row])

        users = await self.get_user_by_coordonates(coords, multi=True)

        return users

    async def get_neighbors(self, coord: list):
        try:
            upper_neighbor = await self.get_user_by_coordonates([coord[0], coord[1] - 1])
        except UserErrors.UserNotFound:
            upper_neighbor = {
                "member_id": "N/A",
                "mention": "N/A",
                "username": "Not Found",
                "id": "N/A",
                "coord": "N/A",
                "iter": "N/A",
                "color": "N/A",
                "indexInFlag": "N/A",
                "Region": "N/A"
            }
        try:
            down_neighbor = await self.get_user_by_coordonates([coord[0], coord[1] + 1])
        except UserErrors.UserNotFound:
            down_neighbor = {
                "member_id": "N/A",
                "mention": "N/A",
                "username": "Not Found",
                "id": "N/A",
                "coord": "N/A",
                "iter": "N/A",
                "color": "N/A",
                "indexInFlag": "N/A",
                "Region": "N/A"
            }
        try:
            left_neighbor = await self.get_user_by_coordonates([coord[0] - 1, coord[1]])
        except UserErrors.UserNotFound:
            left_neighbor = {
                "member_id": "N/A",
                "mention": "N/A",
                "username": "Not Found",
                "id": "N/A",
                "coord": "N/A",
                "iter": "N/A",
                "color": "N/A",
                "indexInFlag": "N/A",
                "Region": "N/A"
            }
        try:
            right_neighbor = await self.get_user_by_coordonates([coord[0] + 1, coord[1]])
        except UserErrors.UserNotFound:
            right_neighbor = {
                "member_id": "N/A",
                "mention": "N/A",
                "username": "Not Found",
                "id": "N/A",
                "coord": "N/A",
                "iter": "N/A",
                "color": "N/A",
                "indexInFlag": "N/A",
                "Region": "N/A"
            }
        return {
            "up": upper_neighbor,
            "down": down_neighbor,
            "left": left_neighbor,
            "right": right_neighbor,
        }
