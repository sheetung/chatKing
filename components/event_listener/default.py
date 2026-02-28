from __future__ import annotations

import os
import sys
import uuid
import requests
import json
import re
import tempfile
import base64
from datetime import datetime
from pathlib import Path

plugin_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(plugin_dir))

from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities import events, context
from langbot_plugin.api.entities.builtin.platform import message as platform_message
from langbot_plugin.api.entities.builtin.provider import message as provider_message

from database import ChatDatabase
from core.rank_generator import generate_rank_image


class DefaultEventListener(EventListener):
    
    async def initialize(self):
        await super().initialize()
        
        data_dir = plugin_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "chat_records.db"
        
        self.db = ChatDatabase(str(db_path))

        # 从插件配置中获取值，如果没有则使用默认值
        self.api_url = self.plugin.get_config().get('api_url', '')
        self.access_token = self.plugin.get_config().get('access_token', '')
        
        @self.handler(events.GroupMessageReceived)
        async def handler(event_context: context.EventContext):
            event = event_context.event
            message_chain = event.message_chain
            msg = str(message_chain).strip()
            # 获取群聊ID
            group_id = str(event.launcher_id)
            # 获取用户信息
            user_id = str(event.sender_id)
            user_name = user_id
            msg_id = str(event.message_id) if hasattr(event, 'message_id') else str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{group_id}_{user_id}_{msg}_{datetime.now().isoformat()}"))
            msg_time = datetime.now()

            # print(f'event: {event}')
            # print(f'group_id: {group_id}, user_id: {user_id}, user_name: {user_name}, msg_id: {msg_id}, msg_time: {msg_time}, msg: {msg}')
            # 解析 "1日发言榜"、"2日发言榜" 这样的命令格式
            match = re.match(r'(\d+)日发言榜', msg)
            if match:
                try:
                    days = int(match.group(1))
                    # 确保天数是正数
                    if days < 1:
                        days = 1
                except ValueError:
                    days = 1
                
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
        
        # 准备API请求所需的成员数据
        members = []
        for item in ranking_data:
            members.append({
                "nickname": item["user_name"],
                "qq": item["user_id"],
                "count": item["msg_count"]
            })
        
        # 生成排行榜图片
        image_content = generate_rank_image(f"群聊{group_id}", days, members, self.api_url, self.access_token)
        
        if image_content:
            # 将图片内容转换为base64编码
            base64_image = base64.b64encode(image_content).decode('utf-8')
            
            # 发送图片
            await event_context.reply(
                platform_message.MessageChain([
                    platform_message.Image(base64=base64_image)
                ])
            )
            event_context.prevent_default()
        else:
            # 如果生成图片失败
            await event_context.reply(
                platform_message.MessageChain([
                    platform_message.Plain(text="生成排行榜图片失败，请稍后重试")
                ])
            )
            event_context.prevent_default()
