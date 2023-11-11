import os
import tkinter as tk
import tkinter.filedialog
import aiofiles
import aiohttp
import asyncio
import requests
import re
from bs4 import BeautifulSoup
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

WIDTH, HEIGHT = 600, 400    # 窗口大小
PADDING = 4                # 右下角窗口边距
OFFSET_X, OFFSET_Y = 500, 300   # 窗口偏移量

class DownloadUI(tk.Frame):    # 下载UI
    def __init__(self, master: tk.Tk=None) -> None:
        super().__init__(master)
        self.place()    # 采用place布局
        self.download_core = DownloadCore()    # 下载内核
        if not os.path.exists("Downloads"):
            os.mkdir("Downloads")
        self.path = os.getcwd() + "\Downloads"      # 当前路径
        self.ui_init()

    def ui_init(self) -> None:
        # 创建背景图片
        self.bp = tk.PhotoImage(file=f"bg.png").subsample(2)
        self.bp_canvas = tk.Canvas(width=WIDTH, height=HEIGHT)
        self.bp_canvas.place(x=0, y=0)
        self.bp_canvas.create_image(0, 0, image=self.bp, anchor='nw')
        # 创建标签
        LABEL_FONT_SIZE = 13
        LABEL_RELX = 0.1
        LABEL_WIDTH = 68
        self.column_label = tk.Label(text="①专栏地址:", font=("黑体", LABEL_FONT_SIZE))
        self.column_label.place(relx=LABEL_RELX, rely=0.05)
        self.info_label = tk.Label(text="暂无下载内容", justify="center", width=LABEL_WIDTH, height=1, fg="black")
        self.info_label.place(relx=LABEL_RELX, rely=0.83)
        self.path_label = tk.Label(text="当前路径为：" + self.path, width=LABEL_WIDTH, justify="center", height=1, fg="black", anchor="w")
        self.path_label.place(relx=LABEL_RELX, rely=0.88)
        self.space_label = tk.Label(text="②空间地址:", font=("黑体", LABEL_FONT_SIZE))
        self.space_label.place(relx=LABEL_RELX, rely=0.15)
        self.page_label = tk.Label(text=" 空间页数:", font=("黑体", LABEL_FONT_SIZE))
        self.page_label.place(relx=LABEL_RELX, rely=0.25)
        # 创建输入框
        ENTRY_WIDTH = 38
        ENTRY_RELX = 0.28
        self.column_value = tk.StringVar()
        self.space_value = tk.StringVar()
        self.page_value = tk.StringVar()
        self.page_value.set("1-3")
        self.column_entry = tk.Entry(width=ENTRY_WIDTH, textvariable=self.column_value)
        self.column_entry.place(relx=ENTRY_RELX, rely=0.05)
        self.space_entry = tk.Entry(width=ENTRY_WIDTH, textvariable=self.space_value)
        self.space_entry.place(relx=ENTRY_RELX, rely=0.15)
        self.page_entry = tk.Entry(width=7, textvariable=self.page_value)
        self.page_entry.place(relx=ENTRY_RELX, rely=0.25)
        # 创建按钮
        self.column_btn = tk.Button(text="提交", font=("黑体", 10), height=1,
                                    command=lambda : Thread(target=self.column_download).start())
        self.column_btn.place(relx=0.75,rely=0.05)
        self.change_path_btn = tk.Button(text="更\n改\n路\n径", font=("黑体", 12), height=4, command=self.change_path)
        self.change_path_btn.place(relx=0.85, rely=0.04)
        self.space_btn = tk.Button(text="提交", font=("黑体", 10), height=1,
                                   command=lambda : Thread(target=self.space_download).start())
        self.space_btn.place(relx=0.75, rely=0.15)

    def change_path(self) -> None:  # 更改下载路径
        address = tk.filedialog.askdirectory()
        if address != '':
            self.address = address
            self.path_label.configure(text=f"当前路径为：{self.address}")

    def column_download(self) -> None:  # 一个专栏图片下载
        self.info_label.configure(text="正在下载中......")
        times = self.download_core.column_download(self.column_value.get(), self.path)
        if (times is None):
            self.info_label.configure(text="地址输入错误！")
        else:
            self.info_label.configure(text=f"{times}次下载已完成")

    def space_download(self) -> None:   # 按页数下载空间的专栏图片
        self.info_label.configure(text="正在下载中......")
        times = self.download_core.space_download(self.space_value.get(), self.path, self.page_value.get())
        if (times is None):
            self.info_label.configure(text="地址或页数输入错误！")
        else:
            self.info_label.configure(text=f"{times}次下载已完成")

class DownloadCore():   # 下载内核
    def __init__(self) -> None:
        self.times = 0
        self.headers = {
            'referer': 'https://space.bilibili.com/9277299/article',    # 防盗链，随便找一个专栏地址
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36'
        }
        self.obj = re.compile('"id":(?P<id>\d+),"category.*?],"title":"(?P<title>.*?)","summary"')

    def column_download(self, url: str, path: str) -> Optional[int]:
        try:
            # 页面解析获得图片地址
            resp = requests.get(url, headers=self.headers)
            imgs = BeautifulSoup(resp.text, "html.parser").find_all("img", class_=None)
            # 异步下载图片
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # 解决RuntimeError: Event loop is closed
            asyncio.run(self.async_main(imgs, path))

            self.times += 1
            return self.times
        except Exception as e:
            print(e.with_traceback())
            return None

    async def async_main(self, imgs, path) -> None:
        tasks = []
        for img in imgs:
            src = img.get("data-src")
            name = path + "\\" + src.split("/")[-1]
            src = "https:" + src
            tasks.append(asyncio.create_task(self.picture_download(src, name)))
        await asyncio.gather(*tasks)

    async def picture_download(self, src: str, path: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(src) as html:
                content = await html.read()  # 读取内容
                async with aiofiles.open(path, mode="wb") as f:
                    await f.write(content)

    def space_download(self, url: str, path: str, page: str) -> Optional[int]:
        # 判断地址和页数是否输入正确
        try:
            response = requests.get(url)
            page = page.split('-')
            start, end = int(page[0]), int(page[1])
        except Exception as e:
            print(e.with_traceback())
            return None
        UID = url.split('/')[-1]  # 获得空间的UID

        flag = True  # 判断是否越界
        index = start if start >= 0 else 0  # 页数
        while (flag):
            if index > end:
                break
            flag = False
            url = 'https://api.bilibili.com/x/space/article?mid=' + UID + '&pn=' + str(
                index) + '&ps=12&sort=publish_time&jsonp=jsonp&callback=__jp1'
            resp = requests.get(url, headers=self.headers)
            resp.encoding = 'utf-8'
            ids = self.obj.finditer(resp.text)  # 获得的本页的专栏id和标题
            with ThreadPoolExecutor(20) as t:
                for id in ids:
                    dir_path = path + '\\' + id.group("title").replace('/', '|').replace(':', '|')
                    if not os.path.exists(dir_path):
                        os.mkdir(dir_path)
                    url = "https://www.bilibili.com/read/cv" + id.group("id") + "?spm_id_from=333.999.0.0"
                    t.submit(self.column_download(url, dir_path))
                    flag = True
            index += 1
        return self.times

if __name__ == "__main__":
    application = tk.Tk()
    application.geometry(f"{WIDTH + PADDING}x{HEIGHT + PADDING}+{OFFSET_X}+{OFFSET_Y}")
    application.resizable(width=False, height=False)  # 设置无法更改比例
    application.title("B站专栏图片下载")
    application.attributes("-alpha", 0.9)  # 设置透明度
    DownloadUI(application)
    application.mainloop()