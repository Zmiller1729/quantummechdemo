from numpy import roll
from pydantic import BaseModel
from typing import List
from openai import OpenAI
import random
import json
import os
import argparse

client = OpenAI()
LOG_FILE = "scenario.log"

class Outcome(BaseModel):
    description: str
    weight: int

class Outcomes(BaseModel):
    friendly: Outcome
    hostile: Outcome
    neutral: Outcome
    threaten: Outcome

class DialogLine(BaseModel):
    speaker: str
    text: str

class Scenario(BaseModel):
    backstory: str
    gullability: int
    aggression: int
    intelligence: int
    suspicion: int
    superstition: int
    perception: int
    dialog_history: List[DialogLine]
    outcomes: Outcomes

class OutcomeResponse(BaseModel):
    dialog: str
    outcomes: Outcomes

def log_event(event: str):
    with open(LOG_FILE, 'a') as f:
        f.write(event + '\n')

def print_and_save_new_dialog_line(scenario: Scenario, speaker: str, text: str):
    log_event(f"{speaker}: {text}")
    print(f"{speaker}: {text}")
    scenario.dialog_history.append(DialogLine(speaker=speaker, text=text))

def roll_dice():
    roll = random.randint(1, 100)
    log_event(f"Rolling a 1-100 dice... You rolled a {roll}")
    print("Rolling a 1-100 dice...")
    print("You rolled a ", roll)
    return roll

def process_dialog_with_ai(scenario: Scenario, roll: int, debug: bool):
    prompt = f"""
    Here is the backstory: {scenario.backstory}

    Here is the dialog history: {scenario.dialog_history}

    Here are your character attributes on a scale from 0-10:

    gullability: {scenario.gullability}
    aggression: {scenario.aggression}
    intelligence: {scenario.intelligence}
    suspicion: {scenario.suspicion}
    superstition: {scenario.superstition}
    perception: {scenario.perception}

    Your attributes guide your character's responses to the user's dialog. These attributes will not change
    nor will they be visible to the user.

    The user rolled a {roll} on a 1-100 dice roll.

    You are the "guard" in this dialog history.

    Here are the outcomes you can choose from:
    friendly: {scenario.outcomes.friendly.description},
    hostile: {scenario.outcomes.hostile.description},
    neutral: {scenario.outcomes.neutral.description},
    threaten: {scenario.outcomes.threaten.description},

    Each outcome has a weight associated with it. The weights all started at 0.
    You can increase the weight of an outcome by selecting it.
    The weight represents your inclination towards that outcome.
    The weights are scaled from 0 to 0. Once an outcome reaches 10 or more, the conversation will end
    and the outcome will be chosen.
    You may not give more than one outcome a weight of 10 or more.
    If no outcome has a weight of 10 or more, the conversation will continue until you choose an outcome.
    Be more inclined to choose an outcome if the conversation goes back and forth too many times.
    We're looking for a natural but short to medium length conversation.

    Please read through the backstory and the dialog history and consider a response to give.
    The response is what you will be saying to the user. Please consider the user's roll when evaluating
    how effective they are at any attempts to fool, intimidate, or persuade, etc you.
    """

    if debug:
        print("Prompt being sent to OpenAI:")
        print(prompt)

    log_event(f"Prompt being sent to OpenAI:\n{prompt}")

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": scenario.backstory},
            {"role": "user", "content": prompt},
        ],
        response_format=OutcomeResponse,
    )

    if completion.choices and completion.choices[0].message.parsed:
        outcome_response = completion.choices[0].message.parsed
        log_event(f"Outcome values received from OpenAI:\n{outcome_response}")
        if debug:
            print("Outcome values received from OpenAI:")
            for outcome_name, outcome in outcome_response.outcomes.dict().items():
                print(f"{outcome_name}: {outcome['weight']}")
        return outcome_response
    return None

def get_user_response(scenario: Scenario):
    response = input("Your response: ")
    print_and_save_new_dialog_line(scenario, "You", response)

def start_game(debug: bool):
    # Clear the log file at the start of a new game
    with open(LOG_FILE, 'w') as f:
        f.write("")

    scenario = Scenario(
        backstory="You are standing at the gate of a gladiatorial arena. The guard is tasked with not letting any mortal pass.",
        gullability=6,
        aggression=7,
        intelligence=4,
        suspicion=4,
        superstition=7,
        perception=3,
        dialog_history=[],
        outcomes=Outcomes(
            friendly=Outcome(description="The guard smiles and lets you pass.", weight=0),
            hostile=Outcome(description="The guard draws his sword and attacks you.", weight=0),
            neutral=Outcome(description="The guard looks at you suspiciously but does nothing.", weight=0),
            threaten=Outcome(description="The guard lets you pass but sounds the alarm as soon as you do.", weight=0),
        )
    )

    print("Welcome to the Text Adventure Game!")
    log_event("Welcome to the Text Adventure Game!")

    print_and_save_new_dialog_line(scenario, "Guard", "Halt! Who goes there? I'm charged with letting no mortal pass.")

    get_user_response(scenario)

    while True:
        roll = roll_dice()
        outcome_response = process_dialog_with_ai(scenario, roll, debug)
        if outcome_response:
            print_and_save_new_dialog_line(scenario, "Guard", outcome_response.dialog)
            scenario.outcomes = outcome_response.outcomes
            for outcome_name, outcome in outcome_response.outcomes.dict().items():
                log_event(f"Outcome {outcome_name}: {outcome['description']} with weight {outcome['weight']}")
            selected_outcomes = list[str]()
            log_event(f"Selected outcomes: {selected_outcomes}")

            if scenario.outcomes.friendly.weight >= 10:
                selected_outcomes.append(scenario.outcomes.friendly.description)
            if scenario.outcomes.hostile.weight >= 10:
                selected_outcomes.append(scenario.outcomes.hostile.description)
            if scenario.outcomes.neutral.weight >= 10:
                selected_outcomes.append(scenario.outcomes.neutral.description)
            if scenario.outcomes.threaten.weight >= 10:
                selected_outcomes.append(scenario.outcomes.threaten.description)

            if selected_outcomes:
                chosen_outcome = random.choice(selected_outcomes)
                log_event(f"Chosen outcome: {chosen_outcome}")
                print(chosen_outcome)
                break
            get_user_response(scenario)
        else:
            print("No valid response from AI.")
            log_event("No valid response from AI.")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text Adventure Game")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    start_game(args.debug)
