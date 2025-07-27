from __future__ import annotations
import pdata.pdata
import glob
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Tuple

from PIL import Image, ImageTk


IMAGE_EXTS = (".png", ".jpg")
GRID_DIVISIONS = 75

# Pre‑defined annotation boxes: (label, UL‑grid‑coord, LR‑grid‑coord, colour, dashed?)
PREDEFINED_BOXES = [
    ("Face", (2, 3), (10, 12), "yellow", False),
    ("License Plate", (12,14), (18, 18), "red", True),
    ("Logo", (1, 17), (6, 19), "cyan", False),
]

class ImageGridViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Grid Viewer")
        self.geometry("1000x1000")

        # internal list of drawn quests
        self._box_ids: List[int] = []

        # map selector
        top = ttk.Frame(self); top.pack(side="top", fill="x", padx=6, pady=4)
        self.path_var = tk.StringVar()
        self.cmb = ttk.Combobox(top, textvariable=self.path_var, state="readonly", postcommand=self.update_file_list, width=60)
        self.cmb.bind("<<ComboboxSelected>>", lambda *_: self.load_image())
        self.cmb.pack(side="left", fill="x", expand=True, padx=4)

        main_pane = ttk.Panedwindow(self, orient="horizontal"); main_pane.pack(fill="both", expand=True)

        # Canvas for map and quests
        self.canvas = tk.Canvas(main_pane, highlightthickness=0, bg="black")
        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<Button-1>", self.on_click)
        main_pane.add(self.canvas, weight=4)

        # quest selector
        side = ttk.Frame(main_pane, padding=6)
        ttk.Label(side, text="Quests", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.box_vars: List[tk.BooleanVar] = []
        for idx, (label, *_ , colour, _dashed) in enumerate(PREDEFINED_BOXES):
            style_name = f"Box{idx}.TCheckbutton"
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(side, text=label, variable=var, style=style_name, command=self.draw_selected_quests)
            cb.pack(anchor="w", pady=1, fill="x")
            self.box_vars.append(var)
        main_pane.add(side, weight=1)

        # image attributes
        self.image_dir = f"{os.getcwd()}/maps"
        self.images: List[str] = []
        self.orig_im: Image.Image | None = None
        self.tk_im: ImageTk.PhotoImage | None = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def update_file_list(self):
        self.images = [f for f in glob.glob(os.path.join(self.image_dir, "*")) if f.lower().endswith(IMAGE_EXTS)]
        self.cmb["values"] = [os.path.basename(f) for f in self.images]
        if not self.images:
            messagebox.showinfo("No images", f"No image files found in {self.image_dir}")
            self.orig_im = None
            self.canvas.delete("all")

    def load_image(self):
        idx = self.cmb.current()
        if idx < 0:
            return
        path = self.images[idx]
        try:
            self.orig_im = Image.open(path).convert("RGBA")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not load image:\n{exc}")
            return
        self.redraw()

    def redraw(self, *_):
        """Redraw image, grid, and any selected boxes."""
        if self.orig_im is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        iw, ih = self.orig_im.size
        self.scale = min(cw / iw, ch / ih)
        disp_w, disp_h = int(iw * self.scale), int(ih * self.scale)
        resized = self.orig_im.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_im = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.offset_x = (cw - disp_w) // 2
        self.offset_y = (ch - disp_h) // 2
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_im)
        self.draw_grid(disp_w, disp_h)
        self.draw_selected_quests()

    def draw_grid(self, disp_w: int, disp_h: int): #Remove after quests are added
        step_x = disp_w / GRID_DIVISIONS
        step_y = disp_h / GRID_DIVISIONS
        for i in range(1, GRID_DIVISIONS):
            x = self.offset_x + int(i * step_x)
            self.canvas.create_line(x, self.offset_y, x, self.offset_y + disp_h, fill="#00ff00", dash=(2, 2))
        for j in range(1, GRID_DIVISIONS):
            y = self.offset_y + int(j * step_y)
            self.canvas.create_line(self.offset_x, y, self.offset_x + disp_w, y, fill="#00ff00", dash=(2, 2))

    def _grid_to_canvas(self, gx: int, gy: int) -> Tuple[float, float]:
        cell_w = self.orig_im.width / GRID_DIVISIONS
        cell_h = self.orig_im.height / GRID_DIVISIONS
        return (self.offset_x + gx * cell_w * self.scale,
                self.offset_y + gy * cell_h * self.scale)

    def draw_quest(self, ul: Tuple[int, int], lr: Tuple[int, int], *,
                 color: str, dashed: bool, width: int = 2, tag: str = "box") -> int:
        x1, y1 = self._grid_to_canvas(*ul)
        x2, y2 = self._grid_to_canvas(*lr)
        opts = {"outline": color, "width": width, "tags": tag}
        if dashed:
            opts["dash"] = (4, 4)
        return self.canvas.create_rectangle(x1, y1, x2, y2, **opts)

    def draw_selected_quests(self):
        self.canvas.delete("box")
        self._box_ids.clear()
        if self.orig_im is None:
            return
        for idx, var in enumerate(self.box_vars):
            if var.get():
                label, ul, lr, colour, dashed = PREDEFINED_BOXES[idx]
                rid = self.draw_box(ul, lr, color=colour, dashed=dashed)
                self._box_ids.append(rid)

    # get muh coords
    def on_click(self,event):
        if self.orig_im is None: return
        x_c, y_c = event.x - self.offset_x, event.y - self.offset_y
        if not (0 <= x_c < self.tk_im.width() and 0 <= y_c < self.tk_im.height()): return
        img_x, img_y = x_c / self.scale, y_c / self.scale
        cell_w, cell_h = self.orig_im.width/GRID_DIVISIONS, self.orig_im.height/GRID_DIVISIONS
        grid_x, grid_y = round(img_x / cell_w), round(img_y / cell_h)
        print(f"{grid_x}, {grid_y}")
        r=3; self.canvas.create_line(event.x-r,event.y,event.x+r,event.y, fill="red", width=2, tags="clickmarker")
        self.canvas.create_line(event.x,event.y-r,event.x,event.y+r, fill="red", width=2, tags="clickmarker"); self.canvas.tag_raise("clickmarker")
        self.canvas.tag_raise("clickmarker")


if __name__ == "__main__":
    ImageGridViewer().mainloop()
