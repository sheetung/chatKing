from __future__ import annotations

import sqlite3
import aiosqlite
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import asyncio


class ChatDatabase:
    def __init__(self, db_path: str = "chat_records.db"):
        self.db_path = db_path
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self):
        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:
                    await self._create_table()
                    self._initialized = True

    async def _create_table(self):
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chat_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    msg_time TEXT NOT NULL,
                    msg_id TEXT UNIQUE NOT NULL
                )
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_group_time ON chat_records(group_id, msg_time)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_msg_id ON chat_records(msg_id)
            ''')
            await db.commit()

    async def insert_record(
        self,
        group_id: str,
        user_id: str,
        user_name: str,
        msg_time: datetime,
        msg_id: str
    ) -> bool:
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR IGNORE INTO chat_records 
                    (group_id, user_id, user_name, msg_time, msg_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    group_id,
                    user_id,
                    user_name,
                    msg_time.strftime('%Y-%m-%d %H:%M:%S'),
                    msg_id
                ))
                await db.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    async def get_today_ranking(self, group_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        await self._ensure_initialized()
        
        today = date.today().strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute('''
                SELECT 
                    user_id,
                    user_name,
                    COUNT(*) as msg_count
                FROM chat_records
                WHERE group_id = ? AND DATE(msg_time) = ?
                GROUP BY user_id
                ORDER BY msg_count DESC
                LIMIT ?
            ''', (group_id, today, limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_date_range_ranking(
        self,
        group_id: str,
        start_date: date,
        end_date: date,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute('''
                SELECT 
                    user_id,
                    user_name,
                    COUNT(*) as msg_count
                FROM chat_records
                WHERE group_id = ? 
                    AND DATE(msg_time) >= ? 
                    AND DATE(msg_time) <= ?
                GROUP BY user_id
                ORDER BY msg_count DESC
                LIMIT ?
            ''', (
                group_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                limit
            ))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_range_ranking(
        self,
        group_id: str,
        days: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取从指定天数前到现在的排行榜
        days=1: 今天
        days=2: 昨天到今天
        days=3: 前天到今天
        """
        await self._ensure_initialized()
        
        # 计算开始日期
        start_date = (date.today() - timedelta(days=days-1)).strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute('''
                SELECT 
                    user_id,
                    user_name,
                    COUNT(*) as msg_count
                FROM chat_records
                WHERE group_id = ? 
                    AND DATE(msg_time) >= ?
                GROUP BY user_id
                ORDER BY msg_count DESC
                LIMIT ?
            ''', (
                group_id,
                start_date,
                limit
            ))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_old_records(self, days: int = 30) -> int:
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM chat_records
                WHERE DATE(msg_time) < DATE('now', ?)
            ''', (f'-{days} days',))
            await db.commit()
            return cursor.rowcount

    async def record_exists(self, msg_id: str) -> bool:
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT 1 FROM chat_records WHERE msg_id = ?',
                (msg_id,)
            )
            return await cursor.fetchone() is not None

    async def get_user_stats(self, group_id: str, user_id: str) -> Dict[str, Any]:
        await self._ensure_initialized()
        
        today = date.today().strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            
            cursor = await db.execute('''
                SELECT COUNT(*) as total_msgs
                FROM chat_records
                WHERE group_id = ? AND user_id = ?
            ''', (group_id, user_id))
            total_row = await cursor.fetchone()
            
            cursor = await db.execute('''
                SELECT COUNT(*) as today_msgs
                FROM chat_records
                WHERE group_id = ? AND user_id = ? AND DATE(msg_time) = ?
            ''', (group_id, user_id, today))
            today_row = await cursor.fetchone()
            
            return {
                'total_msgs': total_row['total_msgs'] if total_row else 0,
                'today_msgs': today_row['today_msgs'] if today_row else 0
            }
