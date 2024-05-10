import subprocess
import tkinter as tk
from tkinter import filedialog, StringVar, DoubleVar, ttk
import json
import os


def get_video_dimensions(file_path):
    command = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height', '-of', 'json', file_path
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(process.stdout.decode('utf-8'))
    video_stream = metadata.get('streams', [])[0]
    return video_stream['width'], video_stream['height']


def get_image_dimensions(file_path):
    command = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height', '-of', 'json', file_path
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(process.stdout.decode('utf-8'))
    image_stream = metadata.get('streams', [])[0]
    return image_stream['width'], image_stream['height']


def get_unique_filename(file_path):
    if not os.path.exists(file_path):
        return file_path

    base, extension = os.path.splitext(file_path)
    index = 1
    while True:
        new_file_path = f"{base}_{index}{extension}"
        if not os.path.exists(new_file_path):
            return new_file_path
        index += 1


def add_watermark(input_video, output_video, watermark_image, size_percentage=30, position='upper left', opacity=0.5,
                  codec='libx264', file_ext='mp4'):
    video_width, video_height = get_video_dimensions(input_video)
    wm_orig_width, wm_orig_height = get_image_dimensions(watermark_image)

    # Maintain aspect ratio
    scale_factor = size_percentage / 100
    wm_width = int(wm_orig_width * scale_factor)
    wm_height = int(wm_orig_height * scale_factor)

    position_coords = calculate_position(position, video_width, video_height, wm_width, wm_height)
    watermark_opacity = f'format=rgba,colorchannelmixer=aa={opacity}'

    filter_complex = f"[1:v]scale={wm_width}:{wm_height},{watermark_opacity}[wm];[0:v][wm]overlay={position_coords}"

    output_video = output_video if output_video.endswith(f'.{file_ext}') else f"{output_video}.{file_ext}"

    command = [
        'ffmpeg', '-i', input_video, '-i', watermark_image, '-filter_complex', filter_complex,
        '-c:a', 'copy', '-c:v', codec, '-crf', '18', '-preset', 'medium', output_video
    ]

    subprocess.run(command)


def calculate_position(position, video_width, video_height, watermark_width, watermark_height):
    positions = {
        "upper left": "10:10",
        "upper right": f"{video_width - watermark_width - 10}:10",
        "lower left": f"10:{video_height - watermark_height - 10}",
        "lower right": f"{video_width - watermark_width - 10}:{video_height - watermark_height - 10}",
        "center": f"{(video_width - watermark_width) // 2}:{(video_height - watermark_height) // 2}"
    }
    return positions.get(position.lower(), "10:10")


def open_file_dialog(title):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title=title)
    root.destroy()
    return file_path


def start_app():
    root = tk.Tk()
    root.title("Rainmaker Watermarker")

    def on_submit():
        input_video = input_video_path.get()
        watermark_image = watermark_image_path.get()
        output_video = output_video_path.get()
        size_percentage = watermark_size_var.get()
        position = position_var.get()
        opacity = opacity_var.get()
        codec = codec_var.get()
        file_ext = file_ext_var.get()

        output_video = get_unique_filename(output_video)
        add_watermark(input_video, output_video, watermark_image, size_percentage, position, opacity, codec, file_ext)
        print(f'Watermarked video saved as {output_video}')
        root.quit()

    input_video_path = StringVar()
    watermark_image_path = StringVar()
    output_video_path = StringVar(value="output")
    watermark_size_var = DoubleVar(value=30)  # Set to 30% by default
    position_var = StringVar(value="upper left")
    opacity_var = DoubleVar(value=0.5)
    codec_var = StringVar(value="libx264")
    file_ext_var = StringVar(value="mp4")

    # UI Elements
    ttk.Label(root, text="Input Video:").grid(row=0, column=0, sticky="w")
    ttk.Entry(root, textvariable=input_video_path, width=50).grid(row=0, column=1)
    ttk.Button(root, text="Browse...",
               command=lambda: input_video_path.set(open_file_dialog("Select Input Video File"))).grid(row=0, column=2)

    ttk.Label(root, text="Watermark Image:").grid(row=1, column=0, sticky="w")
    ttk.Entry(root, textvariable=watermark_image_path, width=50).grid(row=1, column=1)
    ttk.Button(root, text="Browse...",
               command=lambda: watermark_image_path.set(open_file_dialog("Select Watermark Image"))).grid(row=1,
                                                                                                          column=2)

    ttk.Label(root, text="Output Video:").grid(row=2, column=0, sticky="w")
    ttk.Entry(root, textvariable=output_video_path, width=50).grid(row=2, column=1)

    ttk.Label(root, text="Watermark Size %:").grid(row=3, column=0, sticky="w")
    tk.Scale(root, variable=watermark_size_var, from_=10, to=100, orient="horizontal", resolution=1).grid(row=3,
                                                                                                          column=1)  # Slider

    ttk.Label(root, text="Watermark Position:").grid(row=4, column=0, sticky="w")
    positions = ["upper left", "upper right", "lower left", "lower right", "center"]
    for i, pos in enumerate(positions):
        ttk.Radiobutton(root, text=pos, variable=position_var, value=pos).grid(row=4 + i, column=1, sticky="w")

    ttk.Label(root, text="Opacity:").grid(row=9, column=0, sticky="w")
    tk.Scale(root, variable=opacity_var, from_=0, to=1, orient="horizontal", resolution=0.1).grid(row=9, column=1,
                                                                                                  sticky="w")

    ttk.Label(root, text="Codec:").grid(row=10, column=0, sticky="w")
    ttk.OptionMenu(root, codec_var, "libx264", "libx264", "libx265", "mpeg4", "vp9").grid(row=10, column=1, sticky="w")

    ttk.Label(root, text="File Extension:").grid(row=11, column=0, sticky="w")
    ttk.OptionMenu(root, file_ext_var, "mp4", "mp4", "mkv", "avi", "webm").grid(row=11, column=1, sticky="w")

    ttk.Button(root, text="Add Watermark", command=on_submit).grid(row=12, column=1)

    root.mainloop()


if __name__ == '__main__':
    start_app()
