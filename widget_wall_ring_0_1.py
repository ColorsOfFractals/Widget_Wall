import tkinter as tk
from tkinter import ttk
from datetime import datetime

BG = "#101827"
PANEL = "#192638"
CARD = "#223349"
ACCENT = "#61d7ff"
TEXT = "#eef5ff"
MUTED = "#91a8be"

class WidgetWall:
    def __init__(self, root):
        self.root = root
        root.title("Widget_Wall | Ring 0.1")
        root.geometry("780x560")
        root.minsize(650, 480)
        root.configure(bg=BG)

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=24, pady=(22, 10))

        tk.Label(
            header, text="WIDGET_WALL",
            font=("Segoe UI", 22, "bold"),
            bg=BG, fg=ACCENT
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Desktop Widget & TokenBridge Control Panel",
            font=("Segoe UI", 10),
            bg=BG, fg=MUTED
        ).pack(anchor="w")

        tk.Frame(root, bg=ACCENT, height=2).pack(
            fill="x", padx=24, pady=12
        )

        grid = tk.Frame(root, bg=BG)
        grid.pack(fill="x", padx=24, pady=8)

        modules = [
            ("TOKENBRIDGES", "Future bridge spawner"),
            ("MINI WIDGETS", "Tiny desktop utilities"),
            ("WIDGET REGISTRY", "Installed widget inventory"),
            ("SETTINGS", "Appearance and behavior")
        ]

        for index, (name, description) in enumerate(modules):
            row, col = divmod(index, 2)

            card = tk.Frame(
                grid, bg=PANEL,
                highlightbackground="#344a61",
                highlightthickness=1
            )
            card.grid(
                row=row, column=col,
                sticky="nsew", padx=6, pady=6
            )

            tk.Label(
                card, text=name,
                font=("Segoe UI", 12, "bold"),
                bg=PANEL, fg=TEXT
            ).pack(anchor="w", padx=16, pady=(14, 4))

            tk.Label(
                card, text=description,
                font=("Segoe UI", 9),
                bg=PANEL, fg=MUTED
            ).pack(anchor="w", padx=16)

            tk.Button(
                card, text="OPEN PLACEHOLDER",
                font=("Segoe UI", 9),
                bg=CARD, fg=ACCENT,
                activebackground="#304c66",
                activeforeground=TEXT,
                relief="flat", cursor="hand2",
                command=lambda n=name: self.activate(n)
            ).pack(anchor="w", padx=16, pady=14)

        grid.columnconfigure(0, weight=1, uniform="cards")
        grid.columnconfigure(1, weight=1, uniform="cards")

        tk.Label(
            root, text="ACTIVITY LOG",
            font=("Segoe UI", 10, "bold"),
            bg=BG, fg=ACCENT
        ).pack(anchor="w", padx=30, pady=(12, 4))

        self.logbox = tk.Text(
            root, height=6, bg=PANEL, fg=TEXT,
            insertbackground=ACCENT,
            font=("Consolas", 10),
            relief="flat", state="disabled"
        )
        self.logbox.pack(
            fill="both", expand=True,
            padx=30, pady=(0, 12)
        )

        self.log("Widget_Wall initialized.")
        self.log("Four placeholder modules registered.")
        self.log("Awaiting first TokenBridge design.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logbox.configure(state="normal")
        self.logbox.insert("end", f"[{timestamp}] {message}\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def activate(self, name):
        self.log(f"{name}: placeholder activated.")
        window = tk.Toplevel(self.root)
        window.title(name)
        window.geometry("360x180")
        window.configure(bg=BG)

        tk.Label(
            window, text=name,
            font=("Segoe UI", 16, "bold"),
            bg=BG, fg=ACCENT
        ).pack(pady=(30, 12))

        tk.Label(
            window, text="Reserved for a future Widget_Wall ring.",
            font=("Segoe UI", 10),
            bg=BG, fg=TEXT
        ).pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = WidgetWall(root)
    root.mainloop()
