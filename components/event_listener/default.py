from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

plugin_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(plugin_dir))

from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities import events, context
from langbot_plugin.api.entities.builtin.platform import message as platform_message

from database import ChatDatabase


class DefaultEventListener(EventListener):
    
    async def initialize(self):
        await super().initialize()
        
        plugin_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = plugin_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "chat_records.db"
        
        self.db = ChatDatabase(str(db_path))
        
        @self.handler(events.GroupMessageReceived)
        async def handler(event_context: context.EventContext):
            event = event_context.event
            message_chain = event.message_chain
            msg = str(message_chain).strip()
            
            group_id = str(event.group_id) if hasattr(event, 'group_id') else str(event.sender_id)
            user_id = str(event.sender_id)
            user_name = str(event.sender_name) if hasattr(event, 'sender_name') else user_id
            msg_id = str(event.message_id) if hasattr(event, 'message_id') else str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{group_id}_{user_id}_{msg}_{datetime.now().isoformat()}"))
            msg_time = datetime.now()
            
            if msg.startswith("rank"):
                # 解析命令参数
                parts = msg.split()
                days = 1  # 默认今天
                
                if len(parts) > 1:
                    try:
                        days = int(parts[1])
                        # 确保天数是正数
                        if days < 1:
                            days = 1
                    except ValueError:
                        pass
                
                await self._handle_rank_command(event_context, group_id, days)
                event_context.prevent_default()
                return
            
            await self.db.insert_record(
                group_id=group_id,
                user_id=user_id,
                user_name=user_name,
                msg_time=msg_time,
                msg_id=msg_id
            )

    async def _handle_rank_command(self, event_context: context.EventContext, group_id: str, days: int = 1):
        ranking_data = await self.db.get_range_ranking(group_id, days=days, limit=10)
        
        if not ranking_data:
            if days == 1:
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text="今日暂无发言记录")
                    ])
                )
            else:
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text=f"近{days}天暂无发言记录")
                    ])
                )
            return
        
        # 使用文本形式返回排行榜
        if days == 1:
            rank_text = "今日发言排行榜\n"
        else:
            rank_text = f"近{days}天发言排行榜\n"
        
        rank_text += "====================\n"
        
        for i, item in enumerate(ranking_data, 1):
            user_name = item["user_name"]
            msg_count = item["msg_count"]
            
            if i == 1:
                rank_text += f"🥇 第{i}名: {user_name} - {msg_count}条\n"
            elif i == 2:
                rank_text += f"🥈 第{i}名: {user_name} - {msg_count}条\n"
            elif i == 3:
                rank_text += f"🥉 第{i}名: {user_name} - {msg_count}条\n"
            else:
                rank_text += f"📊 第{i}名: {user_name} - {msg_count}条\n"
        
        rank_text += "====================\n"
        rank_text += f"共{len(ranking_data)}位活跃成员"
        
        await event_context.reply(
            platform_message.MessageChain([
                platform_message.Plain(text=rank_text)
            ])
        )
