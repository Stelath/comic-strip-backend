from openai import OpenAI
from story_components.character import Character, CharacterMoment
from story_components.frame import Frame
import Levenshtein

import copy
import random
import logging
from multiprocessing import Pool

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

        self.logging = logging.getLogger(__name__)
        self.logging.setLevel(logging.DEBUG)
        self.logging.addHandler(logging.StreamHandler())

        self.logging.info("Initializing OpenAI")

        self.openai = OpenAI(api_key=self.key)
        self.logging.info("Getting outline...")
        self.outline = self.gen_outline()

        self.logging.info("Getting title...")
        self.title = self.gen_title()

        self.logging.info("Getting characters...")

        done = False
        while not done:
            try:
                self.characters = self.gen_characters()
                done = True
            except ValueError as e:
                self.logging.error(e)
                self.logging.error("Retrying to get characters...")

        self.logging.info(f"Got {len(self.characters)} characters")

        self.logging.info("Getting frames...")
        self.frames = self.gen_frames()
        self.logging.info(f"Got {len(self.frames)} frames")

        self.logging.info("Getting diffusion prompts...")
        self.frame_diffusion_prompts = self.get_diffusion_prompts_for_frames()
        self.logging.info(f"Got {len(self.frame_diffusion_prompts)} diffusion prompts")

    def ask_chat_gpt(self, messages):
        """
        Given a list of messages, ask the ChatGPT for a response
        :param messages: List of messages, each with a role and content
        :return: The response from the ChatGPT
        """
        response = self.openai.chat.completions.create(
            model="gpt-4-turbo-preview",
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

    def gen_title(self):
        # Given the outline, generate a title
        with open('story_generator/prompts/gen_title_prompt.txt', 'r') as file:
            prompt = file.read()

        prompt = prompt.replace("$OUTLINE", self.outline)
        messages = [
            {"role": "system", "content": "You are a good title maker for comic book stories"},
            {"role": "user", "content": prompt}
        ]
        output = self.ask_chat_gpt(messages)
        with open("title_output.txt", "w") as file:
            file.write(output)

        for line in output.split("\n"):
            if "Title:" in line:
                return line[7:]

    def gen_characters(self):
        """
        Given the outline, generate characters

        Returns: list of Character objects
        """

        num_characters = random.randint(2, 4)

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
                elif "Gender:" in line:
                    physical_description = line[8:] + " " + physical_description
                elif "Race:" in line:
                    physical_description = line[6:] + " " + physical_description

            if name and physical_description and personality:
                characters.append(Character(name, physical_description, personality))
            else:
                print("Error: failed to parse character\n",
                      "Info:", character_text_section)

        if len(characters) < 2:
            raise ValueError("Error: failed to generate enough characters")

        return characters

    def gen_frames(self):
        """
        Generate frames for the comic book

        Provides ChatGPT with the general outline and characters, and asks for 4 to 6 frames for the comic book
        """
        num_frames = random.randint(10, 20)
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

            if not scene_description:
                print("Error: failed to parse scene description from the following lines\n"
                      , frame_text_section)
                continue

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

    @staticmethod
    def generate_prompt(frame):
        """
        Generate a prompt for the diffusion model given a frame
        Meant to be used with multiprocessing
        :param frame: The frame to generate a prompt for
        :param openai: The OpenAI object to send the prompt to
        :return: The prompt for the diffusion model
        """
        to_prompt = open("story_generator/prompts/frame_to_diffusion_prompt.txt", "r").read()
        to_prompt = to_prompt.replace("$SCENE_DESCRIPTION", frame.scene_description)

        # Adding character information to the prompt
        for i, character_moment in enumerate(frame.character_moments):
            to_prompt += "\nCharacter " + str(i) + ":\n"
            to_prompt += character_moment.no_dialogue_description() + "\n"

        messages = [
            {"role": "system", "content": "You are a good diffusion model prompter engineer that is concise\n"
                                          "Always use physical descriptions including gender and race\n"},
            {"role": "user", "content": to_prompt}
        ]
        with open('story_generator/chatgpt_key.txt', 'r') as file:
            key = file.read().replace('\n', '')
        print("Sending prompt to OpenAI")
        response = OpenAI(api_key=key).chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages
        )
        print("Got response from OpenAI")
        return response.choices[0].message.content

    def get_diffusion_prompts_for_frames(self):
        """
        Get the diffusion prompts for each frame
        :return: A list of prompts for each frame
        """
        with Pool() as p:
            prompts = p.map(self.generate_prompt, self.frames)
        return prompts

    def __str__(self):
        out = ""
        out += "Title: " + self.title + "\n"
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

    def to_dict(self):
        out = {"title": self.title,
               "outline": self.outline,
               "characters": [character.to_dict() for character in self.characters],
               "frames": [frame.to_dict() for frame in self.frames]}
        return out
