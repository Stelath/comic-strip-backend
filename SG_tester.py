from story_generator.story_prompter import ComicBookPrompter

"""Testing"""
user_prompt = "A superhero comic book about a hero who can fly"
story = ComicBookPrompter(user_prompt)

# Write story to file
with open("story_output.txt", "w") as file:
    file.write(story.__str__())