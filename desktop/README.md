# HOTPOOR 记录：公开与加密写作客户端

客户端有独立 Electron 窗口，不依赖 Hotpoor Director 运行。它在本机编辑正文，输入口令后在浏览器进程中加密，只把密文与公开目录提交到此仓库。GitHub Pages 使用同一口令在访问者浏览器中解密。

## 本机准备

需要 Node 22.12+、Python 3.10+、Git。执行 `npm install` 安装桌面组件，`python -m pip install -r requirements.txt` 安装站点构建依赖，然后用 `npm start` 或 Windows 的 `Start_Archive.bat` 打开。当前为源码桌面客户端，尚未制作独立分发安装包。

在忽略提交的 `.local/archive-client.json` 配置当前记录：

```json
{
  "id": "2026-09-27-perspective",
  "title": "2026 年 9 月 27 日的记录",
  "summary": "一份加密记录，输入口令后阅读。",
  "date": "2026-09-27",
  "chapter": "dialogue",
  "draft": "/private/outside-repository/draft.md",
  "python": "python",
  "node": "node",
  "github_token_file": "/private/outside-repository/github.token"
}
```

示例路径需换成本机实际位置；私密草稿必须在仓库外。首次使用从私密文件载入草稿；已有密文时先输入口令解密，不自动用最初草稿覆盖后续版本。左侧通过“公开 / 加密”两个标签页区分文档。文档列表自动载入本地草稿、密文记录及仓库公开文章，支持标题搜索、新建加密记录与切换；公开文章支持直接编辑，并先保存为本地草稿。未加密保存的修改会阻止切换，避免误丢。每篇记录使用独立的本机状态文件。

## GitHub 设置

左侧展开“GitHub 设置”，可填写 Access Token 文件的绝对路径，或点击“选择文件…”定位本机文件，再点“保存位置”。这里只填写路径，不粘贴 Token 内容；文件必须在仓库外。设置只写入忽略提交的本地配置。界面显示文件是否存在，不展示或读取 Token 内容；实际发布时由本机程序读取。

## 公开记录

在“公开”标签页新建记录，或选择已有文章编辑。无需输入口令，点击顶部“保存草稿”将正文保存在仓库外的本地草稿目录；保存不会自动公开。点击“发布公开记录”后才写入仓库 Markdown、更新目录、验证并同步 GitHub。修改历史文章时保留原有日期精度、来源、章节和其他目录信息。发布完成后核对在线正文。

## 加密记录

1. 编辑正文，核对将公开的标题和说明。
2. 输入同一口令两次，点击顶部“加密保存”。建议使用较长且独有的口令；客户端要求至少 12 个字符。
3. 客户端核对加解密结果后，仅把密文写入 `content/encrypted/`，清空编辑区和口令框。口令不发给本机服务、不保存到文件或浏览器持久存储。原始私密草稿仍留在仓库外。
4. 点击顶部“发布密文”。本机程序生成公开占位文章和目录，运行检查，提交本篇、获取并合并远端 main、推送并核对提交。其他尚未发布的密文可留在本机；发现其他代码、公开目录改动或已暂存的无关文件时停止，不混入本篇。
5. 发布状态分别报告推送与 Pages 部署。只有 Actions 成功且在线密文与本机一致，才显示发布已核对。网络或部署失败时保留本地文件和已完成的提交。

GitHub Token 只在本机进程内读取；HTTPS 认证头仅用于确认过的 GitHub 目标，不写入 Git 配置。网页没有 GitHub 凭证，也没有密码验证服务器。

## 加密与边界

使用 AES-256-GCM、每次新生成的 12 字节 nonce 和 16 字节盐、PBKDF2-HMAC-SHA256 600000 次派生；认证数据绑定记录 ID。桌面和网页采用浏览器 Web Crypto，命令行工具使用 Node 标准库，测试验证两端互通。依据：[Web Crypto 口令派生](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/deriveKey)、[AES-GCM](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/encrypt)。

公开标题、日期、说明、密文大小和修改历史可见。加密不等于编码，也不等于把正文藏在 HTML 中；构建只读取公开占位稿与密文，不读取私密草稿。解密内容以文本节点显示，不执行正文中的 HTML 或脚本。

口令丢失无法由网站恢复。Git 会保留旧密文；改口令不能撤回持有旧口令的人对旧版本的访问。阅读端仍需可信浏览器和页面脚本；不能承诺防止本机恶意软件、已解密后的复制或截图。锁定会清空页面内容和输入框，不宣称能彻底擦除 JavaScript 运行时的全部内存副本。

维护原稿时可用 `scripts/encrypt-story.cjs`，明文和口令文件都必须在仓库外；命令行参数只传文件路径，不传口令内容。客户端本机服务仅监听回环地址，校验 Host、Origin 与每次启动的请求令牌，只接受规定的密文字段。

## 验证

- `python scripts/build.py`
- `python -m unittest discover -s tests`
- `node scripts/test-encryption.cjs`
- `electron scripts/test-client.cjs`：使用独立虚构草稿，检查客户端编辑、仅上传密文、错误口令、网页解密、安全显示与重新锁定；不读取用户草稿或口令，不调用 GitHub 写接口。

本机组件与配置不提交，前端加密测试进入 Pages CI。网页构建不部署客户端、编辑服务或本地配置。
