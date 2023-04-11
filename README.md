# Bilibili视频评论爬虫

Bilibili Comment Scraper 是一个 Python 脚本，用于批量爬取 Bilibili 多个视频的评论。此脚本使用 Selenium 和 BeautifulSoup 解析网页并提取评论数据。评论数据将按照视频 ID 保存到 CSV 文件中。
#### 好用的话记得给个star

## 安装
1. 安装 Python 3。
2. 安装所需的库。在命令行中输入以下命令：pip install selenium beautifulsoup4 webdriver-manager

## 使用
1. 将要爬取评论的视频 URL 列表放入名为 video_list.txt 的文件中，每行一个 URL。
2. 运行脚本：python Bilicomment.py（或pycharm等软件打开运行）
3. 根据看到"请登录，登录成功跳转后，按回车键继续..."提示后，请登录 Bilibili。登录成功并跳转后，回到代码，按回车键继续。
4. 等待爬取完成。每个视频的评论数据将保存到以视频 ID 命名的 CSV 文件中， CSV 文件位于代码文件同级目录下。
5. 输出的 CSV 文件将包括以下列：'计数', '隶属关系'（一级评论/二级评论）, '被评论者昵称'（如果是一级评论，则为“up主”）, '被评论者ID'（如果是一级评论，则为“up主”）, '昵称', '用户ID', '评论内容', '发布时间', '点赞数'。
6. 输出的 CSV 文件是utf-8编码，若乱码，请检查编码格式。

## 功能
1. 完整爬取全部一级和二级评论。输出文件将包含以下字段：隶属关系（一级/二级评论）、被评论者昵称、被评论者 ID、评论者昵称、评论者用户 ID、评论内容、发布时间、点赞数。
2. 断点续爬：中断后，爬虫可以根据 progress.txt 文件中的进度继续爬取。如果想要从头开始爬取，只需删除 progress.txt 文件即可。
3. 批量爬取多个视频的评论，把要爬取的网址写进video_list.txt即可，每个视频的评论都会输出一个以视频ID命名的CSV文件。

## 注意事项
1. 爬取速度可能较慢，因为脚本需要加载页面和评论。请耐心等待。
2. 爬取过程中请勿关闭浏览器窗口。
3. 请将浏览器窗口拉宽，避免悬浮视频小窗遮挡评论区
4. 因为B站存在评论数虚标，部分评论可能被封禁或隐藏，所以爬取到的评论数量通常小于标称数量。只要自己在网页中不断下滑看到的最后几条评论和代码爬取的最后几条数据相符合，所有评论就已被完整爬取了。
