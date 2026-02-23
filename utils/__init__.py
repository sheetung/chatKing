from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import io


class RankingImageGenerator:
    def __init__(self):
        self.width = 500
        self.item_height = 70
        self.header_height = 120
        self.footer_height = 60
        self.padding = 20
        
        self.bg_color = "#1a1a2e"
        self.card_bg = "#16213e"
        self.text_color = "#ffffff"
        self.accent_color = "#e94560"
        self.gold_color = "#ffd700"
        self.silver_color = "#c0c0c0"
        self.bronze_color = "#cd7f32"
        
        self._init_fonts()

    def _init_fonts(self):
        font_dir = Path("/usr/share/fonts")
        
        self.title_font = self._load_font(28, font_dir)
        self.rank_font = self._load_font(24, font_dir)
        self.name_font = self._load_font(18, font_dir)
        self.count_font = self._load_font(16, font_dir)
        self.date_font = self._load_font(14, font_dir)

    def _load_font(self, size: int, font_dir: Path) -> ImageFont.FreeTypeFont:
        font_paths = [
            font_dir / "truetype" / "noto" / "NotoSansCJK-Regular.ttc",
            font_dir / "opentype" / "noto" / "NotoSansCJK-Regular.ttc",
            font_dir / "noto-cjk" / "NotoSansCJK-Regular.ttc",
            font_dir / "truetype" / "dejavu" / "DejaVuSans.ttf",
        ]
        
        for path in font_paths:
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except Exception:
                    continue
        
        try:
            return ImageFont.truetype("NotoSansCJK-Regular.ttc", size)
        except Exception:
            return ImageFont.load_default()

    def _draw_rounded_rect(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple,
        radius: int,
        fill: str
    ):
        x1, y1, x2, y2 = coords
        draw.rounded_rectangle(coords, radius=radius, fill=fill)

    def _get_rank_style(self, rank: int) -> Dict[str, Any]:
        styles = {
            1: {
                "bg_color": "#2d1f3d",
                "border_color": self.gold_color,
                "medal_color": self.gold_color,
                "medal_text": "🥇",
                "highlight": True
            },
            2: {
                "bg_color": "#1f2d3d",
                "border_color": self.silver_color,
                "medal_color": self.silver_color,
                "medal_text": "🥈",
                "highlight": True
            },
            3: {
                "bg_color": "#3d2d1f",
                "border_color": self.bronze_color,
                "medal_color": self.bronze_color,
                "medal_text": "🥉",
                "highlight": True
            }
        }
        return styles.get(rank, {
            "bg_color": self.card_bg,
            "border_color": None,
            "medal_color": "#666666",
            "medal_text": str(rank),
            "highlight": False
        })

    def _draw_rank_item(
        self,
        draw: ImageDraw.ImageDraw,
        y_offset: int,
        rank: int,
        user_name: str,
        msg_count: int,
        max_count: int
    ):
        style = self._get_rank_style(rank)
        
        card_x = self.padding
        card_width = self.width - self.padding * 2
        card_rect = (card_x, y_offset, card_x + card_width, y_offset + self.item_height - 10)
        
        self._draw_rounded_rect(draw, card_rect, 12, style["bg_color"])
        
        if style["border_color"]:
            draw.rounded_rectangle(
                card_rect,
                radius=12,
                outline=style["border_color"],
                width=2
            )
        
        medal_x = card_x + 25
        medal_y = y_offset + (self.item_height - 10) // 2
        
        if style["highlight"]:
            draw.ellipse(
                (medal_x - 20, medal_y - 20, medal_x + 20, medal_y + 20),
                fill=style["medal_color"],
                outline="#ffffff",
                width=1
            )
            draw.text(
                (medal_x, medal_y),
                style["medal_text"],
                font=self.rank_font,
                fill="#ffffff",
                anchor="mm"
            )
        else:
            draw.ellipse(
                (medal_x - 18, medal_y - 18, medal_x + 18, medal_y + 18),
                fill="#333344",
                outline="#555566",
                width=1
            )
            draw.text(
                (medal_x, medal_y),
                str(rank),
                font=self.rank_font,
                fill="#aaaaaa",
                anchor="mm"
            )
        
        name_x = card_x + 70
        name_y = y_offset + 18
        display_name = user_name[:12] + "..." if len(user_name) > 12 else user_name
        draw.text(
            (name_x, name_y),
            display_name,
            font=self.name_font,
            fill=self.text_color
        )
        
        bar_x = name_x
        bar_y = y_offset + 45
        bar_width = 180
        bar_height = 12
        
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
            radius=6,
            fill="#333344"
        )
        
        if max_count > 0:
            progress = min(msg_count / max_count, 1.0)
            progress_width = int(bar_width * progress)
            if progress_width > 0:
                progress_color = style["medal_color"] if style["highlight"] else self.accent_color
                draw.rounded_rectangle(
                    (bar_x, bar_y, bar_x + progress_width, bar_y + bar_height),
                    radius=6,
                    fill=progress_color
                )
        
        count_x = card_x + card_width - 25
        count_y = y_offset + (self.item_height - 10) // 2
        draw.text(
            (count_x, count_y),
            f"{msg_count}",
            font=self.rank_font,
            fill=self.accent_color if not style["highlight"] else style["medal_color"],
            anchor="rm"
        )
        
        draw.text(
            (count_x, count_y + 20),
            "条",
            font=self.count_font,
            fill="#888888",
            anchor="rm"
        )

    def generate_ranking_image(
        self,
        ranking_data: List[Dict[str, Any]],
        title: str = "今日发言排行榜",
        date_str: Optional[str] = None
    ) -> bytes:
        num_items = len(ranking_data) if ranking_data else 1
        height = self.header_height + (self.item_height * num_items) + self.footer_height
        
        image = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        draw.text(
            (self.width // 2, 35),
            title,
            font=self.title_font,
            fill=self.text_color,
            anchor="mm"
        )
        
        if date_str:
            draw.text(
                (self.width // 2, 70),
                date_str,
                font=self.date_font,
                fill="#888888",
                anchor="mm"
            )
        else:
            draw.text(
                (self.width // 2, 70),
                datetime.now().strftime("%Y-%m-%d"),
                font=self.date_font,
                fill="#888888",
                anchor="mm"
            )
        
        draw.text(
            (self.width // 2, 95),
            "━" * 20,
            font=self.date_font,
            fill="#333344",
            anchor="mm"
        )
        
        if not ranking_data:
            y_offset = self.header_height + 20
            draw.text(
                (self.width // 2, y_offset + 30),
                "暂无发言记录",
                font=self.name_font,
                fill="#666666",
                anchor="mm"
            )
        else:
            max_count = ranking_data[0]["msg_count"] if ranking_data else 1
            
            for i, item in enumerate(ranking_data):
                y_offset = self.header_height + (i * self.item_height)
                self._draw_rank_item(
                    draw,
                    y_offset,
                    i + 1,
                    item["user_name"],
                    item["msg_count"],
                    max_count
                )
        
        footer_y = height - 35
        draw.text(
            (self.width // 2, footer_y),
            f"共 {len(ranking_data)} 位活跃成员",
            font=self.count_font,
            fill="#666666",
            anchor="mm"
        )
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", quality=95)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_image_bytes(
        self,
        ranking_data: List[Dict[str, Any]],
        title: str = "今日发言排行榜",
        date_str: Optional[str] = None
    ) -> bytes:
        return self.generate_ranking_image(ranking_data, title, date_str)
