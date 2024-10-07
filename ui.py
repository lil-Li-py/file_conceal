import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from main import *


class MyGUI:
    def __init__(self):
        self.root = tk.Tk()
        # 默认参数
        self.prototype_file = None
        self.target_files = None
        self.target_file = None
        self.wash_file = None
        self.check_value = tk.BooleanVar()
        self.focused = False
        self.name = 'default'
        self.is_all = 0

        self.root.title('文件隐写')
        self.root.geometry(f'+{int(self.root.winfo_screenwidth()/3)}+{int(self.root.winfo_screenheight()/4)}')
        self.root.resizable(False, False)
        self.root.iconbitmap('')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.set_widget()
        self.root.mainloop()

    def close(self):
        messagebox.showinfo('', '撒哟拉拉~')
        self.root.destroy()

    def set_widget(self):
        # 总体框架
        frame = tk.LabelFrame(self.root, text='开 始 使 用', font=('微软雅黑', 20), labelanchor='n', fg='red', borderwidth=0)
        frame.pack(ipady=5, ipadx=10, pady=10, padx=10)

        # 隐写子框架1
        frame_1 = tk.LabelFrame(frame, relief='ridge', borderwidth=5)
        frame_1.pack(pady=5)
        label_1_1 = tk.Label(frame_1, text='选择原型文件(注意一定得是png格式的!!!)', font=('微软雅黑', 12))
        label_1_1.grid(row=0, column=0, padx=10, sticky='w')
        self.button_1_1 = button_1_1 = tk.Button(frame_1, text='选择', command=lambda: self.selcet_file(1), width=8, font=('微软雅黑', 10))
        button_1_1.grid(row=0, column=1, padx=10)
        button_1_2 = tk.Button(frame_1, text='取消', command=lambda: self.cancel(1), width=8, font=('微软雅黑', 10))
        button_1_2.grid(row=0, column=2, padx=10)
        self.entry_1_1 = entry_1_1 = tk.Entry(frame_1, width=20, font=('微软雅黑', 10), validatecommand=self.focus_input, validate='focusin')
        entry_1_1.insert(0, '输出文件名(默认为default)')
        entry_1_1.grid(row=1, column=0, padx=12, sticky='w', ipady=5, pady=5)
        self.check_box_1_1 = check_box_1_1 = tk.Checkbutton(frame_1, text='是否删除所有待隐藏的文件', variable=self.check_value)
        check_box_1_1.grid(row=1, column=0, sticky='e', columnspan=2)
        # 显示已选择的文件

        # 隐写子框架2
        frame_2 = tk.LabelFrame(frame, relief='ridge', borderwidth=5)
        frame_2.pack(pady=5)
        label_2_1 = tk.Label(frame_2, text='选择要隐写的文件或文件夹', font=('微软雅黑', 12))
        label_2_1.grid(row=0, column=0, padx=10, sticky='w')
        self.button_2_1 = button_2_1 = tk.Button(frame_2, text='文件选择', command=lambda: self.selcet_file(2), width=8, font=('微软雅黑', 10))
        self.button_2_2 = button_2_2 = tk.Button(frame_2, text='文件夹选择', command=self.select_dir, width=8, font=('微软雅黑', 10))
        button_2_3 = tk.Button(frame_2, text='取消', command=lambda: self.cancel(2), width=8, font=('微软雅黑', 10))
        button_2_4 = tk.Button(frame_2, text='开始隐写', command=self.encrypt, width=8, font=('微软雅黑', 10))
        button_2_1.grid(row=0, column=1, padx=9)
        button_2_2.grid(row=0, column=2, padx=9)
        button_2_3.grid(row=0, column=3, padx=8, pady=5)
        button_2_4.grid(row=1, column=1, padx=10, pady=5, ipadx=8, sticky='e')

        # 解构子框架
        frame_3 = tk.LabelFrame(frame, relief='ridge', borderwidth=5)
        frame_3.pack()
        label_3_1 = tk.Label(frame_3, text='选择要解构的文件', font=('微软雅黑', 12))
        label_3_1.grid(row=0, column=0, padx=10)
        self.button_3_1 = button_3_1 = tk.Button(frame_3, text='文件选择', command=lambda: self.selcet_file(3), width=8, font=('微软雅黑', 10))
        button_3_1.grid(row=0, column=1, padx=10)
        button_3_2 = tk.Button(frame_3, text='取消', command=lambda: self.cancel(3), width=8, font=('微软雅黑', 10))
        button_3_2.grid(row=0, column=2, padx=8)
        button_3_3 = tk.Button(frame_3, text='解构文件', command=self.decrypt, width=8, font=('微软雅黑', 10))
        button_3_3.grid(row=0, column=3, padx=10)
        label_3_2 = tk.Label(frame_3, text='输出文件个数(默认为全部文件)', font=('微软雅黑', 10))
        self.entry_3_1 = entry_3_1 = tk.Entry(frame_3, width=3, font=('微软雅黑', 10))
        label_3_2.grid(row=1, column=0, padx=10, sticky='w')
        entry_3_1.grid(row=1, column=1, pady=10, sticky='w')

        # 图片清洗操作子框架
        frame_4 = tk.LabelFrame(frame, relief='ridge', borderwidth=5)
        frame_4.pack(pady=5)
        label_4_1 = tk.Label(frame_4, text='选择要清洗的文件', font=('微软雅黑', 12))
        label_4_1.grid(row=0, column=0, padx=10, sticky='w')
        self.button_4_1 = button_4_1 = tk.Button(frame_4, text='文件选择', command=lambda: self.selcet_file(4), width=8, font=('微软雅黑', 10))
        button_4_1.grid(row=0, column=1, padx=10)
        button_4_2 = tk.Button(frame_4, text='取消', command=lambda: self.cancel(4), width=8, font=('微软雅黑', 10))
        button_4_2.grid(row=0, column=2, padx=8)
        button_4_3 = tk.Button(frame_4, text='开始清洗', command=self.wash, width=8, font=('微软雅黑', 10))
        button_4_3.grid(row=0, column=3, padx=10)

        self.button_1_1_tooltip = Tooltip(self.button_1_1, '')
        self.button_2_1_tooltip = Tooltip(self.button_2_1, '')
        self.button_2_2_tooltip = Tooltip(self.button_2_2, '')
        self.button_3_1_tooltip = Tooltip(self.button_3_1, '')
        self.button_4_1_tooltip = Tooltip(self.button_4_1, '')


    @staticmethod
    def set_tooltip(tooltip, text):
        tooltip.text = text
        tooltip.set = True

    @staticmethod
    def cancel_tooltip(tooltip):
        tooltip.set = False

    def selcet_file(self, abc):
        match abc:
            case 1:
                self.prototype_file = filedialog.askopenfilename(title='请选择一个原型文件', filetypes=[('png', '*.png')], initialdir=r'C:\Users\Administrator\Desktop')
                if self.prototype_file:
                    self.button_1_1.config(state='disabled')
                    self.set_tooltip(self.button_1_1_tooltip, self.prototype_file)
            case 2:
                self.target_files = filedialog.askopenfilename(title='请选择要隐写的文件', filetypes=[('all', '*.*')])
                if self.target_files:
                    self.button_2_1.config(state='disabled')
                    self.button_2_2.config(state='disabled')
                    self.set_tooltip(self.button_2_1_tooltip, self.target_files)
            case 3:
                self.target_file = filedialog.askopenfilename(title='请选择要解构的文件', filetypes=[('png', '*.png')])
                if self.target_file:
                    self.button_3_1.config(state='disabled')
                    self.set_tooltip(self.button_3_1_tooltip, self.target_file)
            case 4:
                self.wash_file = filedialog.askopenfilename(title='请选择要清洗的文件', filetypes=[('png', '*.png')])
                if self.wash_file:
                    self.button_4_1.config(state='disabled')
                    self.set_tooltip(self.button_4_1_tooltip, self.wash_file)

    def select_dir(self):
        self.target_files = filedialog.askdirectory(title='请选择要隐写的文件夹')
        if self.target_files:
            self.button_2_1.config(state='disabled')
            self.button_2_2.config(state='disabled')
            self.set_tooltip(self.button_2_2_tooltip, self.target_files)

    def focus_input(self):
        self.entry_1_1.delete(0, 'end')
        self.focused = True
        return self.focused

    def cancel(self, abc):
        match abc:
            case 1:
                self.prototype_file = None
                self.button_1_1.config(state='normal')
                self.cancel_tooltip(self.button_1_1_tooltip)
            case 2:
                self.target_files = None
                self.button_2_1.config(state='normal')
                self.button_2_2.config(state='normal')
                self.cancel_tooltip(self.button_2_1_tooltip)
                self.cancel_tooltip(self.button_2_2_tooltip)
            case 3:
                self.target_file = None
                self.button_3_1.config(state='normal')
                self.cancel_tooltip(self.button_3_1_tooltip)
            case 4:
                self.wash_file = None
                self.button_4_1.config(state='normal')
                self.cancel_tooltip(self.button_4_1_tooltip)

    def encrypt(self):
        if self.focused:
            self.name = self.entry_1_1.get() if self.entry_1_1.get() else 'default'
        if not self.prototype_file:
            messagebox.showerror('', '请先选择原型文件')
            return
        if not self.target_files:
            messagebox.showerror('', '请先选择要隐写的文件或文件夹')
            return
        messagebox.showinfo('', '开始执行~')
        encrypt_main(self.prototype_file, self.target_files, out_file_name=self.name, is_remove=self.check_value.get())
        messagebox.showinfo('', '执行完毕, 请查看~')
        self.cancel(1)
        self.cancel(2)

    def decrypt(self):
        try:
            self.is_all = int(self.entry_3_1.get())
        except ValueError:
            pass
        finally:
            self.entry_3_1.delete(0, 'end')
        if not self.target_file:
            messagebox.showerror('', '请先选择要解构的文件')
            return
        messagebox.showinfo('', '开始执行~')
        res = decrypt_main(self.target_file, is_all=self.is_all)
        if not res:
            messagebox.showerror('', '抱歉当前文件中并无隐藏文件!!!')
            return
        messagebox.showinfo('', '执行完毕, 请查看~')
        self.cancel(3)

    def wash(self):
        if not self.target_file:
            messagebox.showerror('', '请先选择要清洗的文件')
            return
        messagebox.showinfo('', '开始执行~')
        res = img_wash(self.target_file)
        if not res:
            messagebox.showerror('', '抱歉当前文件中并无隐藏文件!!!')
            return
        messagebox.showinfo('', '执行完毕, 请查看~')
        self.cancel(4)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.set = False
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip is None and self.set:
            time.sleep(0.5)
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text=self.text)
            label.pack()

    def hide_tooltip(self, event):
        if self.tooltip is not None and self.set:
            self.tooltip.destroy()
            self.tooltip = None


if __name__ == '__main__':
    MyGUI()
