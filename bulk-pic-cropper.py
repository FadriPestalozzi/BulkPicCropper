from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import sys

def select_folders():
    """GUI to select input and output folders"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Select input folder
    input_folder = filedialog.askdirectory(
        title="Select Input Folder (containing images to crop)"
    )
    
    if not input_folder:
        messagebox.showinfo("Cancelled", "No input folder selected. Exiting.")
        return None, None
    
    # Select output folder
    output_folder = filedialog.askdirectory(
        title="Select Output Folder (where cropped images will be saved)"
    )
    
    if not output_folder:
        messagebox.showinfo("Cancelled", "No output folder selected. Exiting.")
        return None, None
    
    root.destroy()
    return input_folder, output_folder

def find_first_image(input_folder):
    """Find the first image file in the input folder"""
    image_files = [f for f in os.listdir(input_folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not image_files:
        return None
    
    return os.path.join(input_folder, sorted(image_files)[0])

def run_crop_selector(first_image_path):
    """Run the crop selector on the first image and return crop box coordinates"""
    try:
        # Create a temporary crop selector script that works with the selected image
        temp_selector_content = f'''
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json

# Import the CropSelector class from the existing file
import sys
import importlib.util

# Load the crop selector module from the file with hyphens
spec = importlib.util.spec_from_file_location("crop_selector", "pic-crop-selector.py")
crop_selector_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crop_selector_module)

class ModifiedCropSelector(crop_selector_module.CropSelector):
    def confirm_selection(self):
        if self.crop_box is None:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return
        
        result = messagebox.askyesno("Confirm", 
            f"Use crop box {{self.crop_box}}?\\n\\nThis will be used for bulk cropping.")
        
        if result:
            # Write coordinates to a temporary file instead of updating the script
            with open('temp_crop_coords.json', 'w') as f:
                json.dump({{
                    'crop_box': self.crop_box,
                    'status': 'success'
                }}, f)
            messagebox.showinfo("Success", 
                f"Selected crop box: {{self.crop_box}}")
            self.root.quit()

def main():
    first_image = r"{first_image_path}"
    print(f"Opening first image: {{first_image}}")
    
    selector = ModifiedCropSelector(first_image)
    selector.run()

if __name__ == "__main__":
    main()
'''
        
        # Write temporary script
        with open('temp_crop_selector.py', 'w') as f:
            f.write(temp_selector_content)
        
        # Remove any existing temp coordinates file
        if os.path.exists('temp_crop_coords.json'):
            os.remove('temp_crop_coords.json')
        
        # Run the crop selector
        result = subprocess.run([sys.executable, 'temp_crop_selector.py'], 
                              capture_output=True, text=True)
        
        # Clean up temporary script file
        if os.path.exists('temp_crop_selector.py'):
            os.remove('temp_crop_selector.py')
        
        if result.returncode != 0:
            messagebox.showerror("Error", f"Crop selector failed: {result.stderr}")
            return None
        
        # Read the crop box coordinates from the temporary file
        if os.path.exists('temp_crop_coords.json'):
            try:
                import json
                with open('temp_crop_coords.json', 'r') as f:
                    data = json.load(f)
                
                # Clean up temporary coordinates file
                os.remove('temp_crop_coords.json')
                
                if data.get('status') == 'success' and 'crop_box' in data:
                    crop_box = tuple(data['crop_box'])
                    print(f"Received crop box: {crop_box}")
                    return crop_box
                else:
                    messagebox.showerror("Error", "No valid crop box coordinates received")
                    return None
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read crop coordinates: {str(e)}")
                return None
        else:
            messagebox.showinfo("Cancelled", "Crop selection was cancelled")
            return None
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run crop selector: {str(e)}")
        return None

def get_crop_box_from_script():
    """Extract the crop_box coordinates from this script file"""
    try:
        # Read from the pic-bulk-crop.py file specifically
        script_file = 'pic-bulk-crop.py'
        with open(script_file, 'r') as f:
            content = f.read()
        
        # Find the crop_box line with actual coordinates (not function calls)
        for line in content.split('\n'):
            if (line.strip().startswith('crop_box =') and 
                '(' in line and 
                ')' in line and 
                'get_crop_box_from_script' not in line):
                # Extract the tuple from the line
                start = line.find('(')
                end = line.find(')', start) + 1
                crop_box_str = line[start:end]
                return eval(crop_box_str)
        
        return None
    except Exception as e:
        print(f"Error reading crop box: {e}")
        return None

def main():
    print("Bulk Picture Cropper")
    print("=" * 50)
    
    # Step 1: Select folders
    print("Step 1: Selecting folders...")
    input_folder, output_folder = select_folders()
    
    if not input_folder or not output_folder:
        return
    
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Step 2: Find first image
    print("\nStep 2: Finding first image...")
    first_image = find_first_image(input_folder)
    
    if not first_image:
        messagebox.showerror("Error", "No image files found in the input folder!")
        return
    
    print(f"First image: {first_image}")
    
    # Step 3: Run crop selector and get crop coordinates
    print("\nStep 3: Opening crop selector...")
    print("Please select the crop area on the first image.")
    
    crop_box = run_crop_selector(first_image)
    
    if not crop_box:
        return
    
    print(f"Crop box: {crop_box}")
    
    # Step 4: Process all images
    print("\nStep 4: Processing all images...")
    
    image_files = [f for f in os.listdir(input_folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not image_files:
        messagebox.showerror("Error", "No image files found!")
        return
    
    processed_count = 0
    error_count = 0
    
    for fname in image_files:
        try:
            input_path = os.path.join(input_folder, fname)
            
            # Create output filename with "-cropped" before the file extension
            name, ext = os.path.splitext(fname)
            output_fname = f"{name}-cropped{ext}"
            output_path = os.path.join(output_folder, output_fname)
            
            print(f"Processing: {fname} -> {output_fname}")
            
            img = Image.open(input_path)
            cropped = img.crop(crop_box)
            cropped.save(output_path)
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {fname}: {e}")
            error_count += 1
    
    # Summary
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count} images")
    if error_count > 0:
        print(f"Errors: {error_count} images")
    
    messagebox.showinfo("Complete", 
        f"Bulk cropping complete!\n\n"
        f"Processed: {processed_count} images\n"
        f"Errors: {error_count} images\n"
        f"Output folder: {output_folder}")

crop_box = (222, 141, 752, 803)  # (left, upper, right, lower)

if __name__ == "__main__":
    main()
