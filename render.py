import cv2
import numpy as np
import random

class VerticalLine:
    def __init__(self, center, width, height, inner_face):
        self.center = center
        self.width = width
        self.height = height
        if inner_face == 'right':
            self.outer_wall_x = center + width // 2  # Adjusted for correct origin
            self.inner_wall_x = center - width // 2  # Adjusted for correct origin
        else:
            self.outer_wall_x = center - width // 2  # Adjusted for correct origin
            self.inner_wall_x = center + width // 2  # Adjusted for correct origin

    def draw(self, image):
        cv2.rectangle(image, (self.outer_wall_x, 0), (self.inner_wall_x, self.height), (0, 0, 0), -1)

def connect_dots(image, start, end, style='line'):
    if style == 'line':
        cv2.line(image, start, end, (0, 0, 255), 2)

def random_connections(image, line1, line2, num_connections):
    for _ in range(num_connections):
        y1 = random.randint(0, line1.height)
        y2 = random.randint(0, line2.height)
        connect_dots(image, (line1.inner_wall_x, y1), (line2.inner_wall_x, y2))

# Image dimensions adjusted to 4K portrait
image_size = (2160, 1840)

# Create a blank image with a softer background color
image = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8) * 240

# Define the lines
center_x = 1080
offset = 100
left_center = center_x - offset
right_center = center_x + offset

left_line = VerticalLine(center=left_center, width=30, height=image_size[1], inner_face='left')
right_line = VerticalLine(center=right_center, width=30, height=image_size[1],inner_face='right')

# Draw the lines
left_line.draw(image)
right_line.draw(image)

# Add random connections
num_connections = 5  # Specify the number of connections
random_connections(image, left_line, right_line, num_connections)

# Save the image
cv2.imwrite('/mnt/data/vertical_lines_4k_portrait.png', image)

# Due to the change to 4K, cv2.imshow may not be practical for display
print("Image saved as 'vertical_lines_4k_portrait.png'")

# Show the image
cv2.imshow('Vertical Lines', image)
cv2.waitKey(0)
cv2.destroyAllWindows()