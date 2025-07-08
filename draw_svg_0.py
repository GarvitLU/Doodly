from manim import *
class DrawSVG(Scene):
    def construct(self):
        svg = SVGMobject('outputs/image_baec8c64-ca4b-4f4a-9648-5eddba769fe2_0.svg', fill_opacity=0, stroke_width=2)
        self.play(Create(svg), run_time=2)
        self.wait(0.5)