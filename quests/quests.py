import json
import os

class Quests():
    def __init__(self):
        self.quest_list = []
        self.find_quests()
        self.quest_list.sort()

    def find_quests(self):
        for root, dirs, files, in os.walk('./quests'):
            for file in files:
                if ".json" in file:
                    with open(os.path.join(root, file), 'r') as f:
                        data = json.load(f)
                        self.quest_list.append((data.get("QuestName"), os.path.join(root, file)))

    def get_quests(self):
        return(self.quest_list)

q = Quests()
print(q.get_quests())
