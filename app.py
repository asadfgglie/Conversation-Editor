import base64
import json
import os.path

import customtkinter as cstk
from tkinter import filedialog, messagebox
from functools import partial

import pydantic

import schema
from PIL import Image
from io import BytesIO
from collections import OrderedDict


class Message(cstk.CTkFrame):
    img_max_size = 400

    def __init__(self, master, message: schema.Message):
        super().__init__(master)
        self.grid_columnconfigure(3, weight=1)

        self.author_name_entry = cstk.CTkEntry(self, placeholder_text='訊息作者名稱')
        self.author_name_entry.insert(0, message.name)
        self.author_name_entry.grid(column=0, row=0)
        self.role_option_menu = cstk.CTkOptionMenu(self, values=['user', 'system', 'assistant'])
        self.role_option_menu.set(message.role)
        self.role_option_menu.grid(column=1, row=0)
        self.timestamp_entry = cstk.CTkEntry(self, placeholder_text='時間戳')
        self.timestamp_entry.insert(0, message.timestamp)
        self.timestamp_entry.grid(column=2, row=0)

        self.content_list: OrderedDict[cstk.CTkButton, cstk.CTkTextbox | cstk.CTkLabel] = OrderedDict()

        if isinstance(message.content, list):
            for i, c in enumerate(message.content):
                delete_button = cstk.CTkButton(self, text='X', width=0)
                delete_button.configure(command=partial(self.delete, delete_button))
                delete_button.grid(column=4, row=i + 1)
                if isinstance(c, schema.TextContent):
                    textbox = cstk.CTkTextbox(self, height=80)
                    textbox.insert('1.0', c.text)
                    textbox.grid(column=0, columnspan=4, row=i + 1, sticky='we')
                    self.content_list[delete_button] = textbox
                elif isinstance(c, schema.ImageContent):
                    img = Image.open(BytesIO(c.get_image_bytes()))
                    if max(img.size) > self.img_max_size:
                        size = ((img.size[0] * self.img_max_size) // max(img.size),
                                (img.size[1] * self.img_max_size) // max(img.size))
                    else:
                        size = img.size
                    image_label = cstk.CTkLabel(self, text='',
                                                image=cstk.CTkImage(light_image=img, size=size))
                    image_label.grid(column=0, columnspan=4, row=i + 1, sticky='we')
                    self.content_list[delete_button] = image_label
        else:
            delete_button = cstk.CTkButton(self, text='X', width=0)
            delete_button.configure(command=partial(self.delete, delete_button))
            delete_button.grid(column=4, row=1)
            textbox = cstk.CTkTextbox(self, height=80)
            textbox.insert('1.0', message.content)
            textbox.grid(column=0, columnspan=4, row=1, sticky='we')
            self.content_list[delete_button] = textbox

        self.add_content_button = cstk.CTkButton(self, text='新增內容', width=0, command=self.add_content,
                                                 state=cstk.DISABLED
                                                 if isinstance(self.content_list[list(self.content_list.keys())[-1]],
                                                               cstk.CTkTextbox)
                                                 else cstk.NORMAL)
        self.add_image_button = cstk.CTkButton(self, text='新增圖片', width=0, command=self.add_image)
        self.add_content_button.grid(column=0, row=len(self.content_list) + 1)
        self.add_image_button.grid(column=1, row=len(self.content_list) + 1)

    def add_image(self):
        delete_button = cstk.CTkButton(self, text='X', width=0)
        delete_button.configure(command=partial(self.delete, delete_button))
        delete_button.grid(column=4, row=len(self.content_list) + 1)
        path = filedialog.askopenfilename(filetypes=[('圖片',
                                                             ('.jpg', '.jpeg', '.png', '.bmp', '.webp')),
                                                            ('所有檔案', '.*')])
        if path == '':
            return
        try:
            with open(path, 'rb') as f:
                img = Image.open(BytesIO(f.read()))
        except Exception as e:
            messagebox.showerror('讀取失敗!', f'圖片讀取失敗!\n原因: {e}')
            delete_button.destroy()
            del delete_button
            return
        if max(img.size) > self.img_max_size:
            size = ((img.size[0] * self.img_max_size) // max(img.size),
                    (img.size[1] * self.img_max_size) // max(img.size))
        else:
            size = img.size
        image_label = cstk.CTkLabel(self, text='',
                                    image=cstk.CTkImage(light_image=img, size=size))
        image_label.grid(column=0, columnspan=4, row=len(self.content_list) + 1, sticky='we')
        self.content_list[delete_button] = image_label

        self.add_content_button.grid_forget()
        self.add_image_button.grid_forget()
        self.add_content_button.grid(column=0, row=len(self.content_list) + 1)
        self.add_image_button.grid(column=1, row=len(self.content_list) + 1)

        self.add_content_button.configure(state=cstk.NORMAL)

    def delete(self, button: cstk.CTkButton):
        self.content_list[button].destroy()
        self.content_list.pop(button)
        button.destroy()

        if len(self.content_list) == 0:
            self.grid_forget()

        if len(self.content_list) > 0:
            self.add_content_button.configure(state=cstk.DISABLED
                                              if isinstance(self.content_list[list(self.content_list.keys())[-1]],
                                                            cstk.CTkTextbox)
                                              else cstk.NORMAL)

    def add_content(self):
        delete_button = cstk.CTkButton(self, text='X', width=0)
        delete_button.configure(command=partial(self.delete, delete_button))
        delete_button.grid(column=4, row=len(self.content_list) + 1)
        textbox = cstk.CTkTextbox(self, height=80)
        textbox.grid(column=0, columnspan=4, row=len(self.content_list) + 1, sticky='we')
        self.content_list[delete_button] = textbox

        self.add_content_button.grid_forget()
        self.add_image_button.grid_forget()
        self.add_content_button.grid(column=0, row=len(self.content_list) + 1)
        self.add_image_button.grid(column=1, row=len(self.content_list) + 1)

        self.add_content_button.configure(state=cstk.DISABLED)

    def to_message(self) -> schema.Message | None:
        content = []
        for c in self.content_list.values():
            if isinstance(c, cstk.CTkTextbox):
                content.append(schema.TextContent(text=c.get('1.0', cstk.END).strip('\n')))
            elif isinstance(c, cstk.CTkLabel):
                b = BytesIO()
                c.cget('image').cget('light_image').save(b, format='jpeg')
                content.append(schema.ImageContent(image_url=schema.Image(url=base64.b64encode(
                    b.getvalue()
                ).decode('utf8'))))
        return schema.Message(role=self.role_option_menu.get(), timestamp=self.timestamp_entry.get(),
                              name=self.author_name_entry.get(), content=content) if len(content) > 0 else None


class App(cstk.CTk):
    def __init__(self):
        super().__init__()
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.title('對話編輯器')
        self.geometry('800x500')
        self.minsize(800, 400)

        self.load_entry = cstk.CTkEntry(self, placeholder_text='資料夾路徑', width=160, state=cstk.DISABLED)
        self.load_entry.grid(column=0, row=0)
        self.path_selector_button = cstk.CTkButton(self, text='選擇資料夾', command=self.load_path, width=0)
        self.path_selector_button.grid(column=1, row=0)

        self.doc_list_frame = cstk.CTkScrollableFrame(self)
        self.doc_list_frame.grid(column=0, row=1, columnspan=2, sticky='nesw')
        self.doc_list_frame.grid_columnconfigure(0, weight=1)
        self.doc_list_button_list: list[cstk.CTkButton] = []

        self.current_file_label = cstk.CTkLabel(self, text='')
        self.current_file_label.grid(column=2, row=0, sticky='we')

        def f():
            self.save_history(path=self.current_file_label.cget('text'), ask_again=True)

        self.save_button = cstk.CTkButton(self, text='存檔', width=0, command=f)
        self.save_button.grid(column=3, row=0)

        def f():
            self.save_history(path=filedialog.asksaveasfilename(defaultextension='.json',
                                                                filetypes=[('json文件', '.json',), ('所有文件', '.*')]),
                              ask_again=False)

        self.other_save_button = cstk.CTkButton(self, text='另存新檔', width=0, command=f)
        self.other_save_button.grid(column=4, row=0)

        def f():
            self.current_file_label.configure(text='')
            self.add_message_button.grid_forget()

            for m in self.current_message_list:
                m.destroy()
            self.current_message_list.clear()

            self.add_message_button.grid(column=0, row=len(self.current_message_list), sticky='we')

        self.close_file_button = cstk.CTkButton(self, text='關閉檔案', width=0, command=f)
        self.close_file_button.grid(column=5, row=0)

        def f():
            path = filedialog.askopenfilename(filetypes=[('json文件', '.json',), ('所有文件', '.*')])
            self.load_history(path)

        self.open_file_button = cstk.CTkButton(self, text='開啟檔案', width=0, command=f)
        self.open_file_button.grid(column=6, row=0)

        self.scroll_frame = cstk.CTkScrollableFrame(self)
        self.scroll_frame.grid(column=2, row=1, columnspan=5, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.current_message_list: list[Message] = []

        self.add_message_button = cstk.CTkButton(self.scroll_frame, text='新增訊息', command=self.add_message)
        self.add_message_button.grid(column=0, row=len(self.current_message_list), sticky='we')

    def add_message(self):
        self.add_message_button.grid_forget()
        self.current_message_list.append(Message(self.scroll_frame, schema.Message(role='user', content='')))
        self.current_message_list[-1].grid(column=0, row=len(self.current_message_list), sticky='we')
        self.add_message_button.grid(column=0, row=len(self.current_message_list) + 1, sticky='we')

    def save_history(self, path: str, ask_again: bool):
        if path == '' and ask_again:
            path = filedialog.asksaveasfilename(defaultextension='.json',
                                                filetypes=[('json文件', '.json',), ('所有文件', '.*')])
            if path == '':
                return
        elif path == '':
            return

        if os.path.exists(path):
            pass

        if self.current_file_label.cget('text') != '':
            with open(self.current_file_label.cget('text'), 'r', encoding='utf8') as f:
                try:
                    schema.History.model_validate_json(f.read())
                except pydantic.ValidationError:
                    if (self.current_file_label.cget('text') == path and
                            not messagebox.askyesno('提醒', '原始檔案中存在其他資訊，是否要覆蓋?')):
                        path = path + '_modify' if path.rfind('.') == -1 \
                            else path[:path.rfind('.')] + '_modify' + path[path.rfind('.'):]

        with open(path, 'w', encoding='utf8') as f:
            f.write(schema.History(history=[m.to_message() for m in self.current_message_list
                                            if m.to_message() is not None]).model_dump_json(indent=2))

        self.current_file_label.configure(text=path)

        if self.load_entry.get() != '':
            self.load_path()

    def load_path(self):
        path = filedialog.askdirectory(mustexist=True)
        self.load_entry.configure(state=cstk.NORMAL)
        self.load_entry.delete(0, cstk.END)
        self.load_entry.insert(0, path)
        for b in self.doc_list_button_list:
            b.destroy()
        for i, p in enumerate(p for p in os.listdir(self.load_entry.get())
                              if os.path.isfile(os.path.join(self.load_entry.get(), p)) and p.endswith('.json')):
            path = os.path.join(self.load_entry.get(), p)
            self.doc_list_button_list.append(cstk.CTkButton(self.doc_list_frame, text=p,
                                                            command=partial(self.load_history, path)))
            self.doc_list_button_list[-1].grid(column=0, row=i, sticky='we')
            self.doc_list_button_list[-1].configure()
        self.load_entry.configure(state=cstk.DISABLED)

    def load_history(self, file_path: str):
        with open(file_path, 'r', encoding='utf8') as f:
            obj = json.loads(f.read())

        try:
            if isinstance(obj, list):
                history = schema.History(history=obj)
            else:
                history = schema.History(**obj)
        except pydantic.ValidationError as e:
            messagebox.showerror('錯誤!', f'這不是一個合法的對話紀錄檔。\n{e}')
            return

        self.add_message_button.grid_forget()
        for m in self.current_message_list:
            m.destroy()
        self.current_message_list.clear()

        for i, m in enumerate(history.history):
            self.current_message_list.append(Message(self.scroll_frame, m))
            self.current_message_list[-1].grid(column=0, row=i, sticky='we')

        self.current_file_label.configure(text=file_path)

        self.add_message_button.grid(column=0, row=len(self.current_message_list), sticky='we')


if __name__ == '__main__':
    app = App()
    app.mainloop()
