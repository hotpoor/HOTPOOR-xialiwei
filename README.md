# HOTPOOR · XIALIWEI

**一些经历，一些实践，一次次把立场说清楚。**

这是 HOTPOOR · XIALIWEI 的个人记录。名字的来历、产品的初心、SayAgain 的实践，以及在具体事情里逐渐明白彼此立场的过程，都从这里慢慢积累。

## 阅读入口

- [网页版本 · 横向时间轴](https://github.xialiwei.com/HOTPOOR-xialiwei/)
- [History · 按时间正序](history/README.md)
- [News · 按时间逆序](news/README.md)
- [章节总目录](chapters/README.md)
- [逐篇 Markdown 原稿](content/stories/)

网页提供横向时间轴、正序与逆序阅读、章节目录、每篇正文目录与前后篇导航。History、News 每页 4 篇，随记录增长自动分页。网页无需 JavaScript 也可以阅读和导航。

## 章节

1. [名字与初心](chapters/origins/README.md)
2. [从校园走向创业](chapters/early/README.md)
3. [实时互动与真实交付](chapters/connected/README.md)
4. [产品、供应链与人群](chapters/exploration/README.md)
5. [把想法做出来](chapters/practice/README.md)
6. [让证据改变判断](chapters/evidence/README.md)
7. [在磨合中相互理解](chapters/dialogue/README.md)

## 记录原则

内容由本人讲述或来自已有公开项目记录，由 AI 协助整理，并由本人要求公开。本人自述、共同约定、项目核验和对话整理分别标明；证据链接优先固定到当时提交。原稿的正文保留来源和适用范围。

只知道年份时不补写日期；记录日不冒充事件起始日。同日条目按编辑顺序排列，不推断日内时间。横向时间轴节点等距排列，不按实际时间跨度缩放。本文档和首批文章整理于 2026-09-26。

## PDF 经历补充

2026-09-26 依据本人提供的《HOTPOOR+LAB 的基于人群覆盖论》新增 16 篇经历，来源页码为第 3—18 页。现共 23 篇、7 个章节，History / News 各 6 页。

原稿中校园配送、格斗机器人、FindMaster、爱味觉四项的“至今”，依本人要求暂按 **2026-09-26** 计，后续修正。目录保留 `source_date_label`、`date_end` 和 `date_end_provisional`；起始日期用于排序，不将整理日期当作项目开始日期。公开文章注明页码、历史自述属性及版本日期差异，省略第三方私人身份细节；原始 PDF 未公开上传。

## 文件夹

```text
content/
  catalog.json       日期、章节、摘要及阅读顺序
  stories/           逐篇 Markdown 原稿
history/             时间正序的 Markdown 分页
news/                时间逆序的 Markdown 分页
chapters/            章节总目录及各章 Markdown
assets/              网页样式、图标与时间轴交互
scripts/build.py     从原稿生成网页和 Markdown 阅读版
tests/               排序、分页、目录、链接与内容一致性检查
.github/workflows/   GitHub Pages 自动发布
```

## 更新与本地预览

编辑 `content/stories/` 内的原稿，并在 `content/catalog.json` 维护条目。日期精度可为 `YYYY`、`YYYY-MM` 或 `YYYY-MM-DD`。然后运行：

```sh
python -m pip install -r requirements.txt
python scripts/build.py
python -m unittest discover -s tests
python -m http.server 8000 --directory _site
```

访问 `http://localhost:8000`。生成的网页在 `_site/`，不提交；生成的 `history/`、`news/`、`chapters/` 与原稿一起提交。

主分支更新后，GitHub Actions 自动构建、检查并发布到 GitHub Pages。仓库 Settings → Pages 的 Source 使用 GitHub Actions。部署配置依据 [GitHub Pages 官方工作流说明](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

本站沿用账号已有的 Pages 域名 `github.xialiwei.com`，启用 HTTPS。默认的 `hotpoor.github.io/HOTPOOR-xialiwei/` 地址会跳转到该域名；站点公开地址保存在 `content/catalog.json` 的 `site_url` 中。

无需服务器、数据库或 AI API 凭证。
