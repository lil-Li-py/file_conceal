import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from main import build_encrypt_output_path, decrypt_main, encrypt_main, img_wash, suggest_encrypt_output_name


IMAGE_FILE_TYPES = [
    ("支持的图片", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
    ("PNG", "*.png"),
    ("JPG", "*.jpg *.jpeg"),
    ("GIF", "*.gif"),
    ("BMP", "*.bmp"),
    ("WEBP", "*.webp"),
]

WINDOW_BG = "#f6f7fb"
CARD_BG = "#ffffff"
TITLE_COLOR = "#1f2937"
TEXT_COLOR = "#4b5563"
ACCENT = "#2563eb"


class MyGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文件隐写工具")
        self.root.geometry("920x700")
        self.root.minsize(920, 700)
        self.root.resizable(False, False)
        self.root.configure(bg=WINDOW_BG)

        self.prototype_file = ""
        self.target_files = ""
        self.decrypt_file = ""
        self.wash_file = ""

        self.remove_source = tk.BooleanVar(value=False)
        self.require_key_var = tk.BooleanVar(value=False)

        self.output_name_var = tk.StringVar(value="result")
        self.extract_count_var = tk.StringVar(value="0")
        self.decrypt_key_var = tk.StringVar(value="")
        self.prototype_var = tk.StringVar(value="未选择原图")
        self.target_var = tk.StringVar(value="未选择待隐藏文件")
        self.decrypt_var = tk.StringVar(value="未选择待解析图片")
        self.wash_var = tk.StringVar(value="未选择待清洗图片")
        self.key_status_var = tk.StringVar(value="当前模式：不需要密钥")

        self._configure_style()
        self._build()
        self.remove_source.trace_add("write", self._on_remove_source_change)
        self.require_key_var.trace_add("write", self._on_require_key_change)
        self._center_window()
        self.root.mainloop()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Page.TFrame", background=WINDOW_BG)
        style.configure("Card.TFrame", background=CARD_BG, relief="flat")
        style.configure(
            "CardTitle.TLabel",
            background=CARD_BG,
            foreground=TITLE_COLOR,
            font=("Microsoft YaHei UI", 13, "bold"),
        )
        style.configure(
            "Body.TLabel",
            background=CARD_BG,
            foreground=TEXT_COLOR,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Path.TLabel",
            background="#f8fafc",
            foreground="#111827",
            font=("Consolas", 9),
            padding=(10, 8),
        )
        style.configure(
            "Primary.TButton",
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(10, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1d4ed8"), ("!disabled", ACCENT)],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure("Secondary.TButton", padding=(10, 6), font=("Microsoft YaHei UI", 10))
        style.configure(
            "Card.TLabelframe",
            background=CARD_BG,
            borderwidth=0,
            relief="flat",
            padding=14,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=CARD_BG,
            foreground=TITLE_COLOR,
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        style.configure("Card.TEntry", padding=6, fieldbackground="#ffffff")

    def _build(self):
        page = ttk.Frame(self.root, style="Page.TFrame", padding=24)
        page.pack(fill="both", expand=True)
        page.columnconfigure(0, weight=1)

        header = ttk.Frame(page, style="Page.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="图片文件隐藏 / 解析 / 清洗",
            style="CardTitle.TLabel",
            font=("Microsoft YaHei UI", 18, "bold"),
            background=WINDOW_BG,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="支持 PNG、JPG/JPEG、GIF、BMP、WEBP 作为载体图片，待隐藏文件类型不限。",
            foreground=TEXT_COLOR,
            background=WINDOW_BG,
            font=("Microsoft YaHei UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self._build_encrypt_section(page).grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self._build_decrypt_section(page).grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self._build_wash_section(page).grid(row=3, column=0, sticky="ew")

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _show_generated_key_dialog(self, output_name: str, generated_key: str):
        dialog = tk.Toplevel(self.root)
        dialog.title("隐藏完成")
        dialog.configure(bg=CARD_BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        container = ttk.Frame(dialog, style="Card.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        ttk.Label(
            container,
            text=f"文件隐藏完成，输出文件名：{output_name}",
            style="CardTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            container,
            text="本次自动生成的密钥如下，请复制保存，后续解析需要使用。",
            style="Body.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(10, 8))

        key_entry = ttk.Entry(container, width=36, style="Card.TEntry")
        key_entry.grid(row=2, column=0, sticky="ew")
        key_entry.insert(0, generated_key)
        key_entry.state(["readonly"])

        button_row = ttk.Frame(container, style="Card.TFrame")
        button_row.grid(row=3, column=0, sticky="e", pady=(14, 0))

        def copy_key():
            self.root.clipboard_clear()
            self.root.clipboard_append(generated_key)
            self.root.update()
            messagebox.showinfo("已复制", "密钥已复制到剪贴板。", parent=dialog)

        ttk.Button(button_row, text="复制密钥", style="Secondary.TButton", command=copy_key).pack(side="left")
        ttk.Button(button_row, text="关闭", style="Primary.TButton", command=dialog.destroy).pack(side="left", padx=(8, 0))

        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        x = root_x + max((root_width - dialog_width) // 2, 0)
        y = root_y + max((root_height - dialog_height) // 2, 0)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        key_entry.state(["!readonly"])
        key_entry.focus_set()
        key_entry.selection_range(0, tk.END)
        key_entry.state(["readonly"])

        self.root.wait_window(dialog)

    def _build_encrypt_section(self, parent):
        frame = ttk.LabelFrame(parent, text="1. 文件隐藏", style="Card.TLabelframe")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        ttk.Label(frame, text="原图", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        ttk.Button(frame, text="选择原图", style="Secondary.TButton", command=self._select_prototype).grid(row=0, column=1, sticky="w", pady=(0, 10))
        ttk.Label(frame, textvariable=self.prototype_var, style="Path.TLabel").grid(row=0, column=2, columnspan=2, sticky="ew", padx=(12, 0), pady=(0, 10))

        ttk.Label(frame, text="待隐藏内容", style="Body.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        button_group = ttk.Frame(frame, style="Card.TFrame")
        button_group.grid(row=1, column=1, sticky="w", pady=(0, 10))
        ttk.Button(button_group, text="选择文件", style="Secondary.TButton", command=self._select_target_file).pack(side="left")
        ttk.Button(button_group, text="选择文件夹", style="Secondary.TButton", command=self._select_target_dir).pack(side="left", padx=(8, 0))
        ttk.Label(frame, textvariable=self.target_var, style="Path.TLabel").grid(row=1, column=2, columnspan=2, sticky="ew", padx=(12, 0), pady=(0, 10))

        ttk.Label(frame, text="输出文件名", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        ttk.Entry(frame, textvariable=self.output_name_var, width=18, style="Card.TEntry").grid(row=2, column=1, sticky="w", pady=(0, 10))

        tk.Checkbutton(
            frame,
            text="隐藏后删除源文件",
            variable=self.remove_source,
            bg=CARD_BG,
            fg=TEXT_COLOR,
            activebackground=CARD_BG,
            activeforeground=TEXT_COLOR,
            selectcolor="#dbeafe",
            font=("Microsoft YaHei UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(0, 10))

        tk.Checkbutton(
            frame,
            text="需要密钥",
            variable=self.require_key_var,
            bg=CARD_BG,
            fg=TEXT_COLOR,
            activebackground=CARD_BG,
            activeforeground=TEXT_COLOR,
            selectcolor="#dbeafe",
            font=("Microsoft YaHei UI", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=3, column=1, sticky="w")
        ttk.Label(frame, textvariable=self.key_status_var, style="Body.TLabel").grid(row=3, column=2, sticky="w", padx=(12, 0))
        ttk.Button(frame, text="开始隐藏", style="Primary.TButton", command=self.encrypt).grid(row=3, column=3, sticky="e")
        return frame

    def _build_decrypt_section(self, parent):
        frame = ttk.LabelFrame(parent, text="2. 文件解析", style="Card.TLabelframe")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        ttk.Label(frame, text="目标图片", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        ttk.Button(frame, text="选择图片", style="Secondary.TButton", command=self._select_decrypt_file).grid(row=0, column=1, sticky="w", pady=(0, 10))
        ttk.Label(frame, textvariable=self.decrypt_var, style="Path.TLabel").grid(row=0, column=2, columnspan=2, sticky="ew", padx=(12, 0), pady=(0, 10))

        ttk.Label(frame, text="提取数量", style="Body.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 10))
        ttk.Entry(frame, textvariable=self.extract_count_var, width=10, style="Card.TEntry").grid(row=1, column=1, sticky="w", pady=(0, 10))
        ttk.Label(frame, text="填 0 表示提取全部隐藏文件", style="Body.TLabel").grid(row=1, column=2, sticky="w", padx=(12, 0), pady=(0, 10))

        ttk.Label(frame, text="解密密钥", style="Body.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(frame, textvariable=self.decrypt_key_var, width=24, style="Card.TEntry").grid(row=2, column=1, sticky="w")
        ttk.Label(frame, text="无密钥模式可留空", style="Body.TLabel").grid(row=2, column=2, sticky="w", padx=(12, 0))
        ttk.Button(frame, text="开始解析", style="Primary.TButton", command=self.decrypt).grid(row=2, column=3, sticky="e")
        return frame

    def _build_wash_section(self, parent):
        frame = ttk.LabelFrame(parent, text="3. 图片清洗", style="Card.TLabelframe")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

        ttk.Label(frame, text="目标图片", style="Body.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Button(frame, text="选择图片", style="Secondary.TButton", command=self._select_wash_file).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, textvariable=self.wash_var, style="Path.TLabel").grid(row=0, column=2, sticky="ew", padx=(12, 0))
        ttk.Button(frame, text="开始清洗", style="Primary.TButton", command=self.wash).grid(row=0, column=3, sticky="e", padx=(12, 0))
        return frame

    def _select_prototype(self):
        path = filedialog.askopenfilename(title="选择原图", filetypes=IMAGE_FILE_TYPES)
        if path:
            self.prototype_file = path
            self.prototype_var.set(path)
            if self.remove_source.get():
                self.output_name_var.set(os.path.splitext(os.path.basename(path))[0])
            else:
                self.output_name_var.set("result")

    def _select_target_file(self):
        path = filedialog.askopenfilename(title="选择待隐藏文件", filetypes=[("所有文件", "*.*")])
        if path:
            self.target_files = path
            self.target_var.set(path)

    def _select_target_dir(self):
        path = filedialog.askdirectory(title="选择待隐藏文件夹")
        if path:
            self.target_files = path
            self.target_var.set(path)

    def _select_decrypt_file(self):
        path = filedialog.askopenfilename(title="选择待解析图片", filetypes=IMAGE_FILE_TYPES)
        if path:
            self.decrypt_file = path
            self.decrypt_var.set(path)

    def _select_wash_file(self):
        path = filedialog.askopenfilename(title="选择待清洗图片", filetypes=IMAGE_FILE_TYPES)
        if path:
            self.wash_file = path
            self.wash_var.set(path)

    def _reset_encrypt(self):
        self.prototype_file = ""
        self.target_files = ""
        self.prototype_var.set("未选择原图")
        self.target_var.set("未选择待隐藏文件")
        self.output_name_var.set("result")
        self.remove_source.set(False)
        self.require_key_var.set(False)
        self.key_status_var.set("当前模式：不需要密钥")

    def _reset_decrypt(self):
        self.decrypt_file = ""
        self.decrypt_var.set("未选择待解析图片")
        self.extract_count_var.set("0")
        self.decrypt_key_var.set("")

    def _reset_wash(self):
        self.wash_file = ""
        self.wash_var.set("未选择待清洗图片")

    def _on_remove_source_change(self, *_):
        if self.remove_source.get():
            if self.prototype_file:
                self.output_name_var.set(os.path.splitext(os.path.basename(self.prototype_file))[0])
        else:
            self.output_name_var.set("result")

    def _on_require_key_change(self, *_):
        if self.require_key_var.get():
            self.key_status_var.set("当前模式：需要密钥，隐藏成功后系统会生成并展示密钥")
        else:
            self.key_status_var.set("当前模式：不需要密钥")

    def encrypt(self):
        output_name = self.output_name_var.get().strip() or "result"
        if not self.prototype_file:
            messagebox.showerror("错误", "请先选择原图。")
            return
        if not self.target_files:
            messagebox.showerror("错误", "请先选择待隐藏的文件或文件夹。")
            return

        requested_output = build_encrypt_output_path(self.prototype_file, output_name)
        same_as_prototype = os.path.abspath(requested_output) == os.path.abspath(self.prototype_file)
        if not same_as_prototype and os.path.exists(requested_output):
            suggested_name, suggested_path = suggest_encrypt_output_name(self.prototype_file, output_name)
            confirm = messagebox.askyesno(
                "提示",
                f"检测到输出文件重名：\n{requested_output}\n\n是否改为：\n{suggested_path}",
            )
            if not confirm:
                return
            output_name = suggested_name
            self.output_name_var.set(output_name)

        try:
            generated_key = encrypt_main(
                self.prototype_file,
                self.target_files,
                out_file_name=output_name,
                is_remove=self.remove_source.get(),
                require_key=self.require_key_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        if generated_key:
            self._show_generated_key_dialog(output_name, generated_key)
        else:
            messagebox.showinfo("完成", f"文件隐藏完成。\n输出文件名：{output_name}")
        self._reset_encrypt()

    def decrypt(self):
        if not self.decrypt_file:
            messagebox.showerror("错误", "请先选择待解析图片。")
            return

        try:
            extract_count = int(self.extract_count_var.get().strip() or "0")
        except ValueError:
            messagebox.showerror("错误", "提取数量必须是整数。")
            return

        try:
            result = decrypt_main(
                self.decrypt_file,
                is_all=extract_count,
                key=self.decrypt_key_var.get().strip() or None,
            )
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        if not result:
            self._reset_decrypt()
            messagebox.showwarning("提示", "当前图片中没有可解析的隐藏文件。")
            return

        messagebox.showinfo("完成", "文件解析完成。")
        self._reset_decrypt()

    def wash(self):
        if not self.wash_file:
            messagebox.showerror("错误", "请先选择待清洗图片。")
            return

        try:
            result = img_wash(self.wash_file)
        except Exception as exc:
            messagebox.showerror("错误", str(exc))
            return

        if not result:
            messagebox.showwarning("提示", "当前图片中没有可清洗的隐藏内容。")
            return

        messagebox.showinfo("完成", "图片清洗完成。")
        self._reset_wash()


if __name__ == "__main__":
    MyGUI()
