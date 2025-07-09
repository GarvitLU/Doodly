
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        svg_path = 'outputs/image_870f9da2-43c0-418c-9fb9-61e058249434_7.svg'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=2)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        self.play(Create(svg), run_time=2.93)
        self.wait(0.5)
