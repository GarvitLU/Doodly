import os
import subprocess
from manim import *
from moviepy.editor import concatenate_videoclips, AudioFileClip, VideoFileClip

# --- CONFIG ---
IMAGES_DIR = 'outputs'
AUDIO_PATH = None  # Set to your audio file path, e.g., 'outputs/audio_<job_id>.mp3'
OUTPUT_VIDEO = 'outputs/final_doodly_video.mp4'
RUN_TIME_PER_IMAGE = 2  # seconds per image animation

# --- 1. Convert PNGs to SVGs ---
def convert_pngs_to_svgs(images_dir):
    svg_paths = []
    for fname in sorted(os.listdir(images_dir)):
        if fname.endswith('.png'):
            png_path = os.path.join(images_dir, fname)
            pbm_path = png_path.replace('.png', '.pbm')
            svg_path = png_path.replace('.png', '.svg')
            # Convert PNG to PBM
            subprocess.run(['convert', png_path, '-threshold', '50%', pbm_path], check=True)
            # Convert PBM to SVG
            subprocess.run(['potrace', pbm_path, '-s', '-o', svg_path], check=True)
            svg_paths.append(svg_path)
    return svg_paths

# --- 2. Animate SVGs with Manim ---
class DrawSVG(Scene):
    def __init__(self, svg_path, run_time=2, **kwargs):
        self.svg_path = svg_path
        self.run_time = run_time
        super().__init__(**kwargs)
    def construct(self):
        svg = SVGMobject(self.svg_path, fill_opacity=0, stroke_width=2)
        self.play(Create(svg), run_time=self.run_time)
        self.wait(0.5)

def animate_svgs(svg_paths, run_time_per_image):
    video_paths = []
    for i, svg_path in enumerate(svg_paths):
        manim_script = f"from manim import *\nclass DrawSVG(Scene):\n    def construct(self):\n        svg = SVGMobject('{svg_path}', fill_opacity=0, stroke_width=2)\n        self.play(Create(svg), run_time={run_time_per_image})\n        self.wait(0.5)"
        script_path = f"draw_svg_{i}.py"
        with open(script_path, 'w') as f:
            f.write(manim_script)
        out_name = f"svg_anim_{i}.mp4"
        subprocess.run([
            'manim', '-pql', script_path, 'DrawSVG',
            '-o', out_name
        ], check=True)
        # Try to find the output video
        found = False
        for root, dirs, files in os.walk('media/videos'):
            if out_name in files:
                video_paths.append(os.path.join(root, out_name))
                found = True
                break
        if not found:
            print(f"Warning: Could not find generated video {out_name}")
    return video_paths

# --- 3. Concatenate Videos and Add Audio ---
def merge_videos_and_audio(video_paths, audio_path, output_path):
    clips = [VideoFileClip(v) for v in video_paths]
    final_clip = concatenate_videoclips(clips)
    if audio_path:
        audio = AudioFileClip(audio_path)
        final_clip = final_clip.set_audio(audio)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    for c in clips:
        c.close()

# --- MAIN PIPELINE ---
def main():
    global AUDIO_PATH
    # Find audio file
    for fname in os.listdir(IMAGES_DIR):
        if fname.startswith('audio_') and fname.endswith('.mp3'):
            AUDIO_PATH = os.path.join(IMAGES_DIR, fname)
            break
    print('Converting PNGs to SVGs...')
    svg_paths = convert_pngs_to_svgs(IMAGES_DIR)
    print('Animating SVGs with Manim...')
    video_paths = animate_svgs(svg_paths, RUN_TIME_PER_IMAGE)
    print('Video paths:', video_paths)
    if not video_paths:
        print('No video files were generated. Please check the Manim output for errors.')
        return
    print('Merging videos and adding audio...')
    merge_videos_and_audio(video_paths, AUDIO_PATH, OUTPUT_VIDEO)
    print(f'Final Doodly-style video saved to {OUTPUT_VIDEO}')

if __name__ == '__main__':
    main() 