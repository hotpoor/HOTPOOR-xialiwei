# HOTPOOR-xialiwei 维护约定

这是本人授权公开的故事与实践记录，使用 GitHub Pages。保留原意，区分本人自述、共同约定、项目核验与对话整理。不猜测历史日期，不公开凭证、私人路径、录音、聊天截图或第三方私人信息。

## 内容与生成

- `content/stories/` 是逐篇 Markdown 原稿；`content/catalog.json` 保存目录、日期精度、章节与摘要。
- `history/`、`news/`、`chapters/` 是生成的 Markdown 阅读目录；`_site/` 为忽略提交的网页产物。
- 修改原稿和目录后执行 `python scripts/build.py`、`python -m unittest discover -s tests` 与 `git diff --check`。不要仅修改生成目录。
- 同日内容按 catalog 的编辑顺序排列，不代表已经确认日内发生时间。只知年份时保留年份精度。
- 公开证据优先链接固定提交，保留其范围和后来更正，不把某个版本文件结论扩大成动机或全部产品结论。
- 网页与 Markdown 使用同一份原稿；History 正序，News 为其严格逆序。每页 4 篇，可在 catalog 调整。
- 主分支推送后由 GitHub Actions 生成、验证并部署 Pages。发布后检查部署状态和公开页面，再报告上线。

在 J:/codex_projects 工作时同时遵守上层 AGENTS.md 与 SHARED_VALUES.md。没有必要为本静态阅读网站引入 AI 服务。
