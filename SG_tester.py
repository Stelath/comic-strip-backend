from story_generator.story_prompter import ComicBookPrompter

"""Testing"""
user_prompt = "A super hero and their sidekick fight each other"
story = ComicBookPrompter(user_prompt)

# Write story to file
with open("story_output.txt", "w") as file:
    file.write(story.__str__())