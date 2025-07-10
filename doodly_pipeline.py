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
import xml.etree.ElementTree as ET
import json

# --- CONFIG ---
IMAGES_DIR = 'outputs'
AUDIO_PATH = None  # Set to your audio file path, e.g., 'outputs/audio_<job_id>.mp3'
OUTPUT_VIDEO = 'outputs/final_doodly_video.mp4'
RUN_TIME_PER_IMAGE = 2  # seconds per image animation

# --- 1. Convert PNGs to SVGs ---
def png_to_svg(png_path, output_dir=None):
    pbm_path = png_path.replace('.png', '.pbm')
    svg_path = png_path.replace('.png', '.svg')
    # Use ImageMagick to threshold and Potrace for clean vector lines
    subprocess.run(['magick', png_path, '-threshold', '50%', pbm_path], check=True)
    # Potrace options: -t 0 (sharp threshold), -a 1 (smooth curves), --flat (no curve optimization), --opaque (no transparency)
    subprocess.run(['potrace', pbm_path, '-s', '-o', svg_path, '-t', '0', '-a', '1', '--flat', '--opaque'], check=True)
    # Post-process SVG: remove fills, keep only stroke, set stroke-width=3
    import xml.etree.ElementTree as ET
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if 'fill' in elem.attrib:
            elem.attrib['fill'] = 'none'
        elem.attrib['stroke'] = 'black'
        elem.attrib['stroke-width'] = '3'
    tree.write(svg_path)
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

# --- SVG Parsing for Word-Level Animation ---
def parse_svg_elements(svg_path):
    """
    Parse SVG and return a list of drawable sub-elements (paths/groups) for word-level animation.
    Returns a list of element IDs or path data.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    elements = []
    for elem in root.findall('.//svg:path', ns):
        elem_id = elem.get('id')
        path_data = elem.get('d')
        elements.append({'id': elem_id, 'd': path_data})
    # Optionally add groups or other shapes
    return elements

# --- 2. Animate SVGs with Manim ---
def animate_svg(svg_path, duration, out_name, output_dir=None, heading=None):
    # Infer PNG path from SVG path
    png_path = svg_path.replace('.svg', '.png')
    manim_script = f"""
from manim import *
from svgpathtools import svg2paths
import numpy as np
class DrawSVGWithHand(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        {'heading = Text("' + heading.replace('"', '\"') + '", font="Arial", color=BLACK).scale(0.8).to_edge(UP)\n        self.play(Write(heading), run_time=2)' if heading else ''}
        svg_path = '{svg_path}'
        png_path = '{png_path}'
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=3)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        self.play(Create(svg), run_time={duration})
        # Pop in the original image
        img = ImageMobject(png_path)
        img.width = svg.width
        img.height = svg.height
        img.move_to(svg.get_center())
        self.play(FadeIn(img), FadeOut(svg), run_time=0.5)
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

def generate_manim_script_word_sync(svg_path, word_svg_mapping, out_name, audio_path=None, heading=None):
    """
    Generate a Manim script that animates SVG sub-elements in sync with word timings.
    Each SVG element is drawn in sync with its word's start/end time.
    """
    mapping_json = json.dumps(word_svg_mapping)
    manim_script = f"""
from manim import *
import json
from svgpathtools import svg2paths
import numpy as np

class DrawSVGWordSync(Scene):
    def construct(self):
        self.camera.background_color = WHITE
        {'heading = Text("' + heading.replace('"', '\"') + '", font="Arial", color=BLACK).scale(0.8).to_edge(UP)\n        self.play(Write(heading), run_time=2)' if heading else ''}
        svg_path = '{svg_path}'
        mapping = json.loads('''{mapping_json}''')
        svg = SVGMobject(svg_path, fill_opacity=0, stroke_width=2)
        svg.set_color(BLACK)
        svg.scale(3.0)
        self.add(svg)
        for item in mapping:
            elem_id = item['svg_element']['id']
            if elem_id:
                sub_svg = [el for el in svg.submobjects if hasattr(el, 'id') and el.id == elem_id]
                if sub_svg:
                    self.play(Create(sub_svg[0]), run_time=item['end']-item['start'])
        self.wait(0.5)
"""
    script_path = f"draw_svg_temp.py"
    with open(script_path, 'w') as f:
        f.write(manim_script)
    return script_path

# --- 3. Concatenate Videos and Add Audio ---
def concatenate_videos(video_paths, output_path):
    clips = [VideoFileClip(v) for v in video_paths]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, codec='libx264', audio=False)
    for c in clips:
        c.close()
    return output_path

def merge_videos_and_audio(video_paths, audio_path, output_path):
    """
    Merge video clips and add audio to create final video
    """
    if not video_paths:
        raise Exception("No video paths provided")
    
    # Load video clips
    clips = [VideoFileClip(v) for v in video_paths]
    
    # Concatenate videos
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Add audio if provided
    if audio_path and os.path.exists(audio_path):
        audio_clip = AudioFileClip(audio_path)
        final_video = final_video.set_audio(audio_clip)
    
    # Write final video
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
    
    # Clean up
    final_video.close()
    for clip in clips:
        clip.close()
    
    return output_path

def map_words_to_svg_elements(words, svg_elements):
    """
    Map each word to a corresponding SVG element for animation.
    For now, assign words to elements in order (1:1 mapping, or repeat if more words than elements).
    Returns a list of dicts: {word, start, end, svg_element}
    """
    mapping = []
    n = min(len(words), len(svg_elements))
    for i in range(n):
        mapping.append({
            'word': words[i]['word'],
            'start': words[i]['start'],
            'end': words[i]['end'],
            'svg_element': svg_elements[i]
        })
    # If more words than elements, repeat last element
    for i in range(n, len(words)):
        mapping.append({
            'word': words[i]['word'],
            'start': words[i]['start'],
            'end': words[i]['end'],
            'svg_element': svg_elements[-1]
        })
    return mapping

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
    video_paths = []
    for i, svg_path in enumerate(svg_paths):
        video_path = animate_svg(svg_path, RUN_TIME_PER_IMAGE, f"svg_anim_{i}.mp4")
        video_paths.append(video_path)

    print('Video paths:', video_paths)
    if not video_paths:
        print('No video files were generated. Please check the Manim output for errors.')
        return
    print('Merging videos and adding audio...')
    merge_videos_and_audio(video_paths, AUDIO_PATH, OUTPUT_VIDEO)
    print(f'Final Doodly-style video saved to {OUTPUT_VIDEO}')
    # Cleanup: delete all temporary audio files (audio_*.mp3)
    for f in glob.glob(os.path.join(IMAGES_DIR, "audio_*.mp3")):
        try:
            os.remove(f)
        except Exception as e:
            print(f'Warning: Could not delete {f}: {e}')
    print('Cleanup complete: Deleted all temporary audio files.')
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