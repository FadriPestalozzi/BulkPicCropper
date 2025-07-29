import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

class CropSelector:
    def __init__(self, image_path):
        self.root = tk.Tk()
        self.root.title("Crop Box Selector")
        
        # Make window resizable and set a good initial size
        self.root.resizable(True, True)
        
        # Get screen dimensions for better initial sizing
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Use 80% of screen width and 85% of screen height
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.85)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Load original image
        self.original_image = Image.open(image_path)
        
        # Zoom and display variables
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Adaptive canvas size based on screen size and image
        self.max_canvas_width = min(int(screen_width * 0.6), 1400)
        self.max_canvas_height = min(int(screen_height * 0.6), 900)
        
        # Calculate initial scale to fit image in window
        self.base_scale = min(
            self.max_canvas_width / self.original_image.width,
            self.max_canvas_height / self.original_image.height,
            1.0  # Don't scale up initially
        )
        
        # Create main frame (expandable)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top controls frame (horizontal layout for better space usage)
        top_controls = ttk.Frame(main_frame)
        top_controls.pack(fill=tk.X, pady=(0, 10))
        
        # Zoom controls frame
        zoom_frame = ttk.LabelFrame(top_controls, text="Zoom Controls")
        zoom_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(zoom_frame, text="Fit to Window", command=self.fit_to_window).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(zoom_frame, text="Actual Size", command=self.actual_size).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Zoom level display
        self.zoom_label = ttk.Label(zoom_frame, text=f"Zoom: {self.zoom_level:.1f}x")
        self.zoom_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Zoom slider
        self.zoom_var = tk.DoubleVar(value=self.zoom_level)
        zoom_slider = ttk.Scale(zoom_frame, from_=0.1, to=5.0, variable=self.zoom_var, 
                               orient=tk.HORIZONTAL, length=200, command=self.on_zoom_slider)
        zoom_slider.pack(side=tk.LEFT, padx=5, pady=5)
        
        # GUI Scale controls frame
        gui_frame = ttk.LabelFrame(top_controls, text="Interface Scale")
        gui_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.gui_scale = tk.DoubleVar(value=1.0)
        ttk.Label(gui_frame, text="GUI:").pack(side=tk.LEFT, padx=5, pady=5)
        gui_scale_slider = ttk.Scale(gui_frame, from_=0.8, to=2.0, variable=self.gui_scale,
                                    orient=tk.HORIZONTAL, length=120, command=self.on_gui_scale)
        gui_scale_slider.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.gui_scale_label = ttk.Label(gui_frame, text="1.0x")
        self.gui_scale_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Image canvas with scrollbars (expandable)
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, width=self.max_canvas_width, height=self.max_canvas_height, 
                               scrollregion=(0, 0, 0, 0), bg='gray90')
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind canvas resize event
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Mouse selection variables
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.panning = False
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Button-3>", self.start_pan)  # Right click to pan
        self.canvas.bind("<B3-Motion>", self.do_pan)
        self.canvas.bind("<ButtonRelease-3>", self.end_pan)
        
        # Bind keyboard events for corner fine-tuning
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()  # Allow root to receive key events
        
        # Control frame - horizontal layout for better space usage
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Left controls (coordinates and fine-tuning side by side)
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Manual input frame
        manual_frame = ttk.LabelFrame(left_controls, text="Manual Coordinates (pixels)")
        manual_frame.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 10))
        
        ttk.Label(manual_frame, text="Left:").grid(row=0, column=0, padx=5, pady=5)
        self.left_var = tk.StringVar()
        self.left_entry = ttk.Entry(manual_frame, textvariable=self.left_var, width=8)
        self.left_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Top:").grid(row=0, column=2, padx=5, pady=5)
        self.top_var = tk.StringVar()
        self.top_entry = ttk.Entry(manual_frame, textvariable=self.top_var, width=8)
        self.top_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Right:").grid(row=1, column=0, padx=5, pady=5)
        self.right_var = tk.StringVar()
        self.right_entry = ttk.Entry(manual_frame, textvariable=self.right_var, width=8)
        self.right_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(manual_frame, text="Bottom:").grid(row=1, column=2, padx=5, pady=5)
        self.bottom_var = tk.StringVar()
        self.bottom_entry = ttk.Entry(manual_frame, textvariable=self.bottom_var, width=8)
        self.bottom_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(manual_frame, text="Apply", command=self.apply_manual_coords).grid(row=0, column=4, rowspan=2, padx=10, pady=5)
        
        # Fine-tune frame
        finetune_frame = ttk.LabelFrame(left_controls, text="Fine-Tune Corner")
        finetune_frame.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 10))
        
        # Corner selection
        ttk.Label(finetune_frame, text="Corner:").grid(row=0, column=0, padx=5, pady=5)
        self.selected_corner = tk.StringVar(value="top-left")
        corner_combo = ttk.Combobox(finetune_frame, textvariable=self.selected_corner, 
                                   values=["top-left", "top-right", "bottom-left", "bottom-right"],
                                   state="readonly", width=10)
        corner_combo.grid(row=0, column=1, padx=5, pady=5)
        corner_combo.bind("<<ComboboxSelected>>", lambda e: self.on_corner_changed())
        
        # Step size
        ttk.Label(finetune_frame, text="Step:").grid(row=1, column=0, padx=5, pady=5)
        self.step_size = tk.IntVar(value=1)
        step_spin = ttk.Spinbox(finetune_frame, from_=1, to=10, textvariable=self.step_size, width=5)
        step_spin.grid(row=1, column=1, padx=5, pady=5)
        
        # Arrow buttons (compact layout)
        button_frame = ttk.Frame(finetune_frame)
        button_frame.grid(row=0, column=2, rowspan=2, padx=20, pady=5)
        
        ttk.Button(button_frame, text="↑", command=lambda: self.move_corner("up"), width=3).grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(button_frame, text="←", command=lambda: self.move_corner("left"), width=3).grid(row=1, column=0, padx=1, pady=1)
        ttk.Button(button_frame, text="→", command=lambda: self.move_corner("right"), width=3).grid(row=1, column=2, padx=1, pady=1)
        ttk.Button(button_frame, text="↓", command=lambda: self.move_corner("down"), width=3).grid(row=2, column=1, padx=1, pady=1)
        
        # Info frame
        info_frame = ttk.LabelFrame(control_frame, text="Current Selection")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="Draw a rectangle or enter coordinates manually")
        self.info_label.pack(pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Use This Crop Box", command=self.confirm_selection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.root.quit).pack(side=tk.RIGHT)
        
        # Instructions (more compact layout)
        inst_frame = ttk.Frame(main_frame)
        inst_frame.pack(fill=tk.X, pady=(10, 0))
        
        instructions = ttk.Label(inst_frame, 
            text=f"Instructions: Left-click+drag: Draw rectangle • Right-click+drag: Pan • Arrow keys: Fine-tune corner • Resize window for larger view\nImage size: {self.original_image.width}x{self.original_image.height} pixels",
            justify=tk.LEFT)
        instructions.pack(side=tk.LEFT)
        
        self.crop_box = None
        self.current_selection_canvas = None
        self.corner_indicators = []  # For visual corner highlighting
        self.auto_fit_on_resize = False  # Toggle for auto-fit on window resize
        
        # Set minimum window size
        self.root.minsize(900, 600)
        
        # Initialize display image after all UI elements are created
        self.update_display_image()
        
    def update_display_image(self):
        """Update the display image based on current zoom and pan"""
        effective_scale = self.base_scale * self.zoom_level
        new_width = int(self.original_image.width * effective_scale)
        new_height = int(self.original_image.height * effective_scale)
        
        self.display_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.display_image)
        
        # Update canvas (only if canvas exists)
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
        
        # Update zoom label (only if it exists)
        if hasattr(self, 'zoom_label'):
            self.zoom_label.config(text=f"Zoom: {self.zoom_level:.1f}x")
        
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to original image coordinates"""
        # Convert canvas coordinates to scrolled canvas coordinates
        scroll_x = self.canvas.canvasx(canvas_x)
        scroll_y = self.canvas.canvasy(canvas_y)
        
        # Convert to original image coordinates
        effective_scale = self.base_scale * self.zoom_level
        img_x = int(scroll_x / effective_scale)
        img_y = int(scroll_y / effective_scale)
        
        # Clamp to image bounds
        img_x = max(0, min(img_x, self.original_image.width))
        img_y = max(0, min(img_y, self.original_image.height))
        
        return img_x, img_y
    
    def image_to_canvas_coords(self, img_x, img_y):
        """Convert original image coordinates to canvas coordinates"""
        effective_scale = self.base_scale * self.zoom_level
        canvas_x = img_x * effective_scale
        canvas_y = img_y * effective_scale
        return canvas_x, canvas_y
    
    def zoom_in(self):
        self.zoom_level = min(self.zoom_level * 1.25, 5.0)
        self.zoom_var.set(self.zoom_level)
        self.update_display_image()
        self.redraw_selection()
    
    def zoom_out(self):
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        self.zoom_var.set(self.zoom_level)
        self.update_display_image()
        self.redraw_selection()
    
    def fit_to_window(self):
        # Fit image to current window size - this should bypass base scale to show actual pixels
        self.zoom_level = 1.0 / self.base_scale
        self.zoom_var.set(self.zoom_level)
        self.update_display_image()
        self.redraw_selection()
    
    def actual_size(self):
        # Show image at actual pixel size - this should use base scale (1.0 zoom relative to fitted size)
        self.zoom_level = 1.0
        self.zoom_var.set(self.zoom_level)
        self.update_display_image()
        self.redraw_selection()
    
    def on_zoom_slider(self, value):
        self.zoom_level = float(value)
        self.update_display_image()
        self.redraw_selection()
    
    
    def redraw_selection(self):
        """Redraw the current selection rectangle at the new zoom level"""
        if self.crop_box and len(self.crop_box) == 4:
            left, top, right, bottom = self.crop_box
            canvas_left, canvas_top = self.image_to_canvas_coords(left, top)
            canvas_right, canvas_bottom = self.image_to_canvas_coords(right, bottom)
            
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            
            self.rect_id = self.canvas.create_rectangle(
                canvas_left, canvas_top, canvas_right, canvas_bottom,
                outline="red", width=2
            )
            
            # Also highlight the selected corner
            self.highlight_selected_corner()
    
    def on_mouse_down(self, event):
        # Don't start selection if we're in pan mode or right-clicking
        if self.panning:
            return
        
        # Store the canvas coordinates where selection started
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def on_mouse_drag(self, event):
        if self.panning:
            return
            
        if self.start_x is None or self.start_y is None:
            return
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # Get current canvas coordinates 
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        
        # Draw rectangle using canvas coordinates
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, current_x, current_y,
            outline="red", width=2
        )
        
        # Convert to image coordinates for display (now using corrected coordinate system)
        effective_scale = self.base_scale * self.zoom_level
        
        start_img_x = int(self.start_x / effective_scale)
        start_img_y = int(self.start_y / effective_scale)
        end_img_x = int(current_x / effective_scale)
        end_img_y = int(current_y / effective_scale)
        
        left = min(start_img_x, end_img_x)
        top = min(start_img_y, end_img_y)
        right = max(start_img_x, end_img_x)
        bottom = max(start_img_y, end_img_y)
        
        # Clamp to image bounds
        left = max(0, min(left, self.original_image.width))
        top = max(0, min(top, self.original_image.height))
        right = max(0, min(right, self.original_image.width))
        bottom = max(0, min(bottom, self.original_image.height))
        
        width = right - left
        height = bottom - top
        
        self.info_label.config(text=f"Selection: ({left}, {top}, {right}, {bottom}) - Size: {width}x{height} pixels")
        
        # Update manual input fields
        self.left_var.set(str(left))
        self.top_var.set(str(top))
        self.right_var.set(str(right))
        self.bottom_var.set(str(bottom))
        
        # Update info display to show selected corner
        corner = self.selected_corner.get()
        self.info_label.config(text=f"Selection: ({left}, {top}, {right}, {bottom}) - Size: {width}x{height} pixels - Corner: {corner}")
    
    def on_mouse_release(self, event):
        if self.panning:
            return
            
        if self.start_x is not None and self.start_y is not None:
            # Get final canvas coordinates
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            
            # Convert to image coordinates
            effective_scale = self.base_scale * self.zoom_level
            
            start_img_x = int(self.start_x / effective_scale)
            start_img_y = int(self.start_y / effective_scale)
            end_img_x = int(current_x / effective_scale)
            end_img_y = int(current_y / effective_scale)
            
            left = min(start_img_x, end_img_x)
            top = min(start_img_y, end_img_y)
            right = max(start_img_x, end_img_x)
            bottom = max(start_img_y, end_img_y)
            
            # Clamp to image bounds
            left = max(0, min(left, self.original_image.width))
            top = max(0, min(top, self.original_image.height))
            right = max(0, min(right, self.original_image.width))
            bottom = max(0, min(bottom, self.original_image.height))
            
            self.crop_box = (left, top, right, bottom)
            
            # Show corner highlight and update display
            self.update_selection_display()
            self.highlight_selected_corner()
    
    def start_pan(self, event):
        self.panning = True
        # Mark the starting point for panning
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")
    
    def do_pan(self, event):
        if not self.panning:
            return
        
        # Use scan_dragto with the current mouse position
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def end_pan(self, event):
        self.panning = False
        self.canvas.configure(cursor="")
    
    def apply_manual_coords(self):
        try:
            left = int(self.left_var.get())
            top = int(self.top_var.get())
            right = int(self.right_var.get())
            bottom = int(self.bottom_var.get())
            
            # Validate coordinates
            if left >= right or top >= bottom:
                messagebox.showerror("Error", "Invalid coordinates: right must be > left, bottom must be > top")
                return
            
            if left < 0 or top < 0 or right > self.original_image.width or bottom > self.original_image.height:
                messagebox.showerror("Error", f"Coordinates must be within image bounds (0, 0, {self.original_image.width}, {self.original_image.height})")
                return
            
            # Clear existing rectangle
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            
            # Draw new rectangle
            canvas_left, canvas_top = self.image_to_canvas_coords(left, top)
            canvas_right, canvas_bottom = self.image_to_canvas_coords(right, bottom)
            
            self.rect_id = self.canvas.create_rectangle(
                canvas_left, canvas_top, canvas_right, canvas_bottom,
                outline="red", width=2
            )
            
            width = right - left
            height = bottom - top
            
            self.crop_box = (left, top, right, bottom)
            
            # Update display and show corner highlight
            self.update_selection_display()
            self.highlight_selected_corner()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer coordinates")
    
    def clear_selection(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        
        # Clear corner indicators
        for indicator in self.corner_indicators:
            self.canvas.delete(indicator)
        self.corner_indicators.clear()
        
        self.left_var.set("")
        self.top_var.set("")
        self.right_var.set("")
        self.bottom_var.set("")
        
        self.info_label.config(text="Draw a rectangle or enter coordinates manually")
        self.crop_box = None
    
    def confirm_selection(self):
        if self.crop_box is None:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return
        
        result = messagebox.askyesno("Confirm", 
            f"Use crop box {self.crop_box}?\n\nThis will update your pic-bulk-crop.py file.")
        
        if result:
            self.update_crop_script()
            messagebox.showinfo("Success", 
                f"Updated pic-bulk-crop.py with crop_box = {self.crop_box}")
            self.root.quit()
    
    def update_crop_script(self):
        # Read the current script
        with open('pic-bulk-crop.py', 'r') as f:
            content = f.read()
        
        # Replace the crop_box line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'crop_box =' in line:
                lines[i] = f"crop_box = {self.crop_box}  # (left, upper, right, lower)"
                break
        
        # Write back
        with open('pic-bulk-crop.py', 'w') as f:
            f.write('\n'.join(lines))
    
    def on_key_press(self, event):
        """Handle arrow key presses for fine-tuning corners"""
        if self.crop_box is None:
            return
        
        if event.keysym in ['Up', 'Down', 'Left', 'Right']:
            direction_map = {
                'Up': 'up',
                'Down': 'down', 
                'Left': 'left',
                'Right': 'right'
            }
            self.move_corner(direction_map[event.keysym])
    
    def move_corner(self, direction):
        """Move the selected corner in the specified direction"""
        if self.crop_box is None:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return
        
        left, top, right, bottom = self.crop_box
        step = self.step_size.get()
        corner = self.selected_corner.get()
        
        # Apply movement based on selected corner and direction
        if corner == "top-left":
            if direction == "left":
                left = max(0, left - step)
            elif direction == "right":
                left = min(right - 1, left + step)
            elif direction == "up":
                top = max(0, top - step)
            elif direction == "down":
                top = min(bottom - 1, top + step)
        
        elif corner == "top-right":
            if direction == "left":
                right = max(left + 1, right - step)
            elif direction == "right":
                right = min(self.original_image.width, right + step)
            elif direction == "up":
                top = max(0, top - step)
            elif direction == "down":
                top = min(bottom - 1, top + step)
        
        elif corner == "bottom-left":
            if direction == "left":
                left = max(0, left - step)
            elif direction == "right":
                left = min(right - 1, left + step)
            elif direction == "up":
                bottom = max(top + 1, bottom - step)
            elif direction == "down":
                bottom = min(self.original_image.height, bottom + step)
        
        elif corner == "bottom-right":
            if direction == "left":
                right = max(left + 1, right - step)
            elif direction == "right":
                right = min(self.original_image.width, right + step)
            elif direction == "up":
                bottom = max(top + 1, bottom - step)
            elif direction == "down":
                bottom = min(self.original_image.height, bottom + step)
        
        # Update crop box
        self.crop_box = (left, top, right, bottom)
        
        # Update UI
        self.update_selection_display()
        self.redraw_selection()
        self.highlight_selected_corner()
    
    def update_selection_display(self):
        """Update the coordinate fields and info label"""
        if self.crop_box is None:
            return
        
        left, top, right, bottom = self.crop_box
        width = right - left
        height = bottom - top
        
        # Update manual input fields
        self.left_var.set(str(left))
        self.top_var.set(str(top))
        self.right_var.set(str(right))
        self.bottom_var.set(str(bottom))
        
        # Update info label
        corner = self.selected_corner.get()
        self.info_label.config(text=f"Selection: ({left}, {top}, {right}, {bottom}) - Size: {width}x{height} pixels - Corner: {corner}")
    
    def highlight_selected_corner(self):
        """Add visual indicator for the selected corner"""
        # Clear existing corner indicators
        for indicator in self.corner_indicators:
            self.canvas.delete(indicator)
        self.corner_indicators.clear()
        
        if self.crop_box is None:
            return
        
        left, top, right, bottom = self.crop_box
        corner = self.selected_corner.get()
        
        # Convert to canvas coordinates
        canvas_left, canvas_top = self.image_to_canvas_coords(left, top)
        canvas_right, canvas_bottom = self.image_to_canvas_coords(right, bottom)
        
        # Determine which corner to highlight
        corner_coords = {
            "top-left": (canvas_left, canvas_top),
            "top-right": (canvas_right, canvas_top),
            "bottom-left": (canvas_left, canvas_bottom),
            "bottom-right": (canvas_right, canvas_bottom)
        }
        
        if corner in corner_coords:
            x, y = corner_coords[corner]
            # Draw a small circle to indicate the selected corner
            size = 6
            indicator = self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill="yellow", outline="orange", width=2
            )
            self.corner_indicators.append(indicator)

    def on_corner_changed(self):
        """Called when user changes the selected corner"""
        self.highlight_selected_corner()
        if self.crop_box:
            self.update_selection_display()
    
    def on_gui_scale(self, value):
        """Handle GUI scaling changes"""
        scale = float(value)
        self.gui_scale_label.config(text=f"{scale:.1f}x")
        
        # Apply font scaling
        font_size = int(9 * scale)  # Base font size 9
        style = ttk.Style()
        style.configure(".", font=("TkDefaultFont", font_size))
        
        # Update button sizes
        for widget in self.root.winfo_children():
            self.apply_scale_to_widget(widget, scale)
    
    def apply_scale_to_widget(self, widget, scale):
        """Recursively apply scaling to widgets"""
        try:
            # Scale widget padding if it has it
            if hasattr(widget, 'configure'):
                current_config = widget.configure()
                if 'padx' in current_config:
                    try:
                        padx = int(current_config['padx'][4])
                        widget.configure(padx=int(padx * scale))
                    except:
                        pass
                if 'pady' in current_config:
                    try:
                        pady = int(current_config['pady'][4])
                        widget.configure(pady=int(pady * scale))
                    except:
                        pass
            
            # Recursively apply to children
            for child in widget.winfo_children():
                self.apply_scale_to_widget(child, scale)
        except:
            pass
    
    def on_canvas_resize(self, event):
        """Handle canvas resize events"""
        # Update canvas size variables for better fitting
        if event.widget == self.canvas:
            self.max_canvas_width = event.width
            self.max_canvas_height = event.height
            
            # Optionally auto-fit image when canvas is resized
            if hasattr(self, 'auto_fit_on_resize') and self.auto_fit_on_resize:
                self.fit_to_window()
    
    def run(self):
        self.root.mainloop()

def main():
    input_folder = 'pic-input'
    
    # Find the first image
    image_files = [f for f in os.listdir(input_folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    if not image_files:
        print("No image files found in pic-input folder!")
        return
    
    first_image = os.path.join(input_folder, sorted(image_files)[0])
    print(f"Opening first image: {first_image}")
    
    selector = CropSelector(first_image)
    selector.run()

if __name__ == "__main__":
    main() 