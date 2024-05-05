import cv2
import numpy as np
import random

class VerticalLine:
    def __init__(self, center, width, height, inner_face, color=(0, 0, 0)):
        self.center = int(center)
        self.width = int(width)
        self.height = int(height)
        self.color = color  # Ensure this is a tuple of three integers, e.g., (255, 255, 255)
        if inner_face == 'right':
            self.outer_wall_x = int(center + width // 2)
            self.inner_wall_x = int(center - width // 2)
        else:
            self.outer_wall_x = int(center - width // 2)
            self.inner_wall_x = int(center + width // 2)

    def draw(self, image):
        # Use integer coordinates explicitly
        cv2.rectangle(image, (self.outer_wall_x, 0), (self.inner_wall_x, self.height), self.color, -1)

def generate_random_color():
  """Generates a random BGR color tuple."""
  return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def connect_dots(image, start, end, style='line', color=(0, 0, 0)):
    if style == 'line':
        cv2.line(image, start, end, color, 2)

def random_connections(image, line1, line2, num_connections, style='line', multicolor=False):
  if multicolor:
      for _ in range(num_connections):
          y1 = random.randint(0, line1.height)
          y2 = random.randint(0, line2.height)
          color = generate_random_color()  # Generate random color
          connect_dots(image, (line1.inner_wall_x, y1), (line2.inner_wall_x, y2), style=style, color=color)
  else:
      # Use default color (optional, modify as needed)
      color = (0, 0, 0)  # Black in BGR format
      for _ in range(num_connections):
          y1 = random.randint(0, line1.height)
          y2 = random.randint(0, line2.height)
          connect_dots(image, (line1.inner_wall_x, y1), (line2.inner_wall_x, y2), style=style, color=color)

# Image dimensions adjusted to 4K portrait
image_size = (2160, 2840)

image = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8)

# Define the lines
center_x = 1080
offset = 100
left_center = center_x - offset
right_center = center_x + offset

background = VerticalLine(center=image_size[1]/2, width=image_size[0]*2, height=image_size[1], inner_face='left', color=(36, 36, 36))
left_line = VerticalLine(center=left_center, width=30, height=image_size[1], inner_face='left')
right_line = VerticalLine(center=right_center, width=30, height=image_size[1],inner_face='right')

# Draw the lines
background.draw(image)
left_line.draw(image)
right_line.draw(image)

# Add random connections
num_connections = 150  # Specify the number of connections
multicolor = False
random_connections(image, left_line, right_line, num_connections, 'line', multicolor=multicolor)

# Save the image
cv2.imwrite('/mnt/data/vertical_lines_4k_portrait.png', image)

# Due to the change to 4K, cv2.imshow may not be practical for display
print("Image saved as 'vertical_lines_4k_portrait.png'")

# Show the image
cv2.imshow('Vertical Lines', image)
cv2.waitKey(0)
cv2.destroyAllWindows()