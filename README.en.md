# WeChat Sticker Studio

Turn one line about a group chat into a set of animated WeChat stickers. Badge Shrimp, the demo character, salutes so hard his employee badge smacks him in the chin.

![Badge Shrimp salutes](examples/badge-shrimp/album/表情/01.gif)

[See all 16 reactions](examples/badge-shrimp/preview.gif) · [Download the demo pack](https://github.com/DeaglePC/wechat-sticker-studio/releases/download/v1.0.0/badge-shrimp-wechat.zip) · [中文说明](README.md)

## Install in Codex

```text
Use $skill-installer to install https://github.com/DeaglePC/wechat-sticker-studio/tree/v1.0.0/skills/wechat-sticker-studio
```

In a fresh session, try this prompt:

> Use $wechat-sticker-studio to make 16 animated WeChat stickers for my hiking buddies. Our mascot is a sparrow who says “almost there” while unfolding a camp chair. Give it short Chinese captions.

The workflow pairs each sticker with a message someone could actually reply to. It creates a character reference, draws distinct animation keys, exports looping GIFs and prepares the album cover, panel icon, banner and per-sticker meanings. Image generation requires an image-capable session. The local animation and validation scripts use Pillow and Python 3.10+ and run via `uv`.

## Upload a draft

> Use $wechat-sticker-studio to upload this album to the official WeChat sticker portal. Let me scan the login code, fill in the draft and stop at the preview.

A compatible interactive browser must be able to attach local files. Codex inspects the current form, matches files with their meanings and checks what the page reports. Review submission is a separate instruction. The official entry point and local browser form have been exercised; signed-in drafts and review receipts must be checked in the actual creator session. [Upload guide in Chinese](skills/wechat-sticker-studio/references/wechat-upload.md)

## License

The [MIT license](LICENSE) covers code and documentation. Rights to the example artwork and the artwork inside the release ZIP are separately reserved. [Artwork notice](examples/badge-shrimp/ARTWORK.md)
