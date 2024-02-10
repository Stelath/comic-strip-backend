from openai import OpenAI
from story_components.character import Character, CharacterMoment
from story_components.frame import Frame
import Levenshtein

import copy
import random


class ComicBookPrompter:
    def __init__(self, user_prompt):
        self.user_prompt = user_prompt

        try:
            # Load api key from key.txt
            with open('story_generator/chatgpt_key.txt', 'r') as file:
                self.key = file.read().replace('\n', '')
        except FileNotFoundError:
            print("Error: chatgpt_key.txt not found")
            exit(1)

        self.openai = OpenAI(api_key=self.key)

        self.outline = self.gen_outline()
        self.characters = self.gen_characters()
        self.frames = self.gen_frames()
        self.frame_diffusion_prompts = self.get_diffusion_prompts_for_frames()

    def ask_chat_gpt(self, messages):
        """
        Given a list of messages, ask the ChatGPT for a response
        :param messages: List of messages, each with a role and content
        :return: The response from the ChatGPT
        """
        response = self.openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content

    def gen_outline(self):
        # Load get outline prompt from file
        with open('story_generator/prompts/get_outline_prompt.txt', 'r') as file:
            prompt = file.read()

        # Replace the $USER-PROMPT with the user prompt
        prompt = prompt.replace("$USER-PROMPT", self.user_prompt)

        messages = [
            {"role": "system", "content": "You are a story writer"},
            {"role": "user", "content": prompt}
        ]
        output = self.ask_chat_gpt(messages)
        with open("outline_output.txt", "w") as file:
            file.write(output)
        return output

    def gen_characters(self):
        """
        Given the outline, generate characters

        Returns: list of Character objects
        """

        num_characters = random.randint(1, 4)

        # Load get characters prompt from file
        with open('story_generator/prompts/get_characters_prompt.txt', 'r') as file:
            prompt = file.read()

        prompt = prompt.replace("$OUTLINE", self.outline)
        prompt = prompt.replace("$NUM_CHARACTERS", str(num_characters))

        messages = [
            {"role": "system", "content": "You are a good character maker"},
            {"role": "user", "content": prompt}
        ]

        output = self.ask_chat_gpt(messages)
        with open("characters_output.txt", "w") as file:
            file.write(output)

        """
        Parsing the output to get a list of individual characters
        """

        characters = []
        character_text_sections = output.split("<start>")[1:]
        for character_text_section in character_text_sections:
            character_text_section = character_text_section.split("\n")

            name = None
            physical_description = None
            personality = None

            for i, line in enumerate(character_text_section):
                if "Name:" in line:
                    name = line[6:]
                elif "Physical:" in line:
                    physical_description = line[10:]
                elif "Personality:" in line:
                    personality = line[13:]

            if name and physical_description and personality:
                characters.append(Character(name, physical_description, personality))
            else:
                print("Error: failed to parse character\n",
                      "Info:", character_text_section)

        return characters

    def gen_frames(self):
        """
        Generate frames for the comic book

        Provides ChatGPT with the general outline and characters, and asks for 4 to 6 frames for the comic book
        """
        num_frames = random.randint(4, 6)
        prompt = None
        with open('story_generator/prompts/get_frames_prompt.txt', 'r') as file:
            prompt = file.read()

        prompt = prompt.replace("$FRAME_COUNT", str(num_frames))
        prompt = prompt.replace("$OUTLINE", self.outline)

        # Building a string which holds the info of all characters
        characters_info = ""
        for character in self.characters:
            characters_info += character.__str__() + "\n"

        prompt = prompt.replace("$CHARACTER_DESCRIPTIONS", characters_info)

        messages = [
            {"role": "system", "content": "You are a good story teller"},
            {"role": "user", "content": prompt}
        ]

        output = self.ask_chat_gpt(messages)
        print("\n\nOutput: \n\n", output)

        with open("frames_output.txt", "w") as file:
            file.write(output)

        frames = []
        frame_text_sections = output.split("<start>")[1:]
        for frame_text_section in frame_text_sections:
            frame_text_section_lines = frame_text_section.split("\n")

            scene_description = None

            for i, line in enumerate(frame_text_section_lines):
                if "Scene:" in line:
                    scene_description = line[6:]

            # Reading in each character moment
            character_moments = []
            character_text_sections = frame_text_section.split("<character>")[1:]
            for character_text_section in character_text_sections:
                character_text_section_lines = character_text_section.split("\n")
                name = None
                action = None
                dialogue = None
                character = None
                for i, line in enumerate(character_text_section_lines):
                    if "Name:" in line:
                        # Use the name to find the character that is most similar
                        name = line[6:]
                        character = self.get_relevant_character(name)
                    elif "Action:" in line:
                        action = line[8:]
                    elif "Dialogue:" in line:
                        # Find the first quotation mark on this line and capture everything after it, including the quotation mark
                        dialogue = line[line.find("\""):]

                if not (name and action and dialogue and character):
                    print("Error: failed to parse character moment\n",
                          "Info:", character_text_section)
                    continue
                else:
                    character_moments.append(CharacterMoment(character, action, dialogue))
            frames.append(Frame(scene_description, copy.deepcopy(character_moments)))
        return frames

    def get_relevant_character(self, name):
        """
        Given a name, find the most relevant character from the list of characters
        :param name: The name of the character
        :return: The most relevant character from the list of characters
        """
        best_character = None
        best_similarity = 0
        for character in self.characters:
            similarity = Levenshtein.ratio(name, character.name)
            if similarity > best_similarity:
                best_similarity = similarity
                best_character = character

        # If the best similarity is below a threshold, return None
        if best_similarity < 0.5:
            # Print a warning in red to the console
            print("\033[91mWarning: No relevant character found for name: " + name + "\nBest similarity: " + str(
                best_similarity) + "\nBest character: " + best_character.__str__() + "\033[0m")
            return None

        return best_character

    def get_diffusion_prompts_for_frames(self):
        """
        Get the diffusion prompts for each frame
        :return: A list of prompts for each frame
        """
        prompts = []
        for frame in self.frames:
            to_prompt = open("story_generator/prompts/frame_to_diffusion_prompt.txt", "r").read()
            to_prompt = to_prompt.replace("$SCENE_DESCRIPTION", frame.scene_description)

            # Adding character information to the prompt
            for i, character_moment in enumerate(frame.characters):
                to_prompt += "\nCharacter " + str(i) + ":\n"
                to_prompt += character_moment.no_dialogue_description() + "\n"

            messages = [
                {"role": "system", "content": "You are a good diffusion model prompter engineer that is concise\n"
                                              "Always use physical descriptions including gender\n"},
                {"role": "user", "content": to_prompt}
            ]
            output = self.ask_chat_gpt(messages)
            prompts.append(output)
        return prompts

    def __str__(self):
        out = ""
        out += "Outline: " + self.outline + "\n"
        out += "\nCharacters: \n"
        for character in self.characters:
            out += character.__str__() + "\n"
        out += "\nFrames: \n"
        for frame in self.frames:
            out += frame.__str__() + "\n"

        out += "\nDiffusion Text: \n"
        for i, frame in enumerate(self.frames):
            out += "Frame " + str(i) + ":\n"
            out += self.frame_diffusion_prompts[i] + "\n"

        return out



