import os
import uuid
import tempfile
from pathlib import Path
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

from astrbot.api.message_components import Image as Comp_Image
from playwright.async_api import async_playwright


@register("html2image", "BUGJI", "让 AI 通过 HTML/SVG 代码绘制图像", "1.0.2")
class html2image(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.temp_dir = tempfile.gettempdir()
        self.config = config
        self.checker = self.config.get("checker", False)
        self.device_scale_factor = self.config.get("device_scale_factor", 2)
        self.max_dimension = self.config.get("max_dimension", 20000)  # 最大分辨率限制
    async def initialize(self):
        """插件初始化"""
        logger.info("HTML2Image 插件已初始化")

    async def _svg_to_png(self, code: str, width: int = 3200, height: int = 2400,
                          transparent_bg: bool = False) -> str:
        filename = f"svg_{uuid.uuid4().hex}.png"
        output_path = os.path.join(self.temp_dir, filename)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=self.device_scale_factor
            )
            page = await context.new_page()
            
            bg_style = "transparent" if transparent_bg else "white"
            
            # 关键：通过 CSS 强制 SVG 块级化并居中
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    html, body {{
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        height: 100%;
                        background: {bg_style};
                    }}
                    body {{
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    svg {{
                        display: block;
                        width: 100%;
                        height: 100%;
                        /* 如果需要保持原始比例，取消下面的注释并注释上面两行 */
                        /* max-width: 100%;
                        max-height: 100%;
                        width: auto;
                        height: auto; */
                    }}
                </style>
            </head>
            <body>
                {code}
            </body>
            </html>
            """
            
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")
            
            # 可选：等待 SVG 完全渲染
            await page.wait_for_timeout(100)  # 短暂等待确保布局完成
            
            await page.screenshot(
                path=output_path,
                type="png",
                full_page=False,
                omit_background=transparent_bg

            )
            
            await browser.close()
        
        return output_path
    
    async def _html_to_png(self, code: str, width: int = 3200, height: int = 2400,
                          transparent_bg: bool = False) -> str:
        filename = f"html_{uuid.uuid4().hex}.png"
        output_path = os.path.join(self.temp_dir, filename)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=self.device_scale_factor
            )
            page = await context.new_page()
            
            bg_style = "transparent" if transparent_bg else "white"
            
            # 关键：通过 CSS 强制 HTML 块级化并居中
            html_content = f"""
            <!DOCTYPE html>
            {code}
            """
            
            await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")
            
            # 可选：等待 HTML 完全渲染
            await page.wait_for_timeout(100)  # 短暂等待确保布局完成
            
            await page.screenshot(
                path=output_path,
                type="png",
                full_page=False,
                omit_background=transparent_bg

            )
            
            await browser.close()
        
        return output_path
    
    @filter.llm_tool(name="draw_by_chrome", description="根据 HTML/SVG 代码绘制图像，返回 PNG 图片，使用 Chromium 渲染图片")
    async def draw_by_chrome(self, event: AstrMessageEvent, 
                       code: str,
                       width: int = 3200,
                       height: int = 2400,
                       transparent_bg: bool = False):
        """
        根据 HTML/SVG 代码绘制图像并生成 PNG 图片

        Args:
            code(str): HTML/SVG 格式的图像代码，从对应标签开始，会自动识别是 HTML 还是 SVG
            width(int): 输出图片的宽度（分辨率），默认 3200
            height(int): 输出图片的高度（分辨率），默认 2400
            transparent_bg(bool): 是否使用透明背景，默认 false（白色背景）
        """
        
        logger.debug(f"接收到绘制请求")
        try:
            # 验证 HTML/SVG 代码
            if self.checker:
                if not code or ("<svg" not in code.lower() and "<html" not in code.lower()):
                    yield f"错误：未检测到有效的 HTML(<html>) 或 SVG(<svg>) 标签，请确保代码包含对应的根标签"
                    return

            # 限制最大分辨率
            max_dimension = self.max_dimension
            width = min(width, max_dimension)
            height = min(height, max_dimension)
            
            logger.debug(f"开始转换 HTML/SVG 为 PNG，宽度={width}, 高度={height}, 透明背景={transparent_bg}")
            if "<svg" in code.lower():
                # 转换 SVG 为 PNG
                png_path = await self._svg_to_png(
                    code=code,
                    width=width,
                    height=height,
                    transparent_bg=transparent_bg
                )
            elif "<html" in code.lower():   
                # 转换 HTML 为 PNG
                png_path = await self._html_to_png(
                    code=code,
                    width=width,
                    height=height,
                    transparent_bg=transparent_bg
                )
            else:
                yield f"错误：未检测到有效的 HTML(<html>) 或 SVG(<svg>) 标签，请确保代码包含对应的根标签"
                return
            
            # 检查文件是否生成成功
            if os.path.exists(png_path):
                # 发送图片到用户
                yield event.image_result(png_path)
                logger.info(f"HTML/SVG 图片已生成：{png_path} ({width}x{height}, transparent={transparent_bg})")
            else:
                yield f"错误：图片生成失败，文件未成功创建。"
                
        except Exception as e:
            logger.error(f"HTML/SVG 转 PNG 失败：{str(e)}")
            yield f"错误：图片生成失败 - {str(e)}"


    async def terminate(self):
        """插件销毁"""
        logger.info("HTML2Image 插件已终止")
