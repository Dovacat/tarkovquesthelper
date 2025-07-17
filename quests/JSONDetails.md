# Main Body


### QuestName
#### Type: 
String
#### Purpose: 
Lists the name of the quest

### Location
#### Type: 
String array
#### Purpose: 
Lists the names of the maps that the quest takes place on in string form, "any" for all maps, "none" for quest that does not require going to a map (ex, hand over x rubles)

### Field: Kappa
#### Type: 
Boolean
#### Purpose: 
Determines whether or not a quest is required for Kappa container

### LeadsTo
#### Type: 
String array
#### Purpose: 
Containts a list of quests that this quest unlocks

### Alternatives
#### Type: 
String Array
#### Purpose: 
Contains a list of alternative completions for this quest


## Requirements


### Level
#### Type: 
Integer
#### Purpose: 
Determines what the required player level for accepting the quest is

### Quests
#### Type: 
String array
#### Purpose: 
Contains a list of quests that must be completed to unlock this quest


## Objectives

#### Note: More than one sub objective can be present

### Required
#### Type: 
Boolean
#### Purpose: 
Determines whether or not an objective is required in order to complete the quest

### Location
#### Type: 
String
#### Purpose: 
Determines which map this objective takes place on

### LocationBoxTopLeft
#### Type: 
Integer array
#### Purpose: 
Determines the top left coordinate (x,y) of the map marking box that will be drawn for this objective. 0,0 for whole map

### LocationBoxBottomRight
#### Type:
Integer array
#### Purpose: 
Determines the bottom right coordinate (x,y) of the map marking box that will be drawn for this objective. 0,0 for whole map

### Type
#### Type: 
String
#### Purpose:
Type of objective this is. 

Elimination if the player is required to kill a target

Fetch if the player is required to gather a quest specific item from the map

Gather if the player is required to hand over specific regular loot

Scout if the player is required to go to a specific area

Stash if the player must place an item on the map (includes marker quests)

Skill if the player is required to be a certain level in a skill to complete the quest

### Time
#### Type:
Integer Array
#### Purpose:
If there is a requirement that a quest take place during a specific time window, this will contain the start and ending times for that window (24hr time)

### Target
#### Type:
String
#### Purpose:
Gives the target of the quest, be it the name of the item that is to be gathered or the enemy to be killed

### Amount
#### Type:
Integer
#### Purpose:
Determines the number of targets in the objective


## Rewards

### Note: More than one sub reward can be present

### Name
#### Type:
String
#### Purpose:
Contains the name of the reward, be it a specific item or something like XP

### Amount
#### Type:
Integer
#### Purpose:
Contains the amount of the reward that will be given
