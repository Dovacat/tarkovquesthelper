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
GRID_DIVISIONS = 100

STATUS_COLORS = {
    "inactive": "#808080",
    "active": "#dcae00",
    "completed": "#008000",
}


class QuestViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tarkov Quest Viewer")
        self.geometry("1000x1000")
        self._build_ui()
        self._init_state()
        self.update_file_list()
        self.player = p.PlayerData()
        self.current_map = ""

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=4)
        self.path_var = tk.StringVar()
        self.cmb = ttk.Combobox(
            top,
            textvariable=self.path_var,
            state="readonly",
            postcommand=self.update_file_list,
            width=50,
        )
        self.cmb.bind("<<ComboboxSelected>>", lambda *_: self.load_image())
        self.cmb.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(top, text="Manage Quests", command=self.open_group_manager).pack(
            side="left", padx=4
        )
        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main, bg="black", highlightthickness=0)
        self.canvas.bind("<Configure>", self.redraw)
        self.canvas.bind("<Button-1>", self.on_click)
        main.add(self.canvas, weight=4)
        side = ttk.Frame(main, padding=6)
        main.add(side, weight=2)
        self.group_chk_frame = ttk.Frame(side)
        self.group_chk_frame.pack(anchor="w", fill="x")
        self.tree = ttk.Treeview(side, show="tree", selectmode="none")
        self.tree.pack(fill="both", expand=True, pady=(4, 0))
        done_font = tkfont.Font(font="TkDefaultFont")
        done_font.configure(overstrike=1)
        self.tree.tag_configure("done", font=done_font)

    def _init_state(self):
        self.image_dir = f"{os.getcwd()}/maps"
        self.images: List[str] = []
        self.orig_im: Image.Image | None = None
        self.tk_im: ImageTk.PhotoImage | None = None
        self.scale = 1.0
        self.offset_x = self.offset_y = 0
        self.box_groups: Dict[str, list] = {}
        self.group_vars: Dict[str, tk.BooleanVar] = {}

    def update_file_list(self):
        self.images = [
            p
            for p in glob.glob(os.path.join(self.image_dir, "*"))
            if p.lower().endswith(IMAGE_EXTS)
        ]
        self.cmb["values"] = [os.path.basename(p) for p in self.images]
        if not self.images:
            messagebox.showinfo("No images", f"No images found in {self.image_dir}")
            self.orig_im = None
            self.canvas.delete("all")

    def load_image(self):
        idx = self.cmb.current()
        if idx < 0:
            return
        path = self.images[idx]
        try:
            self.orig_im = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.current_map = os.path.splitext(os.path.basename(path))[0]
        self.ingest_boxes(self.update_quests(self.current_map))
        self.redraw()

    def ingest_boxes(self, raw: list):
        self.box_groups.clear()
        for parent, desc, ul, lr, done in raw:
            self.box_groups.setdefault(parent, []).append(
                dict(desc=desc, ul=tuple(ul), lr=tuple(lr), done=bool(done))
            )
        for w in self.group_chk_frame.winfo_children():
            w.destroy()
            self.group_vars.clear()
        for parent in sorted(self.box_groups):
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                self.group_chk_frame,
                text=parent,
                variable=var,
                command=self.redraw_boxes,
            ).pack(anchor="w")
            self.group_vars[parent] = var
        self._rebuild_tree()

    def _rebuild_tree(self):
        self.tree.delete(*self.tree.get_children())
        for parent in sorted(self.box_groups):
            pid = self.tree.insert("", "end", text=parent, open=False)
            for itm in self.box_groups[parent]:
                self.tree.insert(
                    pid, "end", text=itm["desc"], tags=("done",) if itm["done"] else ()
                )

    def redraw(self, *_):
        if not self.orig_im:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        iw, ih = self.orig_im.size
        self.scale = min(cw / iw, ch / ih)
        disp = (int(iw * self.scale), int(ih * self.scale))
        self.tk_im = ImageTk.PhotoImage(self.orig_im.resize(disp, Image.LANCZOS))
        self.canvas.delete("all")
        self.offset_x = (cw - disp[0]) // 2
        self.offset_y = (ch - disp[1]) // 2
        self.canvas.create_image(
            self.offset_x, self.offset_y, anchor="nw", image=self.tk_im
        )
        self._draw_grid(*disp)
        self.redraw_boxes()

    def _draw_grid(self, w: int, h: int):
        sx, sy = w / GRID_DIVISIONS, h / GRID_DIVISIONS
        for i in range(1, GRID_DIVISIONS):
            x = self.offset_x + int(i * sx)
            self.canvas.create_line(
                x, self.offset_y, x, self.offset_y + h, fill="#00ff00", dash=(2, 2)
            )
        for j in range(1, GRID_DIVISIONS):
            y = self.offset_y + int(j * sy)
            self.canvas.create_line(
                self.offset_x, y, self.offset_x + w, y, fill="#00ff00", dash=(2, 2)
            )

    def _grid_to_canvas(self, gx: int, gy: int) -> Tuple[float, float]:
        cw, ch = (
            self.orig_im.width / GRID_DIVISIONS,
            self.orig_im.height / GRID_DIVISIONS,
        )
        return (
            self.offset_x + gx * cw * self.scale,
            self.offset_y + gy * ch * self.scale,
        )

    def redraw_boxes(self):
        self.canvas.delete("box")
        if not self.orig_im:
            return
        for parent, items in self.box_groups.items():
            if not self.group_vars.get(parent, tk.BooleanVar(value=True)).get():
                continue
            for itm in items:
                if itm["done"]:
                    continue
                if itm["ul"] == itm["lr"]:
                    continue
                self._draw_box(itm["ul"], itm["lr"], color="yellow", dashed=False)

    def _draw_box(self, ul, lr, *, color, striked=False, dashed=False):
        x1, y1 = self._grid_to_canvas(*ul)
        x2, y2 = self._grid_to_canvas(*lr)
        opts = {"outline": color, "width": 2, "tags": "box"}
        if dashed:
            opts["dash"] = (4, 4)
        self.canvas.create_rectangle(x1, y1, x2, y2, **opts)

    def on_click(self, e):
        if not self.orig_im:
            return
        x, y = e.x - self.offset_x, e.y - self.offset_y
        if not (0 <= x < self.tk_im.width() and 0 <= y < self.tk_im.height()):
            return
        imgx, imgy = x / self.scale, y / self.scale
        cw = self.orig_im.width / GRID_DIVISIONS
        ch = self.orig_im.height / GRID_DIVISIONS
        gx, gy = round(imgx / cw), round(imgy / ch)
        print(f"({gx}, {gy})")

    def open_group_manager(self):
        if hasattr(self, "_mgr_win") and self._mgr_win.winfo_exists():
            self._mgr_win.lift()
            return
        win = tk.Toplevel(self)
        win.title("Group Status Manager")
        win.geometry("400x500")
        self._mgr_win = win
        search_var = tk.StringVar()
        ttk.Entry(win, textvariable=search_var).pack(fill="x", padx=6, pady=6)
        tree = ttk.Treeview(win, show="tree")
        tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        for st, col in STATUS_COLORS.items():
            tree.tag_configure(st, foreground=col)

        def refresh_list(*_):
            query = search_var.get().lower()
            tree.delete(*tree.get_children())
            all_groups = self.player.get_all_quests()
            act = set(self.player.get_active_quests())
            comp = set(self.player.get_completed_quests())
            for g in sorted(all_groups):
                if query and query not in g.lower():
                    continue
                st = "completed" if g in comp else "active" if g in act else "inactive"
                tree.insert("", "end", text=g, tags=(st,))

        search_var.trace_add("write", refresh_list)

        menu = tk.Menu(win, tearoff=False)

        def apply_status(g, to):
            if to == "inactive":
                self.player.remove_active_quest(g)
                self.player.remove_completed_quest(g)
            elif to == "active":
                self.player.add_active_quest(g)
                self.player.remove_completed_quest(g)
            elif to == "completed":
                self.player.add_completed_quest(g)
                self.player.remove_active_quest(g)
            refresh_list()
            self.ingest_boxes(self.update_quests(self.current_map))
            self.redraw_boxes()

        for lab in ("inactive", "active", "completed"):
            menu.add_command(
                label=f"Mark {lab}",
                command=lambda new_lab=lab: apply_status(selected[0], new_lab),
            )
        selected = [None]

        def popup(ev):
            item = tree.identify_row(ev.y)
            if not item:
                return
            selected[0] = tree.item(item, "text")
            tree.selection_set(item)
            menu.tk_popup(ev.x_root, ev.y_root)

        tree.bind("<Button-3>", popup)

        refresh_list()

    def update_quests(self, map):
        active_objectives = []
        objectives = self.player.get_objectives_on_map(map)
        for objective in objectives:
            active_objectives.append(
                (
                    objective[0],  # parent quest name
                    self.objective_to_description(objective),  # generated description
                    objective[1].get(  # top left grid box coordinate
                        "LocationBoxTopLeft"
                    ),
                    objective[1].get(  # bottom right grid box coordinate
                        "LocationBoxBottomRight"
                    ),
                    objective[2],  # Whether or not this objective is completed
                )
            )

        return active_objectives

    def objective_to_description(self, objective):
        description = ""

        if objective[1].get("Type") == "elimination":
            description = description + "Eliminate "
        elif objective[1].get("Type") == "fetch" or "gather":
            description = description + "Find "
        elif objective[1].get("Type") == "scout":
            description = description + "Go to "
        elif objective[1].get("Type") == "stash":
            description = description + "Place "
        if objective[1].get("Amount") > 0:
            description = description + f"{objective[1].get('Amount')} "

        if objective[1].get("Amount") > 1:
            description = description + f"{objective[1].get('Target')}s"
        else:
            description = description + f"{objective[1].get('Target')}"

        if objective[1].get("Time")[0] != objective[1].get("Time")[1]:
            description = (
                description
                + f" between {objective[1].get('Time')[0]} and {objective[1].get('Time')[1]}"
            )

        if not objective[1].get("Required"):
            description = description + " (optional)"

        return description


if __name__ == "__main__":
    QuestViewer().mainloop()
