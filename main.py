import os
from abc import ABC, abstractmethod
from datetime import datetime

from text_file_loader import TextFileLoader


class Helper:
    @classmethod
    def is_valid_number(cls, string):
        if string.isdigit():
            return True
        try:
            float(string)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_now():
        return datetime.now()

    @staticmethod
    def output_filename():
        if not os.path.isdir("output"):
            os.mkdir("output")

        now = Helper.get_now()
        return f"output/drop{now.strftime('%m%d%Y%H%M%S')}.sql"


class ItemReader(ABC):
    def __init__(self, filename):
        try:
            with open(filename, "r") as file_buffer:
                self._file_content = file_buffer.readlines()
        except FileNotFoundError:
            print(f"Unable to load {filename}")
        self._data = []

    @abstractmethod
    def valid_data(self, data):
        pass

    @abstractmethod
    def process_data(self):
        pass

    def print_query_to_file(self, file_buffer):
        for item in self._data:
            file_buffer.write(f"{item}")
        print(f"Converted {len(self._data)} item(s) from {self.__class__.__name__}")


class CommonDropItemReader(ItemReader):
    class CommonDropItem:
        mob_rank = 0
        level_start = 0
        level_end = 0
        item_vnum = 0
        count = 0
        chance = 0

        def __init__(self, data, rank):
            self.level_start = data[1]
            self.level_end = data[2]
            self.chance = data[3]
            self.item_vnum = data[4]
            self.count = data[5]
            self.mob_rank = rank

        def __str__(self):
            return f"INSERT INTO common_drop_item (mob_rank, level_start, level_end, item_vnum, count, chance) " \
                   f"VALUES ('{self.mob_rank}', {self.level_start}, {self.level_end}, " \
                   f"{self.item_vnum}, {self.count}, {self.chance});\n"

    def __init__(self, filename):
        super().__init__(filename)

    def valid_data(self, data):
        if len(data) < 6:
            return False

        if all([Helper.is_valid_number(x) for x in data[1:]]):
            return True
        return False

    def process_data(self):
        temp_ranks = self._file_content[0].split()
        ranks = {
            rank: self._file_content[0].split("\t").index(rank) for rank in temp_ranks
        }
        for key, rank in ranks.items():
            for line in self._file_content:
                rank_data = [t.strip() for t in line.split("\t")[rank:rank + 6]]
                if self.valid_data(rank_data):
                    self._data.append(self.CommonDropItem(rank_data, key))


class EtcDropItemReader(ItemReader):
    class EtcDropItem:
        item_vnum = 0
        count = 0
        chance = 0

        def __init__(self, data):
            self.item_vnum = data[0]
            self.chance = data[1]
            self.count = data[2]

        def __str__(self):
            return f"INSERT INTO etc_drop_item (item_vnum, count, chance) " \
                   f"VALUES ({self.item_vnum}, {self.count}, {self.chance});\n"

    def __init__(self, filename):
        super().__init__(filename)

    def valid_data(self, data):
        return all([Helper.is_valid_number(x) for x in data]) and len(data) > 1

    def process_data(self):
        for line in self._file_content:
            data = [x.strip() for x in line.split("\t")]
            if self.valid_data(data):
                if len(data) < 3:
                    data.append(str(1.0))
                self._data.append(self.EtcDropItem(data))


class MobDropItemReader(ItemReader):
    class MobDropItemGroup:
        type = 0
        mob_vnum = 0
        kill_drop = 0
        level_limit = 0

        def __init__(self, data):
            self.type = data[0]
            self.mob_vnum = data[1]
            self.kill_drop = data[2]
            self.level_limit = data[3]

        def __str__(self):
            return f"INSERT INTO mob_drop_item_group (vnum, type, kill_drop, level_limit)" \
                   f" VALUES ({self.mob_vnum}, '{self.type}', {self.kill_drop}, {self.level_limit});\n"

    class MobDropItemKill:
        mob_vnum = 0
        vnum = 0
        count = 0
        chance = 0
        rare_pct = 0

        def __init__(self, data):
            self.mob_vnum = data[0]
            self.vnum = data[1]
            self.count = data[2]
            self.chance = data[3]
            self.rare_pct = data[4]

        def __str__(self):
            return f"INSERT INTO mob_drop_item_kill (mob_vnum, vnum, count, chance, rare_pct)" \
                   f" VALUES ({self.mob_vnum}, {self.vnum}, {self.count}, {self.chance}, {self.rare_pct});\n"

    class MobDropItemLimit:
        mob_vnum = 0
        vnum = 0
        count = 0
        chance = 0

        def __init__(self, data):
            self.mob_vnum = data[0]
            self.vnum = data[1]
            self.count = data[2]
            self.chance = data[3]

        def __str__(self):
            return f"INSERT INTO mob_drop_item_limit (mob_vnum, vnum, count, chance)" \
                   f" VALUES ({self.mob_vnum}, {self.vnum}, {self.count}, {self.chance});\n"

    class MobDropItemDrop:
        mob_vnum = 0
        vnum = 0
        count = 0
        chance = 0

        def __init__(self, data):
            self.mob_vnum = data[0]
            self.vnum = data[1]
            self.count = data[2]
            self.chance = data[3]

        def __str__(self):
            return f"INSERT INTO mob_drop_item_drop (mob_vnum, vnum, count, chance)" \
                   f" VALUES ({self.mob_vnum}, {self.vnum}, {self.count}, {self.chance});\n"

    def __init__(self, filename):
        super().__init__(filename)
        self._file_content = TextFileLoader(filename).get_all_groups()

    def valid_data(self, data):
        match data[0]:
            case "DROP" | "LIMIT":
                return all([Helper.is_valid_number(x) for x in data[1:]]) and len(data) == 4
            case "KILL":
                return all([Helper.is_valid_number(x) for x in data[1:]]) and len(data) == 5

    def process_data(self):
        for items in self._file_content:
            drop_type = items["data"].get("type")[0].upper()
            mob_vnum = items["data"].get("mob")[0]
            kill_drop = 0
            level_limit = 0
            if drop_type == "KILL":
                kill_drop = items["data"].get("kill_drop")[0]
            elif drop_type == "LIMIT":
                level_limit = items["data"].get("level_limit")[0]
            data = [drop_type, mob_vnum, kill_drop, level_limit]
            self._data.append(self.MobDropItemGroup(data))

            for i in range(255):
                drop = items["data"].get(str(i + 1))
                if not drop:
                    break
                if self.valid_data([drop_type, *drop]):
                    class_dict = {
                        "KILL": self.MobDropItemKill,
                        "LIMIT": self.MobDropItemLimit,
                        "DROP": self.MobDropItemDrop
                    }

                    if class_dict.get(drop_type):
                        obj = class_dict[drop_type]([mob_vnum, *drop])
                        self._data.append(obj)


if __name__ == '__main__':
    readers = [
        CommonDropItemReader("input/common_drop_item.txt"), EtcDropItemReader("input/etc_drop_item.txt"),
        MobDropItemReader("input/mob_drop_item.txt")
    ]

    filename = Helper.output_filename()
    with open(filename, "a") as f:
        now = Helper.get_now()
        f.write(f"-- Script generated at {now.strftime('%B %d, %Y %H:%M:%S')}\n")
        for reader in readers:
            reader.process_data()
            reader.print_query_to_file(f)

    print(f"Drop data saved in {filename}")
    os.system("pause")
