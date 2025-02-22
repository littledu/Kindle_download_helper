# Kindle_download_helper
Download all your kindle books script.


<img width="1661" alt="image" src="https://user-images.githubusercontent.com/15976103/172113700-7be0ae1f-1aae-4b50-8377-13047c63411b.png">


# 准备

1. python3
2. pip
3. pip install -r requirements.txt

# 使用 `amazon CN`

1. 登陆 amazon.cn
2. 访问 https://www.amazon.cn/hz/mycd/myx#/home/content/booksAll/dateDsc/
3. 右键查看源码，搜索 `csrfToken` 复制后面的 value
4. 执行 `python3 kindle.py ${csrfToken} --cn`

# how to `amazon.com`
1. login amazon.com
2. visit https://www.amazon.com/hz/mycd/myx#/home/content/booksAll/dateDsc/
3. right click this page source then find `csrfToken` value copy
4. run: `python3 kindle.py ${csrfToken}`

# 手动输入 cookie

若默认情况下提示 cookie 无效，你也可以手动输入 cookie 。方法是在上述全部书籍列表页面，按 <kbd>F12</kbd> 或右键点击——检查，进入控制台(Console)，输入 `document.cookie`，回车。复制输出的结果即可。

然后，执行 `python3 kindle.py --cookie ${cookie} ${csrfToken}`。

你也可以把 cookie 保存为文本文件，执行 `python3 kindle.py --cookie-file ${cookie_file} ${csrfToken}` 下载书籍。

# 注意
- cookie 和 csrf token 会过期，重新刷新下 amazon 的页面就行
- 书会下载在 DOWNLOADS 里
- 如果你用 [DeDRM_tools](https://github.com/apprenticeharper/DeDRM_tools) 解密 key 存在 key.txt 里
- 或者直接拖进 Calibre 里 please google it.
- 如果过程中失败了可以使用 e.g. `--recover-index ${num}`
- 如果出现名字太长的报错可以增加: `--cut-length 80` 来截断文件名

<img width="1045" alt="image" src="https://user-images.githubusercontent.com/15976103/172113475-92862b57-bb39-4cd7-84d5-6bc428172bc4.png">


# Enjoy
# 赞赏

- 谢谢就够啦
- 分享给需要的人就更好了
 
