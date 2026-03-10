"""
提醒调度服务
处理一次性记事和周期性记事的邮件提醒
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import select, and_, or_
from models.database import async_session, Memo, ElderlyInfo
from tools.email import email_service


class ReminderScheduler:
    """提醒调度器"""
    
    async def get_one_time_memos_to_remind(self) -> List[Memo]:
        """获取当前需要提醒的一次性记事
        
        检查条件：
        1. reminder_time 在当前时间前5分钟到当前时间（已过期但不久）
        2. reminder_time 在当前时间后5分钟内（即将到期）
        """
        now = datetime.now()
        # 提醒时间窗口：当前时间前5分钟到当前时间后5分钟
        # 这样可以捕获刚刚过期的和即将到期的
        start_time = now - timedelta(minutes=5)
        end_time = now + timedelta(minutes=5)
        
        async with async_session() as session:
            query = select(Memo).where(
                and_(
                    or_(Memo.memo_type == "once", Memo.memo_type == None),
                    Memo.is_completed == False,
                    Memo.reminder_time != None,
                    Memo.reminder_time >= start_time,
                    Memo.reminder_time <= end_time
                )
            )
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_periodic_memos_to_remind(self) -> List[Memo]:
        """获取当前需要提醒的周期性记事"""
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=周一, 6=周日
        current_day = now.day  # 当前是几号
        
        async with async_session() as session:
            # 查询所有未完成的周期性记事
            query = select(Memo).where(
                and_(
                    Memo.memo_type == "periodic",
                    Memo.is_completed == False
                )
            )
            result = await session.execute(query)
            memos = result.scalars().all()
            
            reminders = []
            for memo in memos:
                should_remind = False
                
                # 检查时间是否匹配（允许5分钟误差）
                if memo.reminder_time:
                    memo_time = memo.reminder_time.time()
                    time_diff = abs(
                        (current_time.hour * 60 + current_time.minute) -
                        (memo_time.hour * 60 + memo_time.minute)
                    )
                    if time_diff > 5:  # 超过5分钟不提醒
                        continue
                
                # 检查重复类型
                if memo.repeat_type == "daily":
                    should_remind = True
                elif memo.repeat_type == "weekly" and memo.repeat_days:
                    # repeat_days 格式: "0,1,2" 其中 0=周日, 1=周一...
                    days = memo.repeat_days.split(",")
                    # Python weekday: 0=周一, 6=周日
                    # 需要转换: Python 0 -> 我们 1, Python 6 -> 我们 0
                    our_weekday = str((current_weekday + 1) % 7)
                    if str(current_weekday) in days or our_weekday in days:
                        should_remind = True
                elif memo.repeat_type == "monthly" and memo.repeat_days:
                    if str(current_day) in memo.repeat_days.split(","):
                        should_remind = True
                
                # 检查是否已过结束日期
                if memo.end_date and now.date() > memo.end_date.date():
                    should_remind = False
                
                if should_remind:
                    reminders.append(memo)
            
            return reminders
    
    async def send_memo_reminder(self, memo: Memo, elderly: ElderlyInfo) -> bool:
        """发送记事提醒邮件"""
        if not elderly.email:
            return False
        
        # 确定提醒类型描述
        if memo.memo_type == "periodic":
            type_desc = {
                "daily": "每日提醒",
                "weekly": "每周提醒",
                "monthly": "每月提醒"
            }.get(memo.repeat_type, "周期提醒")
        else:
            type_desc = "事项提醒"
        
        subject = f"【{type_desc}】{memo.content}"
        
        time_str = ""
        if memo.reminder_time:
            time_str = f"\n时间：{memo.reminder_time.strftime('%Y-%m-%d %H:%M')}"
        
        content = f"""
您好，{elderly.name}：

这是您的{type_desc}：

📌 {memo.content}
{time_str}

祝您生活愉快！

