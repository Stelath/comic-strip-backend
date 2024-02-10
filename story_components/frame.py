from .character import CharacterMoment


class Frame:
    def __init__(self, scene_description, characters: list[CharacterMoment]):
        self.scene_description = scene_description
        self.characters = characters

    def __str__(self):
        out = f"Scene: {self.scene_description}\n"
        out += "Characters:\n"
        for character in self.characters:
            out += character.__str__() + "\n"
        return out
