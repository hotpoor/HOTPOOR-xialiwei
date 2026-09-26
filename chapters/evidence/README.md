# 让证据改变判断

[返回章节目录](../README.md)

保留核验的方法、结果与适用范围。

## 目录

- [2026-09-25 · 从识别效果，追到模型来源](#2026-09-25-model-evidence)

---

<a id="2026-09-25-model-evidence"></a>

## 从识别效果，追到模型来源

2026.09.25 · 核验日期 · 项目核验 · 整理于 2026-09-26

[独立原稿](../../content/stories/2026-09-25-model-evidence.md) · [网页阅读](https://hotpoor.github.io/HOTPOOR-xialiwei/stories/2026-09-25-model-evidence/index.html)

### 从一个具体效果开始

做 SayAgain 时，我们关注语音识别结果能否成为方便阅读的书面表达：有没有标点、英文大小写是否合适、文字数字能否变成数字。

一次输出差异推动我们继续追查。Windows 当时使用的粤语微调模型，在同一英文样例中输出全大写、没有标点；替换模型文件后，结果出现正常大小写和句末句号。

这让我们从使用体验继续走到模型来源、文件核验和同环境对照。

### 先把文件核实

2026 年 9 月 25 日的项目记录确认：本次核验的 **PatchxNote 1.0.2（21）**，内置模型包名为 `patchnote-standard 0.2.0`。其中的 `model.int8.onnx` 与官方 sherpa-onnx `2024-07-17` 通用 INT8 文件大小及完整 SHA-256 一致。

- 文件大小：239233841 字节。
- SHA-256：`c71f0ce00bec95b07744e116345e33d8cbbe08cef896382cf907bf4b51a2cd51`。

**这份已核验样本使用的是同一份官方通用模型文件。** 应用包名、模型来源和产品集成分别记录。

### 再把效果核实

项目使用统一条件，对四个来源、三种语言及 ITN 开关组合完成了 24 次推理。官方通用版与 Freenote / PatchxNote 样本的输出 token 一致。

没有外部大小写转换、正则处理或 AI 润色，官方通用模型在公开样例中已经表现出：

- 英文句首大写和句末标点。
- `fifty` 转为 `50`。
- 中文时间里的“九点”“五点”转为“9点”“5点”。

这些结果说明上游模型已经具备本次样例所体现的能力。记录中还有独立推理调用的交叉核对，以及禁止测试进程联网后的输出核对。

### 让结论停在证据能到达的地方

文件结论对应已核验版本和文件，不延伸到其他版本、云端模型或厂商动机。相同模型也不意味着两款应用的完整体验相同：分段、上下文、说话人处理和其他产品工作仍需分别观察。

百分比、日期、金额、小数与长数字专项测试，当时仍列为待验证。不能把示意性的“ten percent → 10%”写成已经完成的测试结果。

我们在项目中保留了商业化硬件和应用集成的推荐，也明确上游模型来源。认可具体产品工作与准确记录模型来源，可以同时做到。

### 公开证据

- [模型来源、大小、完整指纹与核验范围](https://github.com/hotpoor/HOTPOOR-SayAgain/blob/ebc91fc8423fc00dd4be70412ef20b0883d90c03/docs/model-provenance.md)
- [四来源公开样例原样输出](https://github.com/hotpoor/HOTPOOR-SayAgain/blob/ebc91fc8423fc00dd4be70412ef20b0883d90c03/docs/sensevoice-four-source-results.md)
- [Windows 同环境模型对照](https://github.com/hotpoor/HOTPOOR-SayAgain/blob/ebc91fc8423fc00dd4be70412ef20b0883d90c03/docs/sensevoice-model-comparison.md)
- [产品推荐与来源说明](https://github.com/hotpoor/HOTPOOR-SayAgain/blob/ebc91fc8423fc00dd4be70412ef20b0883d90c03/docs/patchx-freenote.md)

本文于 2026 年 9 月 26 日依据已有公开项目记录整理，不代表当天重新运行了模型测试。
