import json
from pydantic import BaseModel
from openai import OpenAI
from src.modules.dnd.models.campaign import Campaign, Act, Chapter, Area, Location, NPC


client = OpenAI()

def generate_campaign():
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Generate a D&D campaign."},
            {
                "role": "user",
                "content": """
                    Overview

                    This campaign is set in a fictional high-fantasy world inspired by D&D, with a twist: elements of a 1984 Miami Synthwave aesthetic subtly blend into the medieval fantasy setting. The tone is slightly humorous but remains grounded to preserve the gravity of the story. Magic and retrofuturistic technology intertwine to create a world of vibrant colors and looming conflict.

                    The Villains: The Wizzards

                    A self-interested organization of powerful magic-users striving to take over the world. The Wizzards are not inherently evil but are driven by pragmatism and ambition. They seek to create order and prosperity primarily for themselves, using their magic, technology, and propaganda to maintain control.

                    Motives and Methods:

                    Control through Fusion of Magic and Technology:Developing a magical AI capable of mass production, which will enhance their control without requiring constant vigilance.

                    Subtlety over Force:Preferring manipulation and propaganda, but resorting to violence, fear, and assassination when needed.

                    Focus on Perception:Hosting festivals, gladiatorial games, and spectacles to maintain the illusion of prosperity and contentment.

                    Strict Internal Monitoring:Constant surveillance of fellow Wizzards to prevent any individual from becoming too powerful.

                    Organizational Structure:

                    The Quorum:A small elite council of the most powerful Wizzards who direct the organization’s actions.

                    The Cabal:The tier of lesser Wizzards below the Quorum, organized into units reporting to higher-ranked members.

                    The Neon Keepers:A mix of combatants and non-combatants serving as henchmen, enforcers, and support staff. They report directly to the Cabal.

                    The Artisan: Master of Crafted Magic

                    A non-Wizzard craftsman who wields magic through his creations rather than innate ability. Known for his intelligence and cunning, the Artisan is the grand designer of the AI magical beings being constructed for the Quorum. His body is partially composed of aggregate stone, metal, gold, gems, and energy, replacing limbs and organs to enhance his capabilities, strength, and dexterity. He commands many of the Neon Keepers as his henchmen and seeks magical artifacts to create increasingly powerful AI beings for the Wizzards.

                    Key Traits:

                    Role: The Artisan is a recurring antagonist and mastermind behind the magical AI creations.

                    Goals: To discover and acquire magical artifacts that will enable him to craft more advanced AI beings.

                    Abilities: Exceptional craftsmanship and manipulation of materials, combining magic and technology. His enhanced body grants him incredible physical and intellectual abilities.

                    Act One: Setting the Stage

                    Introduce the Wizzards' looming influence, their fusion of magic and technology, and their plans for domination. The act consists of two chapters.

                    Chapter One: Neon Shadows

                    Objective:Investigate mysterious disappearances and rumors of manipulation by an enigmatic group.

                    Location:

                    Duskspire City:A bustling port city blending medieval architecture with synthwave neon lighting.

                    The Glittergut Tavern: A seedy gathering spot for rumors and gigs.

                    Skyvault District: Wealthier, heavily patrolled, and home to a glowing tower linked to Wizzard activities.

                    Key NPCs:

                    Lance Hightide: Retired knight-turned-bartender with intel on local disappearances.

                    Cynthia Glowglen: A courier secretly working as a Wizzard informant.

                    Marix "The Shadow" Illuna: A rogue claiming to have escaped a Wizzard facility.

                    Events:

                    Uncover mind-control spells being used on merchants.

                    Discover a hidden Wizzard lab testing magical AI prototypes.

                    Chapter Two: The Party’s Over

                    Objective:Disrupt a grand festival hosted by the Wizzards to expose their propaganda and plans.

                    Location:

                    Starlight Plaza:A massive amphitheater for festivals and gladiatorial games, serving as a propaganda hub.

                    Underplaza Tunnels: Secret passageways beneath the plaza for smuggling equipment and prisoners.

                    Key NPCs:

                    Orin Brightflare: A flamboyant mid-ranking Wizzard overseeing the festival.

                    Gladiax: A cybernetic gladiator who secretly despises the Wizzards.

                    Selena Underveil: A spy posing as a festival performer.

                    Events:

                    Infiltrate the festival to gather intel.

                    Uncover plans for citywide deployment of magical AI enforcers.

                    Confront Orin Brightflare and reveal the Wizzards’ larger ambitions.

                    Race against the Artisan to recover a magical neon artifact critical to his AI experiments.
                """
             },
        ],
        response_format=Campaign,
    )

    campaign = completion.choices[0].message.parsed
    return campaign

def save_campaign_to_json(campaign, filename):
    with open(filename, 'w') as f:
        json.dump(campaign.dict(), f, indent=4)

def main():
    campaign = generate_campaign()
    save_campaign_to_json(campaign, 'campaign.json')
    print("Campaign saved to campaign.json")

if __name__ == "__main__":
    main()
