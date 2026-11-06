# 让 Codex 在浏览器里上传

这个流程面向电脑端微信表情开放平台的**动态表情专辑**。先确定用户要哪一种结果，再操作。用户问“需要哪些步骤”时给说明。用户说“帮我上传/填草稿”时实际打开浏览器、上传到预览；说“提交审核”时在核对后送审一次。预约上架按用户明确指定的时间和时区操作。创建专辑本身不包含上述外部操作。

## 1. 在本地准备这一轮上传

先跑 [投稿目录校验](package.md)，把本次成功生成的 JSON 留在本机。仅上传清单列出的素材。以登记的创作者为准填写署名、版权或授权资料；作品由 AI 生成时按实际范围主动声明，使用平台提供的标识功能。例如本例可填「本专辑角色及关键画面由 AI 生成，人物为虚构形象。」如果需要作者声明而页面没有可见入口，检查平台说明，向作者指出未解决的字段，不擅自勾选与事实不符的选项。[微信作品审核标准](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/auditingStandards#auditingStandards_demand) · [生成合成内容标识办法第十条](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm)

## 2. 打开官方页面，延续同一会话

优先用宿主提供的可交互浏览器。它需要能展示页面、支持本人扫码、上传本机文件。先打开 **https://sticker.weixin.qq.com/**，从当前页面的登录或工作台入口进入，读页面快照。若环境有 ego-browser，先执行 `ego-browser skill`，再运行下面的实际导航；保留输出的空间编号。其他浏览器工具按同样步骤执行。只有网页搜索能力时，交付已校验的素材并说明需要支持本地文件上传的浏览器。

```sh
ego-browser nodejs <<'JS'
const task = await taskSpace("微信表情专辑投稿");
const page = task.page("p1");
await page.goto("https://sticker.weixin.qq.com/");
console.log(task.spaceId, await page.snapshot());
JS
```

登录或实名时，把该会话交给账号本人扫码或填证件；完成后恢复同一页面。用 ego-browser 时按工具指南使用 `task.handOff()` 和 `takeOverTaskSpace(空间编号)`。个人注册公开指引列有邮箱、手机号、有效的中国大陆居民身份证及正反面图片、绑定银行卡的微信；企业账号按企业指引准备资料。证件和微信凭据由用户直接交给官网处理。[个人注册指引](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/loginGuides#loginGuides_personage)

## 3. 找到对应草稿，分栏上传

- 确认当前账号是用户要投稿的账号。先查是否已经存在同名草稿、待审核或已上架作品。只有标题相同但封面、张数或编号对应不上时，先核实作品身份。需要另建时，从投稿入口选择「表情专辑」，以当前后台显示为准。
- 打开每个栏目时重新读取标签、按钮、文件输入框和实际限制。找到**表情主图**栏目，支持多选时按清单一批选入；单文件控件就逐项选择当前空槽，每次等到编号或缩略图出现再继续。失败时只补缺失项。
- 将 `cover.file`、`icon.file`、`banner.file` 单独传给平台对应栏目。确认封面为角色半身、图标为头像、横幅为宽图。台词、含义词按照页面当前缩略图顺序逐一核对。若前端按文件名重排，重新按两位编号配对。
- 名称、介绍来自清单。每张含义词用 `meaning` 字段。涉及账号归属、权利、价格、赞赏或 AI 声明的选项按真实情况和用户选择填。逐项处理页面标红或提示的必填项。

例如以下代码运行在 **ego-browser 的 Node 端**。把清单路径、空间编号和定位器替换为当前会话读到的值；根据页面实际能力分步执行。定位器须对应**该栏唯一的文件控件**。如果页面使用按钮触发文件选择器，先调用 `waitForFileChooser`，再点已定位的上传按钮，最后 `setFiles`。使用其他浏览器工具时采用其文件选择器接口。

```js
const { readFile } = await import("node:fs/promises");
const plan = JSON.parse(await readFile(本轮清单的绝对路径, "utf8"));
const task = await taskSpace(本轮空间编号);
const page = task.page("p1");
await page.setInputFiles(已核对且支持多选的主图控件, plan.stickers.map(s => s.file));
// 等当前页面的上传进度结束，检查数量与缩略图，再处理封面。
await page.setInputFiles(已核对的封面控件, [plan.cover.file]);
```

**可执行的 Ego 适配器。** 已安装 ego-browser 时，也可用随包脚本代替上面的导航和文件选择代码。第一条返回空间号并列出页面；第二条中的空间号、页面标签和 CSS 都必须来自本次在官网实际观察的空控件。适配器只向微信表情开放平台的 HTTPS 页面附加已校验文件，提交和表单回显仍由 Codex 按本手册逐步处理。

```sh
uv run --script "$SKILL_DIR/scripts/ego_upload.py" open
uv run --script "$SKILL_DIR/scripts/ego_upload.py" attach \
  --manifest 工作/upload-plan.json --space "$SPACE" --page "$PAGE" \
  --field stickers --selector "$INSPECTED_FILE_INPUT_CSS"
```

可用字段为 `stickers`、`cover`、`icon`、`banner`。单文件槽位或断点补传时用 `--field stickers --id 03`。控件在 iframe、Shadow DOM 或只通过文件选择器可见时，改用宿主的交互式上传工具。已保存的远端缩略图可能对应空的 HTML 输入框，调用前一定要看该槽位的实际页面回显。

## 4. 预览、保存和送审

预览时核对账号、专辑名、首尾图、总数、三张配套图和全部含义词。用户只授权上传草稿时，若支持就保存草稿，保留便于用户接手的页面。页面没有保存回执时准确说“已填到预览页”，并说明页面是否需要保持打开。

用户已明确要求提交审核，且作品、署名、权属声明与资费设置均清楚时，按当前页面提示**提交一次**。等待明确的「待审核」「审核中」或等价回执，记录可见的专辑名和状态。遇到断线、转圈、返回页或重复提交提示，先去作品列表查同一专辑的状态；结果仍不明时报告待核对，暂停重复提交。登录失效则交回原会话。不得为了通过表单而伪造任何作者或权属信息。

通常审核结果在五个工作日内反馈，实际由平台排队决定。通过后在作品后台查看可选上架安排。汇报时说明本地验证、文件上传、草稿保存、送审和上架中**实际到达的那一步**。[微信审核常见问题](https://sticker.weixin.qq.com/cgi-bin/mmemoticon-bin/readtemplate?t=guide/index.html#/commonQuestions#commonQuestions_register)

**可复制的两种指令**

> 用 $wechat-sticker-studio，将我选定的投稿目录上传到微信表情开放平台。需要扫码时叫我，上传完成后停在预览页。

> 用 $wechat-sticker-studio，继续这个已核对的草稿，以当前确认的作者署名提交审核，告诉我后台显示的状态。
