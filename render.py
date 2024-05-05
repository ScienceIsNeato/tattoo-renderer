import cv2
import numpy as np
import random
import sys

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
        cv2.rectangle(image, (self.outer_wall_x, 0), (self.inner_wall_x, self.height), self.color, -1)

def generate_random_color():
    """Generates a random BGR color tuple."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def bezier_point(t, points):
    """ Calculate the Bezier curve point at t using recursive definition. """
    if len(points) == 1:
        return points[0]
    return (1 - t) * bezier_point(t, points[:-1]) + t * bezier_point(t, points[1:])

def connect_dots(image, start, end, style='line', color=(0, 0, 255)):
    if style == 'line':
        cv2.line(image, start, end, color, 2)
    elif style == 'gravitational':
        vertex = start if start[1] < end[1] else end
        other = end if start is vertex else start
        horizontal_distance = abs(vertex[0] - other[0])
        a = (other[1] - vertex[1]) / (horizontal_distance**2)
        h = vertex[0]
        k = vertex[1]
        x_values = np.linspace(vertex[0], other[0], num=100)
        y_values = a * (x_values - h)**2 + k
        points = np.stack((x_values, y_values), axis=1).astype(np.int32)
        points = points.reshape((-1, 1, 2))
        cv2.polylines(image, [points], False, color, 2, cv2.LINE_AA)
    elif style == 'filigree':
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        control_points = np.array([
            start,
            [mid_x - abs(end[1] - start[1]) / 3, mid_y - abs(end[0] - start[0]) / 3],
            [mid_x + abs(end[1] - start[1]) / 3, mid_y + abs(end[0] - start[0]) / 3],
            end
        ])
        t_values = np.linspace(0, 1, num=100)
        bezier_points = np.array([bezier_point(t, control_points) for t in t_values]).astype(np.int32)
        bezier_points = bezier_points.reshape((-1, 1, 2))
        cv2.polylines(image, [bezier_points], False, color, 2, cv2.LINE_AA)

def random_connections(image, line1, line2, num_connections, style='line', multicolor=False):
    for _ in range(num_connections):
        y1 = random.randint(0, line1.height)
        y2 = random.randint(0, line2.height)
        color = generate_random_color() if multicolor else (0, 0, 0)
        connect_dots(image, (line1.inner_wall_x, y1), (line2.inner_wall_x, y2), style=style, color=color)

if __name__ == "__main__":
    # Command-line inputs
    style = sys.argv[1] if len(sys.argv) > 1 else 'line'
    num_connections = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    multicolor = sys.argv[3].lower() in ['true', '1', 'yes', 'y'] if len(sys.argv) > 3 else False

    # Image dimensions adjusted to 4K portrait
    image_size = (2160, 2840)
    image = np.ones((image_size[1], image_size[0], 3), dtype=np.uint8)

    # Define and draw the lines
    center_x = 1080
    offset = 100
    left_center = center_x - offset
    right_center = center_x + offset
    background = VerticalLine(center=image_size[1]/2, width=image_size[0]*2, height=image_size[1], inner_face='left', color=(36, 36, 36))
    left_line = VerticalLine(center=left_center, width=30, height=image_size[1], inner_face='left')
    right_line = VerticalLine(center=right_center, width=30, height=image_size[1], inner_face='right')
    background.draw(image)
    left_line.draw(image)
    right_line.draw(image)

    # Add random connections based on input parameters
    random_connections(image, left_line, right_line, num_connections, style=style, multicolor=multicolor)

    # Save and display the image
    cv2.imwrite('vertical_lines_4k_portrait.png', image)
    print("Image saved as 'vertical_lines_4k_portrait.png'")
    cv2.imshow('Vertical Lines', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
