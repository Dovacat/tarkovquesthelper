## TO DO
# add error handling (file I/O)

import json
import os


class Quests:
    def __init__(self):
        self.quest_list = []
        self.find_quests()
        self.quest_list.sort()

    def find_quests(self):
        for (
            root,
            dirs,
            files,
        ) in os.walk("./quests"):
            for file in files:
                if ".json" in file:
                    with open(os.path.join(root, file), "r") as f:
                        data = json.load(f)
                        self.quest_list.append(
                            (data.get("QuestName"), os.path.join(root, file))
                        )

    def get_quests(self):
        q_list = []
        for name, dir in self.quest_list:
            q_list.append(name)

        return q_list

    def get_file_from_quest(self, quest):
        for name, dir in self.quest_list:
            print(f"{name}, {quest}")
            if name == quest:
                print(f"Dir: {dir}")
                return dir

    def get_json_data(self, quest):
        with open(self.get_file_from_quest(quest), "r") as f:
            data = json.load(f)
            return data

    def get_objectives(self, quest):
        data = self.get_json_data(quest)
        return data.get("Objectives")

    def get_locations(self, quest):
        data = self.get_json_data(quest)
        return data.get("Locations")

    def get_num_quests(self):
        return len(self.quest_list)

    def get_num_quests_kappa(self):
        num = 0
        for name, dir in self.quest_list:
            if self.get_json_data(name).get("Kappa"):
                num += 1
