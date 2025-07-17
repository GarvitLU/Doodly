
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        svg_path = 'outputs/image_4969d0a0-c350-41aa-96e7-f257dbdd359b_1_local.svg'
        png_path = 'outputs/image_4969d0a0-c350-41aa-96e7-f257dbdd359b_1_local.png'
        
        # Create the SVG for drawing animation
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=3)
        svg.set_color(BLACK)
        svg.scale(3.0)
        
        # Create the final image (same size and position as SVG)
        img = ImageMobject(png_path)
        img.width = svg.width
        img.height = svg.height
        img.move_to(svg.get_center())
        
        # Start with the SVG drawing animation
        self.add(svg)
        self.play(Create(svg), run_time=9.61)
        
        # Seamlessly replace SVG with final image (no visible transition)
        # The image is already positioned exactly where the SVG is
        self.remove(svg)
        self.add(img)
        
        # Hold the final image for a moment
        self.wait(0.5)
