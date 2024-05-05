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

def connect_dots(image, start, end, style='line', color=(0, 0, 255)):
    if style == 'line':
        cv2.line(image, start, end, color, 2)
    elif style == 'gravitational':
        # Determine which point is the vertex (higher y-value because y increases downwards)
        vertex = start if start[1] < end[1] else end
        other = end if start is vertex else start

        # Calculate horizontal distance and total x movement
        horizontal_distance = abs(vertex[0] - other[0])

        # Establish parameters for the parabola
        a = (other[1] - vertex[1]) / (horizontal_distance**2)  # Parabola coefficient a
        h = vertex[0]  # x-coordinate of the vertex
        k = vertex[1]  # y-coordinate of the vertex

        # Generate x values from vertex to other point
        x_values = np.linspace(vertex[0], other[0], num=100)  # Number of points can be increased for smoother curve

        # Compute y-values for parabola: y = a(x - h)^2 + k
        y_values = a * (x_values - h)**2 + k

        # Prepare points for drawing
        points = np.stack((x_values, y_values), axis=1).astype(np.int32)
        points = points.reshape((-1, 1, 2))
        cv2.polylines(image, [points], False, color, 2, cv2.LINE_AA)  # Use LINE_AA for anti-aliased curves

        # Ensure the other point falls on the parabola
        assert np.isclose(other[1], a * (other[0] - h)**2 + k, atol=1), "The other point does not lie on the parabola as expected."


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
multicolor = True
style = 'gravitational'
random_connections(image, left_line, right_line, num_connections, style=style, multicolor=multicolor)

# Save the image
cv2.imwrite('/mnt/data/vertical_lines_4k_portrait.png', image)

# Due to the change to 4K, cv2.imshow may not be practical for display
print("Image saved as 'vertical_lines_4k_portrait.png'")

# Show the image
cv2.imshow('Vertical Lines', image)
cv2.waitKey(0)
cv2.destroyAllWindows()