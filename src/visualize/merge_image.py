import os
import shutil
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import LineCollection
from matplotlib.path import Path
from matplotlib.path import Path
from lxml import etree
import pyarrow as pa
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def merge_images_side_by_side(image_path1: str, image_path2: str, output_path: str):
    """
    Merges two images horizontally (side-by-side).
    Resizes them to match the height of the taller image.
    """
    from PIL import Image
    
    if not os.path.exists(image_path1):
        print(f"Merge Skip: File not found {image_path1}")
        return
    if not os.path.exists(image_path2):
        print(f"Merge Skip: File not found {image_path2}")
        return
        
    try:
        i1 = Image.open(image_path1)
        i2 = Image.open(image_path2)
        
        # Resize to match height of the taller one
        max_h = max(i1.height, i2.height)
        
        # Resize i1 if needed
        if i1.height != max_h:
            ratio = max_h / i1.height
            i1 = i1.resize((int(i1.width * ratio), max_h), Image.Resampling.LANCZOS)
            
        # Resize i2 if needed
        if i2.height != max_h:
            ratio = max_h / i2.height
            i2 = i2.resize((int(i2.width * ratio), max_h), Image.Resampling.LANCZOS)
        
        total_w = i1.width + i2.width
        
        new_img = Image.new('RGB', (total_w, max_h))
        new_img.paste(i1, (0, 0))
        new_img.paste(i2, (i1.width, 0))
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
            
        new_img.save(output_path)
        print(f"Merged Image Saved: {output_path}")
    except Exception as e:
        print(f"Error merging images: {e}")

