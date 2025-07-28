## TO DO
# add item tracking
# add error handling (file I/O)
# add ability to mark objectives as completed


from quests import quests as q
import json
import os

class PlayerData():
    def __init__(self):
        self.quests = q.Quests()
        self.pdata = self.load_data()

    def load_data(self):
        with open("./pdata/pdata.json", 'r') as f:
            return(json.load(f))

    def get_all_quests(self):
        return(self.quests.get_quests())
    
    def get_completed_quests(self):
        return(self.pdata.get("CompletedQuests"))
    
    def get_active_quests(self):
        return(self.pdata.get("ActiveQuests"))
    
    def get_objectives_on_map(self, map):
        objectives = []
        for quest in self.get_active_quests():
            if map or "any" in self.quests.get_locations(quest):
                quest_objectives = self.quests.get_objectives(quest)
                for obj in quest_objectives:
                    if map or "any" in obj.get("Location"):
                        objectives.append((quest, obj, False)) # parent quest, objective info, bool for if completed or not
        
        return objectives
    
    def update_json(self):
        with open("./pdata/pdata.json", 'w') as f:
            json.dump(self.pdata, f)

    def add_active_quest(self, quest):
        self.pdata['ActiveQuests'].append(quest)
        self.update_json()

    def remove_active_quest(self, quest):
        self.pdata['ActiveQuests'].remove(quest)
        self.update_json()

    def add_completed_quest(self, quest):
        self.pdata['CompletedQuests'].append(quest)
        self.update_json()

    def remove_completed_quest(self, quest):
        self.pdata['CompletedQuests'].remove(quest)
        self.update_json()
