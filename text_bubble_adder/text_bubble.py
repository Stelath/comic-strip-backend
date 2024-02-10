from PIL import Image, ImageDraw, ImageFont
from .clipseg import get_location
from story_components.character import CharacterMoment, Character
from story_components.frame import Frame
import math

MAX_TEXT_WIDTH = 200

font_size = 30
font = ImageFont.truetype("text_bubble_adder/BackIssuesBB_ital.otf", font_size)
sample_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz     "
bbox = font.getbbox(sample_text)
CHAR_WIDTH = (bbox[2] - bbox[0]) / len(sample_text)
MAX_HEIGHT = 40


def pick_relative_location(image: Image, head_location, t_width, t_height):
    """
    Picks a location relative to the head location
    If the head is on the left side of the image, the text bubble will be on the right side
    If the head is on the right side of the image, the text bubble will be on the left side
    Ensures that there is enough room for the text bubble to fit without going off the image
    :param image: PIL Image
    :param head_location: A tuple of (x, y) coordinates
    :return: A tuple of (x, y) coordinates to define the top left corner of the text bubble
    """

    # Get the size of the image
    image_size = image.size
    image_width = image_size[0]
    image_height = image_size[1]

    # Get the head location
    head_x = head_location[0]
    head_y = head_location[1]

    # If the head is on the left side of the image, the text bubble will be on the right side
    if head_x < image_width / 2:
        x = head_x + 60
    # If the head is on the right side of the image, the text bubble will be on the left side
    else:
        x = head_x - 60 - t_width

    # Placing the bubble above the head
    # If the bubble would go off the top of the image, place it as high as possible
    y = head_y - 60 - t_height
    if y < MAX_HEIGHT:
        y = 0

    return x, y


def calculate_text_size(text: str, font):
    lines = text.split("\n")
    longest_line = max(lines, key=len)
    bbox = font.getbbox(longest_line)
    single_line_height = bbox[3] - bbox[1]
    return bbox[2] - bbox[0], (single_line_height + single_line_height / 3 + 2) * len(lines)


def wrap_text(text: str, max_width=MAX_TEXT_WIDTH):
    """
    Wraps text to a certain width
    :param text: The text to be wrapped (i.e. adding newlines)
    :param max_width: The maximum width of the text in pixels
    :return: The same text with newlines added to wrap the text
    """
    # Finds a space and replaces it with a newline character
    # Tries to keep each line to a length of x characters
    # Searches for the nearest space to the xth character without going over
    l = 0
    best_space = None
    temp_text = ""
    for i, c in enumerate(text):
        if c != "\n":
            l += 1
            temp_text += text[i]
        if c == "\n":
            l = 0
        width_of_temp_text = font.getbbox(temp_text)[2] - font.getbbox(temp_text)[0]
        if width_of_temp_text > max_width:
            if best_space:
                text = text[:best_space] + "\n" + text[best_space + 1:]
                l = i - best_space
                best_space = None
                temp_text = ""
            else:
                text = text[:i] + "\n" + text[i + 1:]
                l = 0
                temp_text = ""
        elif c == " ":
            best_space = i
    return text


def find_head_edge(image: Image, head_location, logits):
    """
    Finds the edge of the head
    :param image: PIL Image
    :param head_location: A tuple of (x, y) coordinates
    :param logits: The logits from the CLIPSeg model
    :return: A tuple of (x, y) coordinates
    """
    # Get the size of the image
    image_size = image.size
    image_width = image_size[0]
    image_height = image_size[1]

    # Get the head location
    head_x = head_location[0]
    head_y = head_location[1]

    head_logit = logits[int(head_y)][int(head_x)]
    if head_x < image_width / 2:
        direction = 1
    else:
        direction = -1

    # Find the edge of the head
    check_x = head_x
    check_y = head_y
    while 0 <= check_x < image_width and 0 <= check_y < image_height:
        check_logit = logits[int(check_y)][int(check_x)]
        if check_logit < head_logit - abs(head_logit * 0.1):
            break
        check_x += direction * 2
        check_y -= 0.1

    return check_x, check_y


class TextBubble:
    def __init__(self, loc, width, height, point_to_loc, text, head_loc):
        """
        Holds all the values associated with a text bubble
        :param loc: The top left corner of the ellipse (x,y)
        :param width: How wide the ellipse is
        :param height: How tall the ellipse is
        :param point_to_loc: The location that the triangle points to (x,y)
        :param text: The text to be displayed in the bubble
        """

        self.head_loc = head_loc
        self.loc = loc
        self.width = width
        self.height = height
        self.point_to_loc = point_to_loc  # Head edge
        self.text = text

    def get_off_of_point_to_loc(self):
        """
        If point to loc is within the bubble or near being within the bubble, move the bubble away from it
        """
        pad = 30

        while self.loc[1] - pad < self.point_to_loc[1] < self.loc[1] + self.height + pad:
            angle = math.atan2(self.point_to_loc[1] - self.loc[1], self.point_to_loc[0] - self.loc[0])
            self.loc = (self.loc[0] - math.cos(angle) * 10, self.loc[1] - 40 * math.sin(angle))
            if math.sin(angle) == 0:
                self.loc = (self.loc[0], self.loc[1] + 40)


