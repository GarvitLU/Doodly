from manim import *
class DrawSVG(Scene):
    def construct(self):
        svg = SVGMobject('outputs/image_e7c5600a-7481-4c4a-b4f3-5069c09f6fd7_5.svg', fill_opacity=0, stroke_width=2)
        self.play(Create(svg), run_time=2)
        self.wait(0.5)