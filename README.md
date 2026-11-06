# 微信表情包工坊 · WeChat Sticker Studio

给 Codex 一句群聊人设，做出一整套能发的微信 GIF。下面是「工牌虾」的三张成品。它有一张比脸还大的工牌，上班嘴硬，出事真顶。

| 同事发来「文件按这版走」 | 同事问「这会儿能帮我顶一下吗」 | 同事说「今天就到这儿」 |
| :---: | :---: | :---: |
| ![工牌虾敬礼，大工牌弹到下巴](examples/badge-shrimp/album/表情/01.gif) | ![工牌虾抓起蓝工牌挡在身前](examples/badge-shrimp/album/表情/11.gif) | ![工牌虾飞奔出门，回头挥手](examples/badge-shrimp/album/表情/16.gif) |

**[看完整 16 张动图](examples/badge-shrimp/preview.gif)** · **[下载工牌虾示例 ZIP](https://github.com/DeaglePC/wechat-sticker-studio/releases/download/v1.0.0/badge-shrimp-wechat.zip)** · [English](README.en.md)

## 把这句话发给 Codex

先安装 Skill。复制下面这行到 Codex，安装完成后打开新会话。

```text
用 $skill-installer 安装 https://github.com/DeaglePC/wechat-sticker-studio/tree/v1.0.0/skills/wechat-sticker-studio
```

然后试试你自己的角色。**写清谁发给谁、主角有什么脾气，再给它一个会惹事的道具。**

```text
用 $wechat-sticker-studio 给周末爬山搭子做 16 张微信动图：主角是一只嘴上说“快到了”、每次都偷偷掏出折叠凳的山雀。
```

Codex 会先编出 16 句能接上话的回复，固定角色母版，再给每张画起势、动作高峰和收势。你会拿到独立循环 GIF、整套预览、专辑封面、聊天图标、详情页横幅，以及按编号整理好的含义词和投稿 ZIP。

## 为什么从群聊的上一句开始

「画一只虾，表情是感激」很难判断画对了没有。换成「同事说：误删的那版我给你找回来了」，这只嘴硬的虾可以双手合十、高举过头，再夸张地鞠个躬。图上四个字就够了：**救我虾命**。

想看一张图怎么动起来，可以对照「收到」的 [三格关键姿势](examples/badge-shrimp/salute-keys.png) 和 [最终 GIF](examples/badge-shrimp/album/表情/01.gif)。想做下一套，可以看 [16 张完整分镜](examples/badge-shrimp/storyboard.json)，把里面的对话换成你们群里真的会说的话。

## 让 Codex 帮你上传到微信

```text
用 $wechat-sticker-studio 把刚做好的专辑上传到微信表情开放平台，需要扫码时叫我，填完停在预览页。
```

Codex 先核对 GIF、尺寸、文件体积和文案，再打开微信官网。你在自己的浏览器里扫码；登录后，Codex 按编号上传，填写含义词，检查缩略图与预览。如果你还想送审，可以继续说「以刚确认的作者署名提交审核，告诉我后台显示的状态」。制作、上传草稿、送审都可以单独使用。[浏览器投稿手册](skills/wechat-sticker-studio/references/wechat-upload.md)

首版验证了微信官网入口，并用真实浏览器在本地模拟表单回读了 16 张主图、16 个含义词和三张配套图。真实账号的登录后表单、草稿保存和审核回执由每次操作时核对。

## 在本地试跑

生成画面需要 Codex 会话可用的图像工具。文件工具可用 `uv` 直接运行，或使用 Python 3.10+ 和 Pillow。上传需要能选择本机文件的交互式浏览器；提供了可选的 ego-browser 适配器。

从仓库根目录运行下面两条，就能用示例数据试做一张无字动图，并检查整套专辑。

```sh
uv run --script skills/wechat-sticker-studio/scripts/animate.py \
  examples/badge-shrimp/salute-keys.png output/salute.gif

uv run --script skills/wechat-sticker-studio/scripts/album.py \
  examples/badge-shrimp/album \
  --manifest output/upload-plan.json --zip output/badge-shrimp.zip
```

带中文台词时加 `--caption 收到 --font /path/to/font.otf`，选用有相应授权的中文字体。上传清单含本机绝对路径，留在本地即可。

**许可** · 代码与文档采用 [MIT](LICENSE)。工牌虾的角色图、GIF、横幅及打包的示例美术单独保留权利；欢迎使用 Skill 制作自己的角色。[示例美术说明](examples/badge-shrimp/ARTWORK.md)
