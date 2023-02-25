class TextFileLoader:
    def __init__(self, filename):
        try:
            with open(filename, "r") as f:
                self._file_content = f.readlines()
        except FileNotFoundError:
            print(f"Unable to load {filename}")

        self._group_dict = {}
        self._data_list = []

        self.__process_file()

    def __process_file(self):
        group_name = ""
        group_data = {}

        for line in self._file_content:
            line = [x.strip() for x in line.split()]

            if not len(line):
                continue

            match line[0]:
                case "Group":
                    if group_name and len(group_data):
                        self._group_dict.update({group_name: group_data})
                        self._data_list.append({"name": group_name, "data": group_data})

                    group_name = line[1]
                    group_data = {}

                case "{" | "}":
                    continue
                case _:
                    group_data.update({
                        "".join(x.lower() for x in line[0]): line[1:]
                    })

    def get_group(self, key):
        return self._group_dict.get(key, None)

    def get_all_groups(self):
        return self._data_list