def add_text_bubbles(image: Image, frame):
    """
    Adds text bubbles to an image
    :param image: PIL Image that the text bubbles will be added to
    :param character_moments: A list of CharacterMoments in the frame
    :return: A PIL Image with text bubbles
    """

    character_moments = frame.character_moments

    """
    Getting a bubble for each character in the frame
    """

    print(f"adding text bubbles to {len(character_moments)} characters)")

    text_bubbles = []
    for character_moment in character_moments:
        physical_description = character_moment.physical_description
        dialogue = character_moment.dialogue

        print("Adding text bubble for", physical_description, "with dialogue", dialogue)

        # Wrap the text
        dialogue = wrap_text(dialogue, 200)
        text_width, text_height = calculate_text_size(dialogue, font)

        bubble_width = text_width * 1.25 + font_size * 2
        bubble_height = text_height * 1.25 + font_size * 2

        vals = get_location(image, [physical_description])
        head_location = (vals[0], vals[1])
        logits = vals[2]

        head_edge = find_head_edge(image, head_location, logits)
        bubble_top_left = pick_relative_location(image, head_location, bubble_width, bubble_height)

        # Moving the bubble up or down from the head_edge if they have a similar y value
        if abs(bubble_top_left[1] - head_edge[1]) < 10:
            bubble_top_left = (bubble_top_left[0], head_edge[1] - bubble_height - 20)

        # Checking if the bubble is off the left or right side of the image
        if bubble_top_left[0] < 0:
            bubble_top_left = (0, bubble_top_left[1])
        if bubble_top_left[0] + bubble_width > image.size[0]:
            bubble_top_left = (image.size[0] - bubble_width, bubble_top_left[1])

        text_bubbles.append(
            TextBubble(bubble_top_left, bubble_width, bubble_height, head_edge, dialogue, head_location))

    """
    Deconflicting bubbles that may overlap or cross each other with their triangles
    """
    for i in range(len(text_bubbles)):
        for j in range(i + 1, len(text_bubbles)):
            if text_bubbles[i].loc[0] < text_bubbles[j].loc[0] + text_bubbles[j].width and \
                    text_bubbles[i].loc[0] + text_bubbles[i].width > text_bubbles[j].loc[0] and \
                    text_bubbles[i].loc[1] < text_bubbles[j].loc[1] + text_bubbles[j].height and \
                    text_bubbles[i].loc[1] + text_bubbles[i].height > text_bubbles[j].loc[1]:
                # If the bubbles overlap, move the second bubble down
                print("DECONFLICTING")
                text_bubbles[j].loc = (text_bubbles[j].loc[0], text_bubbles[i].loc[1] + text_bubbles[i].height + 80)

    # for text_bubble in text_bubbles:
    #     text_bubble.get_off_of_point_to_loc()

    """
    Drawing the bubbles and triangles
    """
    draw = ImageDraw.Draw(image)

    for text_bubble in text_bubbles:
        # Define the location and size of the text bubble
        bubble_location = [text_bubble.loc[0], text_bubble.loc[1], text_bubble.loc[0] + text_bubble.width,
                           text_bubble.loc[1] + text_bubble.height]

        # Draw a triangle from the head edge to the text bubble
        head_edge_x = text_bubble.point_to_loc[0]
        head_edge_y = text_bubble.point_to_loc[1]
        draw.polygon([head_edge_x, head_edge_y, text_bubble.loc[0], text_bubble.loc[1] + text_bubble.height / 2,
                      text_bubble.loc[0] + text_bubble.width, text_bubble.loc[1] + text_bubble.height / 2],
                     fill='white', outline='black')

        # Draw the text bubble
        draw.ellipse(bubble_location, fill='white', outline='black')

        text_top_left = (text_bubble.loc[0] + (text_bubble.width - text_width) / 2,
                         text_bubble.loc[1] + (text_bubble.height - text_height) / 2)

        # Add the text to the bubble
        draw.text(text_top_left, text_bubble.text, fill='black', font=font)

        # Debug drawing
        # draw = ImageDraw.Draw(image)
        # draw.ellipse([head_edge_x - 5, head_edge_y - 5, head_edge_x + 5, head_edge_y + 5],
        #              fill='blue', outline='blue')
        # draw.ellipse([text_bubble.head_loc[0] - 5, text_bubble.head_loc[1] - 5, text_bubble.head_loc[0] + 5,
        #               text_bubble.head_loc[1] + 5], fill='red',
        #              outline='red')
        # draw.line([text_bubble.point_to_loc[0], text_bubble.point_to_loc[1], text_bubble.loc[0], text_bubble.loc[1]],
        #           fill='black')


    # Extending the image by 120 pixels at the bottom to put the scene description
    image = image.resize((image.size[0], image.size[1] + 120))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, image.size[1] - 120, image.size[0], image.size[1]], fill='white')
    draw.text((10, image.size[1] - 110), wrap_text(frame.scene_description, 900), fill='black', font=font)

    return image



if __name__ == "__main__":
    # Example usage

    print("starting example usage of text_bubble.py")

    guardian = CharacterMoment(Character("Guardian",
                                         "Tall and muscular, with a strong and chiseled jawline. Shiny silver armor with a glowing emblem on the chest.",
                                         "Brave and selfless"), "punches", "You're going down, villain!")
    shadow = CharacterMoment(Character("Shadow", "Wearing green",
                                       "Cunning and mysterious"), "dodges", "You can't catch me, Guardian!")

    description = "A top a skyscraper, Guardian and Shadow face off, there is a storm in the background and the battle is" +\
                    " intense. The city is visible below, and the sun is setting. Today is the day that the fate of the city" +\
                    " will be decided."
    frame = Frame(description, [guardian, shadow])
    output = add_text_bubbles(Image.open("text_bubble_adder/twoguys.jpg"), frame)
    # Save the image
    output.save("output1.jpg")
