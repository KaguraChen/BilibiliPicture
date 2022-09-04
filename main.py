import os
import tkinter as tk
import tkinter.filedialog
import aiofiles
import aiohttp
import asyncio
import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.place()
        self.address = os.getcwd()       # 当前路径
        self.time=0     # 记录下载次数

        self.creatUI()

    def creatUI(self):
        # 创建背景图片
        self.photo = tk.PhotoImage(file=f"bg.png").subsample(2)
        self.bp = tk.Canvas(width=600,height=400)
        self.bp.place(x=0, y=0)
        self.bp.create_image(0, 0, image=self.photo, anchor='nw')
        # 创建标签
        self.label1 = tk.Label(self.master, text="①专栏地址:", font=("黑体", 15))
        self.label1.place(relx=0.08, rely=0.05)
        self.label2 = tk.Label(self.master, text="暂无下载内容", justify="center", width=40, height=1, fg="black")
        self.label2.place(relx=0.2, rely=0.83)
        self.label3 = tk.Label(self.master, width=40, justify="center", height=1, fg="black", text="当前路径为："+self.address, anchor="w")
        self.label3.place(relx=0.2, rely=0.88)
        self.label4 = tk.Label(self.master, text="②空间地址:", font=("黑体", 15))
        self.label4.place(relx=0.08, rely=0.15)
        self.label5 = tk.Label(self.master, text=" 空间页数:", font=("黑体", 15))
        self.label5.place(relx=0.08, rely=0.25)
        # 创建输入框
        self.url1 = tk.StringVar()
        self.url2 = tk.StringVar()
        self.url3 = tk.StringVar()
        self.url3.set("1-3")
        self.entry1 = tk.Entry(self.master, width=30, textvariable=self.url1)
        self.entry1.place(relx=0.25, rely=0.05)
        self.entry2 = tk.Entry(self.master, width=30, textvariable=self.url2)
        self.entry2.place(relx=0.25, rely=0.15)
        self.entry3 = tk.Entry(self.master, width=6, textvariable=self.url3)
        self.entry3.place(relx=0.25, rely=0.25)
        # 创建按钮
        self.button1 = tk.Button(self.master, text="提交", font=("黑体", 20), height=1, command=self.sumit)
        self.button1.place(relx=0.75,rely=0.05)
        self.button2 = tk.Button(self.master, text="更\n改\n路\n径", font=("黑体", 15), height=4, command=self.addressChange)
        self.button2.place(relx=0.85,rely=0.04)
        self.button3 = tk.Button(self.master, text="提交", font=("黑体", 20), height=1, command=self.uiddownload)
        self.button3.place(relx=0.75, rely=0.15)

    def addressChange(self):
        address = tk.filedialog.askdirectory()
        if address != '':
            self.address = address  # 获得选择的路径
            self.label3.configure(text=f"当前路径为：{self.address}")

    def sumit(self,url='', address=''):
        try:
            self.label2.configure(text="正在下载中......")
            # 页面解析获得图片地址
            if url == '':
                url = self.entry1.get()
            resp = requests.get(url)
            page = BeautifulSoup(resp.text, "html.parser")
            imgs = page.find_all("img", class_=None)
            # 异步协程下载图片
            asyncio.run(self.main(imgs,address))

            self.time += 1
            self.label2.configure(text=f"{self.time}次下载已完成")
        except:
            self.label2.configure(text="地址输入错误！")

    async def main(self, imgs, address):
        tasks = []
        for img in imgs:
            src = img.get("data-src")
            name = src.split("/")[-1]
            src = "https:" + src
            tasks.append(asyncio.create_task(self.download(src, name, address)))
        await asyncio.wait(tasks)

    async def download(self, src, name, address):
        async with aiohttp.ClientSession() as session:
            async with session.get(src) as html:
                content = await html.read()     # 读取内容
                if address == '':
                    async with aiofiles.open(f"{self.address}/{name}", mode="wb") as f:
                        await f.write(content)
                else:
                    async with aiofiles.open(f"{address}/{name}", mode="wb") as f:
                        await f.write(content)

    def uiddownload(self):
        # 判断地址是否输入正确
        first_url = self.entry2.get()
        try:
            response = requests.get(first_url)
        except:
            self.label2.configure(text="地址输入错误！")
            return
        # url处理
        UID = first_url.split('/')[-1]
        # 预处理
        obj = re.compile('"id":(?P<id>\d+),"category.*?],"title":"(?P<title>.*?)","summary"')
        headers = {
            'referer': 'https://space.bilibili.com/9277299/article',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36'
        }

        flag = True  # 判断循环
        i = 0  # 页数
        page = self.entry3.get().split('-')
        start = int(page[0])
        end = int(page[1])
        while (flag):
            i += 1
            if i<start:
                continue
            if i>end:
                break
            flag = False
            second_url = 'https://api.bilibili.com/x/space/article?mid=' + UID + '&pn=' + str(
                i) + '&ps=12&sort=publish_time&jsonp=jsonp&callback=__jp1'
            resp = requests.get(second_url, headers=headers)
            resp.encoding = 'utf-8'
            ids = obj.finditer(resp.text)
            with ThreadPoolExecutor(30) as t:
                for id in ids:
                    address = self.address + '/' + id.group("title").replace('/','|').replace(':','|')
                    os.mkdir(address)
                    url = "https://www.bilibili.com/read/cv"+id.group("id")+"?spm_id_from=333.999.0.0"
                    t.submit(self.sumit(url=url,address=address))
                    flag = True



if __name__ == "__main__":
    bili = tk.Tk()
    bili.geometry("607x407+400+200")
    bili.resizable(width=False, height=False)   # 设置无法更改比例
    bili.title("B站专栏图片下载")
    bili.attributes("-alpha", 0.9)      # 设置透明度
    Application(master = bili)
    bili.mainloop()
