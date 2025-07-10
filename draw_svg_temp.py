
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        svg_path = 'outputs/image_950c5391-45e2-4259-98c4-c3549cfab13d_3.svg'
        png_path = 'outputs/image_950c5391-45e2-4259-98c4-c3549cfab13d_3.png'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=3)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        self.play(Create(svg), run_time=3.6)
        # Pop in the original image
        img = ImageMobject(png_path)
        img.width = svg.width
        img.height = svg.height
        img.move_to(svg.get_center())
        self.play(FadeIn(img), FadeOut(svg), run_time=0.5)
        self.wait(0.5)
