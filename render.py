import cv2
import numpy as np

class VerticalLine:
    def __init__(self, center, width, height):
        self.center = center
        self.width = width
        self.height = height
        self.outer_wall_x = center + width // 2
        self.inner_wall_x = center - width // 2

    def draw(self, image):
        cv2.rectangle(image, (self.inner_wall_x, 0), (self.outer_wall_x, self.height), (0, 0, 0), -1)

# Image dimensions
image_size = (424, 554)

# Create a blank white image
image = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8) * 255

# Define the lines
left_line = VerticalLine(center=100, width=10, height=image_size[1])
right_line = VerticalLine(center=300, width=10, height=image_size[1])

# Draw the lines
left_line.draw(image)
right_line.draw(image)

# Save the image
cv2.imwrite('/mnt/data/vertical_lines_updated.png', image)

# Show the image
cv2.imshow('Vertical Lines', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
