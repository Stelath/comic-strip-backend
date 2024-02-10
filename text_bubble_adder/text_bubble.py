from PIL import Image, ImageDraw, ImageFont
from clipseg import get_location
from story_components.character import CharacterMoment, Character

MAX_TEXT_WIDTH = 200


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
        x = head_x + 20
    # If the head is on the right side of the image, the text bubble will be on the left side
    else:
        x = head_x - 20 - t_width

    # Placing the bubble above the head
    # If the bubble would go off the top of the image, place it as high as possible
    y = head_y - 20 - t_height
    if y < 0:
        y = 0

    return x, y


def calculate_text_size(text: str, font):
    lines = text.split("\n")
    longest_line = max(lines, key=len)
    bbox = font.getbbox(longest_line)
    single_line_height = bbox[3] - bbox[1]
    return bbox[2] - bbox[0], (single_line_height + single_line_height / 3 + 2) * len(lines)


def wrap_text(text: str):
    # Finds a space and replaces it with a newline character
    # Tries to keep each line to a length of x characters
    # Searches for the nearest space to the xth character without going over

    l = 0
    best_space = None
    for i, c in enumerate(text):
        if c == " ":
            best_space = i
        if c != "\n":
            l += 1
        if l > MAX_TEXT_WIDTH / 5:
            if best_space:
                text = text[:best_space] + "\n" + text[best_space + 1:]
                l = i - best_space
                best_space = None
            else:
                text = text[:i] + "\n" + text[i + 1:]
                l = 0
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
        if check_logit < head_logit - 1:
            break
        check_x += direction * 2
        check_y -= 0.1

    return check_x, check_y


class TextBubble:
    def __init__(self, loc, width, height, point_to_loc, text):
        """
        Holds all the values associated with a text bubble
        :param loc: The top left corner of the ellipse (x,y)
        :param width: How wide the ellipse is
        :param height: How tall the ellipse is
        :param point_to_loc: The location that the triangle points to (x,y)
        :param text: The text to be displayed in the bubble
        """

        self.loc = loc
        self.width = width
        self.height = height
        self.point_to_loc = point_to_loc
        self.text = text


def add_text_bubbles(image: Image, character_moments: list[CharacterMoment]):
    font_size = 30
    font = ImageFont.truetype("textbubblefont.ttf", font_size)

    """
    Getting a bubble for each character in the frame
    """

    text_bubbles = []
    for character_moment in character_moments:
        physical_description = character_moment.physical_description + " head"
        dialogue = character_moment.dialogue

        # Wrap the text
        dialogue = wrap_text(dialogue)
        text_width, text_height = calculate_text_size(dialogue, font)

        bubble_width = text_width * 1.25 + font_size * 2
        bubble_height = text_height * 1.25 + font_size * 2

        vals = get_location(image, [physical_description])
        head_location = (vals[0], vals[1])
        logits = vals[2]

        head_edge = find_head_edge(image, head_location, logits)
        bubble_top_left = pick_relative_location(image, head_location, bubble_width, bubble_height)

        text_bubbles.append(TextBubble(bubble_top_left, bubble_width, bubble_height, head_edge, dialogue))

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
                text_bubbles[j].loc = (text_bubbles[j].loc[0], text_bubbles[i].loc[1] + text_bubbles[i].height + 20)
                text_bubbles[j].point_to_loc = (text_bubbles[j].point_to_loc[0], text_bubbles[i].point_to_loc[1] + text_bubbles[i].height + 20)

    """
    Drawing the bubbles and triangles
    """
    draw = ImageDraw.Draw(image)

    for text_bubble in text_bubbles:
        # Define the location and size of the text bubble
        bubble_location = [text_bubble.loc[0], text_bubble.loc[1], text_bubble.loc[0] + text_bubble.width, text_bubble.loc[1] + text_bubble.height]

        # Draw a triangle from the head edge to the text bubble
        head_x = text_bubble.point_to_loc[0]
        head_y = text_bubble.point_to_loc[1]
        draw.polygon([head_x, head_y, text_bubble.loc[0], text_bubble.loc[1] + text_bubble.height / 2, text_bubble.loc[0] + text_bubble.width, text_bubble.loc[1] + text_bubble.height / 2], fill='white', outline='black')

        # Draw the text bubble
        draw.ellipse(bubble_location, fill='white', outline='black')

        text_top_left = (text_bubble.loc[0] + (text_bubble.width - text_width) / 2, text_bubble.loc[1] + (text_bubble.height - text_height) / 2)

        # Add the text to the bubble
        draw.text(text_top_left, text_bubble.text, fill='black', font=font)

    return image


# Usage
dialogue = "Hello there! I'm John. I love to walk around and talk to people. I'm a very friendly person. I also like trees!"
my_character = CharacterMoment(Character("John", "A dark haired man", "None"), "walks", dialogue)
add_text_bubbles(Image.open("dark-haired-man.jpg"), [my_character])