—— 老年智能助手 小助
"""
        
        result = await email_service.send_email(
            to_email=elderly.email,
            subject=subject,
            content=content
        )
        return result.get("success", False)
    
    async def mark_memo_as_reminded(self, memo_id: int, is_periodic: bool = False):
        """标记记事已提醒
        
        对于一次性记事，标记为已完成
        对于周期性记事，不改变状态
        """
        if is_periodic:
            return  # 周期性记事不自动完成
        
        async with async_session() as session:
            result = await session.execute(
                select(Memo).where(Memo.id == memo_id)
            )
            memo = result.scalar_one_or_none()
            if memo:
                memo.is_completed = True
                await session.commit()
    
    async def run_reminder_task(self) -> Dict:
        """运行提醒任务（定时调用）"""
        now = datetime.now()
        results = {
            "timestamp": now.isoformat(),
            "one_time": {"total": 0, "success": 0, "failed": 0},
            "periodic": {"total": 0, "success": 0, "failed": 0},
            "details": []
        }
        
        print(f"\n{'='*50}")
        print(f"📅 提醒任务检查 @ {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        # 处理一次性记事
        one_time_memos = await self.get_one_time_memos_to_remind()
        results["one_time"]["total"] = len(one_time_memos)
        print(f"📌 一次性记事待提醒: {len(one_time_memos)} 条")
        
        for memo in one_time_memos:
            print(f"   - ID:{memo.id} | {memo.content} | 提醒时间: {memo.reminder_time}")
        
        for memo in one_time_memos:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        select(ElderlyInfo).where(ElderlyInfo.id == memo.elderly_id)
                    )
                    elderly = result.scalar_one_or_none()
                    
                    if not elderly:
                        print(f"   ⚠️ ID:{memo.id} - 找不到老人信息")
                        continue
                    
                    if not elderly.email:
                        print(f"   ⚠️ ID:{memo.id} - 老人 {elderly.name} 未设置邮箱")
                        results["one_time"]["failed"] += 1
                        continue
                    
                    print(f"   📧 发送邮件给 {elderly.name} ({elderly.email})")
                    success = await self.send_memo_reminder(memo, elderly)
                    if success:
                        await self.mark_memo_as_reminded(memo.id, is_periodic=False)
                        results["one_time"]["success"] += 1
                        print(f"   ✅ ID:{memo.id} - 发送成功")
                    else:
                        results["one_time"]["failed"] += 1
                        print(f"   ❌ ID:{memo.id} - 发送失败")
            except Exception as e:
                results["one_time"]["failed"] += 1
                print(f"   ❌ ID:{memo.id} - 错误: {e}")
        
        # 处理周期性记事
        periodic_memos = await self.get_periodic_memos_to_remind()
        results["periodic"]["total"] = len(periodic_memos)
        print(f"\n🔄 周期性记事待提醒: {len(periodic_memos)} 条")
        
        for memo in periodic_memos:
            print(f"   - ID:{memo.id} | {memo.content} | 类型: {memo.repeat_type}")
        
        for memo in periodic_memos:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        select(ElderlyInfo).where(ElderlyInfo.id == memo.elderly_id)
                    )
                    elderly = result.scalar_one_or_none()
                    
                    if not elderly:
                        print(f"   ⚠️ ID:{memo.id} - 找不到老人信息")
                        continue
                    
                    if not elderly.email:
                        print(f"   ⚠️ ID:{memo.id} - 老人 {elderly.name} 未设置邮箱")
                        results["periodic"]["failed"] += 1
                        continue
                    
                    print(f"   📧 发送邮件给 {elderly.name} ({elderly.email})")
                    success = await self.send_memo_reminder(memo, elderly)
                    if success:
                        results["periodic"]["success"] += 1
                        print(f"   ✅ ID:{memo.id} - 发送成功")
                    else:
                        results["periodic"]["failed"] += 1
                        print(f"   ❌ ID:{memo.id} - 发送失败")
            except Exception as e:
                results["periodic"]["failed"] += 1
                print(f"   ❌ ID:{memo.id} - 错误: {e}")
        
        # 汇总
        print(f"\n📊 提醒完成: 一次性 {results['one_time']['success']}/{results['one_time']['total']}, "
              f"周期性 {results['periodic']['success']}/{results['periodic']['total']}")
        
        return results


# 创建调度器实例
reminder_scheduler = ReminderScheduler()


# 定时任务相关
_scheduler_task = None
_running = False


async def start_scheduler(interval_minutes: int = 5):
    """启动定时调度器
    
    Args:
        interval_minutes: 检查间隔时间（分钟）
    """
    global _running, _scheduler_task
    _running = True
    
    async def scheduler_loop():
        while _running:
            try:
                result = await reminder_scheduler.run_reminder_task()
                if result["one_time"]["total"] > 0 or result["periodic"]["total"] > 0:
                    print(f"📅 提醒任务执行: 一次性({result['one_time']['success']}/{result['one_time']['total']}) "
                          f"周期性({result['periodic']['success']}/{result['periodic']['total']})")
            except Exception as e:
                print(f"❌ 提醒任务错误: {e}")
            
            await asyncio.sleep(interval_minutes * 60)
    
    _scheduler_task = asyncio.create_task(scheduler_loop())
    print(f"✅ 提醒调度器已启动，每 {interval_minutes} 分钟检查一次")


async def stop_scheduler():
    """停止定时调度器"""
    global _running, _scheduler_task
    _running = False
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    print("⏹️ 提醒调度器已停止")
