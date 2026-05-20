# astrbot_plugin_html2image

让 AI 通过 HTML / SVG 代码绘制图像，返回 PNG 图片。

## 功能

注册一个 LLM Tool `draw_by_chrome`，AI 调用时传入 HTML 或 SVG 代码，插件使用 Playwright + Chromium 将代码渲染为 PNG 图片并返回。

- 自动识别代码类型（`<svg>` 或 `<html>`），无需手动指定模式
- 支持透明背景
- 可配置设备像素比（控制清晰度）

## 安装

将插件放入 AstrBot 的 `data/plugins/` 目录下，重启或通过插件管理面板载入。

### 依赖

需要系统安装 Chromium 以及 Python 包 `playwright`：

```bash
pip install playwright
playwright install chromium
```

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `checker` | bool | `false` | 开启后检查代码是否包含 `<svg>` 或 `<html>` 标签 |
| `device_scale_factor` | int | `2` | 设备像素比，值越大图片越清晰，资源消耗也越大 |

## 使用

AI 调用 `draw_by_chrome` 工具时传入以下参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `code` | str | 必填 | HTML 或 SVG 代码，需包含对应的根标签 |
| `width` | int | `3200` | 输出图片宽度 |
| `height` | int | `2400` | 输出图片高度 |
| `transparent_bg` | bool | `false` | 是否使用透明背景 |

### 示例 Prompt

```
用 SVG 画一个蓝色圆形，直径 200
```

AI 会自动生成 SVG 代码并调用 `draw_by_chrome`。

## 许可

参见 [LICENSE](./LICENSE)
