
from manim import *
from svgpathtools import svg2paths
import numpy as np

class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        svg_path = 'outputs/image_c3481968-1858-47a8-ac82-86bd652388ad_0.svg'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=2)
        svg.set_color(BLACK)
        self.add(svg)
        paths, _ = svg2paths(svg_path)
        if not paths:
            return
        path = paths[0]
        n_points = 100
        points = [path.point(t) for t in np.linspace(0, 1, n_points)]
        points = [(p.real, p.imag, 0) for p in points]
        hand = ImageMobject('hand.png').scale(0.2)
        hand.move_to(points[0])
        self.add(hand)
        def update_hand(mob, alpha):
            idx = int(alpha * (n_points - 1))
            mob.move_to(points[idx])
        self.play(
            Create(svg),
            UpdateFromAlphaFunc(hand, update_hand),
            run_time=2
        )
        self.wait(0.5)
