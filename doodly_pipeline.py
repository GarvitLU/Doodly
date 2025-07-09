import os
import subprocess
from manim import *
from moviepy.editor import concatenate_videoclips, AudioFileClip, VideoFileClip
import glob
import shutil
from svgpathtools import svg2paths
import numpy as np
import cv2
import svgwrite

# --- CONFIG ---
IMAGES_DIR = 'outputs'
AUDIO_PATH = None  # Set to your audio file path, e.g., 'outputs/audio_<job_id>.mp3'
OUTPUT_VIDEO = 'outputs/final_doodly_video.mp4'
RUN_TIME_PER_IMAGE = 2  # seconds per image animation

# --- 1. Convert PNGs to SVGs ---
def png_to_svg(png_path, output_dir=None):
    pbm_path = png_path.replace('.png', '.pbm')
    svg_path = png_path.replace('.png', '.svg')
    subprocess.run(['convert', png_path, '-threshold', '50%', pbm_path], check=True)
    subprocess.run(['potrace', pbm_path, '-s', '-o', svg_path], check=True)
    if output_dir:
        new_svg_path = os.path.join(output_dir, os.path.basename(svg_path))
        os.rename(svg_path, new_svg_path)
        return new_svg_path
    return svg_path

# --- 1A. Convert PNGs to Color SVGs ---
def png_to_color_svg(png_path, output_dir=None, k_colors=8, min_area=100):
    img = cv2.imread(png_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    Z = img_rgb.reshape((-1,3))
    Z = np.float32(Z)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = k_colors
    _, labels, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    segmented_img = centers[labels.flatten()].reshape(img_rgb.shape).astype(np.uint8)
    svg_path = png_path.replace('.png', '_color.svg')
    dwg = svgwrite.Drawing(svg_path, profile='tiny', size=(img.shape[1], img.shape[0]))
    for i, center in enumerate(centers):
        mask = (labels.reshape(img.shape[:2]) == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        color = svgwrite.rgb(int(center[0]), int(center[1]), int(center[2]))
        for cnt in contours:
            if cv2.contourArea(cnt) > min_area:
                path = "M " + " L ".join([f"{pt[0][0]},{pt[0][1]}" for pt in cnt]) + " Z"
                dwg.add(dwg.path(d=path, fill=color, stroke='black', stroke_width=1))
    dwg.save()
    if output_dir:
        new_svg_path = os.path.join(output_dir, os.path.basename(svg_path))
        os.rename(svg_path, new_svg_path)
        return new_svg_path
    return svg_path

# --- 2. Animate SVGs with Manim ---
def animate_svg(svg_path, duration, out_name, output_dir=None, heading=None):
    manim_script = f"""
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        {'heading = Text("' + heading.replace('"', '\"') + '", font="Arial", color=BLACK).scale(0.8).to_edge(UP)\n        self.play(Write(heading), run_time=2)' if heading else ''}
        svg_path = '{svg_path}'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=2)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        self.play(Create(svg), run_time={duration})
        self.wait(0.5)
"""
    script_path = f"draw_svg_temp.py"
    with open(script_path, 'w') as f:
        f.write(manim_script)
    subprocess.run([
        'manim', '-ql', '--disable_caching', script_path, 'DrawSVGWithHand',
        '-o', out_name
    ], check=True)
    # Find the output video
    video_path = None
    for root, dirs, files in os.walk('media/videos'):
        if out_name in files:
            video_path = os.path.join(root, out_name)
            break
    if not video_path:
        raise Exception('SVG animation video not found')
    if output_dir:
        new_video_path = os.path.join(output_dir, out_name)
        os.rename(video_path, new_video_path)
        return new_video_path
    return video_path

# --- 3. Concatenate Videos and Add Audio ---
def concatenate_videos(video_paths, output_path):
    clips = [VideoFileClip(v) for v in video_paths]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, codec='libx264', audio=False)
    for c in clips:
        c.close()
    return output_path

# --- MAIN PIPELINE ---
def main():
    global AUDIO_PATH
    # Find audio file
    for fname in os.listdir(IMAGES_DIR):
        if fname.startswith('audio_') and fname.endswith('.mp3'):
            AUDIO_PATH = os.path.join(IMAGES_DIR, fname)
            break
    print('Converting PNGs to SVGs...')
    svg_paths = [png_to_svg(os.path.join(IMAGES_DIR, fname)) for fname in sorted(os.listdir(IMAGES_DIR)) if fname.endswith('.png')]
    print('Animating SVGs with Manim...')
    video_paths = [animate_svg(svg_path, RUN_TIME_PER_IMAGE, f"svg_anim_{i}.mp4") for i, svg_path in enumerate(svg_paths)]
    print('Video paths:', video_paths)
    if not video_paths:
        print('No video files were generated. Please check the Manim output for errors.')
        return
    print('Merging videos and adding audio...')
    merge_videos_and_audio(video_paths, AUDIO_PATH, OUTPUT_VIDEO)
    print(f'Final Doodly-style video saved to {OUTPUT_VIDEO}')
    # Cleanup: delete PBM and SVG files in outputs/ and media/videos directory, keep PNG images
    for ext in ('*.pbm', '*.svg'):
        for f in glob.glob(os.path.join(IMAGES_DIR, ext)):
            try:
                os.remove(f)
            except Exception as e:
                print(f'Warning: Could not delete {f}: {e}')
    if os.path.exists('media/videos'):
        shutil.rmtree('media/videos')
    print('Cleanup complete: PBM, SVG, and intermediate media files deleted, PNG images retained.')

if __name__ == '__main__':
    main() 