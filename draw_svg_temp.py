
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        
        svg_path = 'apiOutputs/image_fb13786d-9d6d-49d6-9c99-48058bf572dc_0.svg'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=2)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        self.play(Create(svg), run_time=10.0)
        self.wait(0.5)
