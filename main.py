## TO DO
# have objective boxes change color based on quest type
from __future__ import annotations
import pdata.pdata as p
import glob
import os
import tkinter as tk
from tkinter import messagebox, ttk, font as tkfont
from typing import List, Tuple, Dict

from PIL import Image, ImageTk


IMAGE_EXTS = (".png", ".jpg")
GRID_DIVISIONS = 75

class QuestViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tarkov Quest Viewer")
        self.geometry("1000x1000")

        self.player = p.PlayerData()

        # map selector
        top = ttk.Frame(self)
        top.pack(side="top", fill="x", padx=6, pady=4)
        self.path_var = tk.StringVar()
        self.cmb = ttk.Combobox(top, textvariable=self.path_var, state="readonly", postcommand=self.update_file_list, width=60)
        self.cmb.bind("<<ComboboxSelected>>", lambda *_: self.load_image())
        self.cmb.pack(side="left", fill="x", expand=True, padx=4)

        main_pane = ttk.Panedwindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        # canvas for map and quests
        self.canvas = tk.Canvas(main_pane, highlightthickness=0, bg="black")
        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<Button-1>", self.on_click)
        main_pane.add(self.canvas, weight=4)

        # quest selector
        side = ttk.Frame(main_pane, padding=6)
        main_pane.add(side, weight=2)
        self.group_chk_frame = ttk.Frame(side)
        self.group_chk_frame.pack(anchor="w", fill="x")
        self.tree = ttk.Treeview(side, show="tree", selectmode="none")
        self.tree.pack(fill="both", expand=True, pady=(4, 0))
        done_font = tkfont.Font(font="TkDefaultFont")
        done_font.configure(overstrike=1)
        self.tree.tag_configure("done", font=done_font)

        self.image_dir: str = f"{os.getcwd()}/maps"
        self.images: List[str] = []
        self.orig_im: Image.Image | None = None
        self.tk_im: ImageTk.PhotoImage | None = None
        self.scale: float = 1.0
        self.offset_x = self.offset_y = 0

        self.box_groups: Dict[str, list] = {}
        self.group_vars: Dict[str, tk.BooleanVar] = {}
        self._box_ids: List[int] = []


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
        # Update objectives
        base = os.path.splitext(os.path.basename(path))[0]
        self.ingest_boxes(self.update_quests(base))
        self.redraw()

    def ingest_boxes(self, box_list: list):

        # Structure objectives by parent
        self.box_groups.clear()
        for parent, desc, ul, lr, done in box_list:
            self.box_groups.setdefault(parent, []).append({
                "desc": desc,
                "ul":   tuple(ul),
                "lr":   tuple(lr),
                "done": bool(done),
            })
        # Rebuild objective checkboxes
        for w in self.group_chk_frame.winfo_children():
            w.destroy()
        self.group_vars.clear()
        for parent in sorted(self.box_groups.keys()):
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.group_chk_frame, text=parent, variable=var, command=self.redraw_boxes)
            chk.pack(anchor="w")
            self.group_vars[parent] = var
        # Rebuild tree view
        self.tree.delete(*self.tree.get_children())
        for parent in sorted(self.box_groups.keys()):
            pid = self.tree.insert("", "end", text=parent, open=False)
            for item in self.box_groups[parent]:
                tags = ("done",) if item["done"] else ()
                self.tree.insert(pid, "end", text=item["desc"], tags=tags)

    def redraw(self, *_):
        if self.orig_im is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        iw, ih = self.orig_im.size
        self.scale = min(cw / iw, ch / ih)
        disp_w, disp_h = int(iw * self.scale), int(ih * self.scale)
        self.tk_im = ImageTk.PhotoImage(self.orig_im.resize((disp_w, disp_h), Image.LANCZOS))
        self.canvas.delete("all")
        self.offset_x = (cw - disp_w) // 2
        self.offset_y = (ch - disp_h) // 2
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.tk_im)
        self.draw_grid(disp_w, disp_h)
        self.redraw_boxes()

    def draw_grid(self, w: int, h: int):
        sx, sy = w / GRID_DIVISIONS, h / GRID_DIVISIONS
        for i in range(1, GRID_DIVISIONS):
            x = self.offset_x + int(i * sx)
            self.canvas.create_line(x, self.offset_y, x, self.offset_y + h, fill="#00ff00", dash=(2, 2))
        for j in range(1, GRID_DIVISIONS):
            y = self.offset_y + int(j * sy)
            self.canvas.create_line(self.offset_x, y, self.offset_x + w, y, fill="#00ff00", dash=(2, 2))

    def _grid_to_canvas(self, gx: int, gy: int) -> Tuple[float, float]:
        cell_w = self.orig_im.width  / GRID_DIVISIONS
        cell_h = self.orig_im.height / GRID_DIVISIONS
        return self.offset_x + gx * cell_w * self.scale, self.offset_y + gy * cell_h * self.scale

    def redraw_boxes(self):
        self.canvas.delete("box")
        if self.orig_im is None:
            return
        for parent, items in self.box_groups.items():
            if not self.group_vars[parent].get():
                continue  # group disabled
            for item in items:
                if item["done"]:
                    continue  # skip finished boxes
                ul = item["ul"]
                lr = item["lr"]
                if ul == lr:
                    continue  # zero‑size, nothing to draw
                self.draw_box(ul, lr, color="yellow", dashed=False)

    def draw_box(self, ul: Tuple[int, int], lr: Tuple[int, int], *, color: str, dashed: bool, tag: str = "box"):
        x1, y1 = self._grid_to_canvas(*ul)
        x2, y2 = self._grid_to_canvas(*lr)
        opts = {"outline": color, "width": 2, "tags": tag}
        if dashed:
            opts["dash"] = (4, 4)
        self.canvas.create_rectangle(x1, y1, x2, y2, **opts)

    def on_click(self, event):
        if self.orig_im is None:
            return
        x_c = event.x - self.offset_x
        y_c = event.y - self.offset_y
        if not (0 <= x_c < self.tk_im.width() and 0 <= y_c < self.tk_im.height()):
            return
        img_x, img_y = x_c / self.scale, y_c / self.scale
        cell_w = self.orig_im.width  / GRID_DIVISIONS
        cell_h = self.orig_im.height / GRID_DIVISIONS
        grid_x, grid_y = round(img_x / cell_w), round(img_y / cell_h)
        print(f"({grid_x}, {grid_y})")
        r = 3
        self.canvas.create_line(event.x - r, event.y, event.x + r, event.y, fill="red", width=2, tags="clickmarker")
        self.canvas.create_line(event.x, event.y - r, event.x, event.y + r, fill="red", width=2, tags="clickmarker")
        self.canvas.tag_raise("clickmarker")

    def update_quests(self, map):
        active_objectives = []
        objectives = self.player.get_objectives_on_map(map)
        for objective in objectives:
            active_objectives.append((objective[0], # parent quest name
                                      self.objective_to_description(objective), # generated description
                                      objective[1].get("LocationBoxTopLeft"), # top left grid box coordinate
                                      objective[1].get("LocationBoxBottomRight"), # bottom right grid box coordinate
                                      objective[2])) # Whether or not this objective is completed

        return(active_objectives)

    def objective_to_description(self, objective):
        description = ""

        if(objective[1].get("Type") == "elimination"):
            description = description + "Eliminate "
        elif(objective[1].get("Type") == "fetch" or "gather"):
            description = description + "Find "
        elif(objective[1].get("Type") == "scout"):
            description = description + "Go to "
        elif(objective[1].get("Type") == "stash"):
            description = description + "Place "
        
        if(objective[1].get("Amount") > 0):
            description = description + f"{objective[1].get("Amount")} "

        if(objective[1].get("Amount") > 1):
            description = description + f"{objective[1].get("Target")}s"
        else:
            description = description + f"{objective[1].get("Target")}"

        if(objective[1].get("Time")[0] != objective[1].get("Time")[1]):
            description = description + f" between {objective[1].get("Time")[0]} and {objective[1].get("Time")[1]}"

        if(not objective[1].get("Required")):
            description = description + " (optional)"

        return(description)

if __name__ == "__main__":
    QuestViewer().mainloop()