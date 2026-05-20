"""
日期识别模块
使用 chinese_calendar 库识别日期类型（date_profile）
"""

from datetime import datetime, date, timedelta
from typing import Optional
import logging

try:
    import chinese_calendar as calendar
    HAS_CHINESE_CALENDAR = True
except ImportError:
    HAS_CHINESE_CALENDAR = False
    logging.warning("chinese_calendar 库未安装，将使用简化的日期识别逻辑")


class DateProfileDetector:
    """日期类型检测器"""
    
    # 7 种 date_profile（按优先级排序）
    LUNAR_EVE = "lunar_eve"
    SPRING_FESTIVAL = "spring_festival"
    MAJOR_HOLIDAY = "major_holiday"
    OTHER_HOLIDAY = "other_holiday"
    PRE_HOLIDAY = "pre_holiday"
    NORMAL_FRIDAY = "normal_friday"
    NORMAL_WEEKDAY = "normal_weekday"
    
    def __init__(self, use_chinese_calendar: bool = True):
        """
        初始化日期检测器
        
        Args:
            use_chinese_calendar: 是否使用 chinese_calendar 库
        """
        self.use_chinese_calendar = use_chinese_calendar and HAS_CHINESE_CALENDAR
        
        if not self.use_chinese_calendar:
            logging.info("使用简化的日期识别逻辑（不依赖 chinese_calendar）")
    
    def get_date_profile(self, target_date: date) -> str:
        """
        获取指定日期的 date_profile
        
        判断优先级：
        1. lunar_eve（除夕）
        2. spring_festival（春节）
        3. major_holiday（五一/国庆）
        4. other_holiday（其他节假日+周末）
        5. pre_holiday（节假日前一天）
        6. normal_friday（普通周五）
        7. normal_weekday（周一-周四）
        
        Args:
            target_date: 目标日期
            
        Returns:
            date_profile 名称
        """
        # 1. 检查是否为除夕
        if self._is_lunar_eve(target_date):
            return self.LUNAR_EVE
        
        # 2. 检查是否为春节
        if self._is_spring_festival(target_date):
            return self.SPRING_FESTIVAL
        
        # 3. 检查是否为重大节假日（五一/国庆）
        if self._is_major_holiday(target_date):
            return self.MAJOR_HOLIDAY
        
        # 4. 检查是否为其他节假日或周末
        if self._is_other_holiday(target_date):
            return self.OTHER_HOLIDAY
        
        # 5. 检查是否为节假日前一天
        if self._is_pre_holiday(target_date):
            return self.PRE_HOLIDAY
        
        # 6. 检查是否为普通周五
        if target_date.weekday() == 4:  # 周五
            return self.NORMAL_FRIDAY
        
        # 7. 默认为普通工作日
        return self.NORMAL_WEEKDAY
    
    def _is_lunar_eve(self, target_date: date) -> bool:
        """
        判断是否为除夕
        
        使用 chinese_calendar 获取农历日期信息
        除夕为农历腊月最后一天
        """
        if not self.use_chinese_calendar:
            # 简化逻辑：手动指定2025-2030年的除夕日期
            lunar_eves = {
                date(2025, 1, 28),  # 2025年除夕
                date(2026, 2, 16),  # 2026年除夕
                date(2027, 2, 5),   # 2027年除夕
                date(2028, 1, 25),  # 2028年除夕
                date(2029, 2, 12),  # 2029年除夕
                date(2030, 2, 2),   # 2030年除夕
            }
            return target_date in lunar_eves
        
        # 使用 chinese_calendar 判断
        try:
            # 检查明天是否为春节（正月初一）
            next_day = target_date + timedelta(days=1)
            # 如果明天是春节，则今天是除夕
            if calendar.is_holiday(next_day):
                # 检查是否为春节
                holiday_name = calendar.get_holiday_detail(next_day)
                if holiday_name and '春节' in str(holiday_name[0]):
                    return True
        except:
            pass
        
        return False
    
    def _is_spring_festival(self, target_date: date) -> bool:
        """
        判断是否为春节（正月初一及初二）
        """
        if not self.use_chinese_calendar:
            # 简化逻辑：手动指定2025-2030年的春节日期（初一和初二）
            spring_festivals = {
                date(2025, 1, 29), date(2025, 1, 30),  # 2025
                date(2026, 2, 17), date(2026, 2, 18),  # 2026
                date(2027, 2, 6),  date(2027, 2, 7),   # 2027
                date(2028, 1, 26), date(2028, 1, 27),  # 2028
                date(2029, 2, 13), date(2029, 2, 14),  # 2029
                date(2030, 2, 3),  date(2030, 2, 4),   # 2030
            }
            return target_date in spring_festivals
        
        # 使用 chinese_calendar 判断
        try:
            if calendar.is_holiday(target_date):
                holiday_name = calendar.get_holiday_detail(target_date)
                if holiday_name and '春节' in str(holiday_name[0]):
                    return True
        except:
            pass
        
        return False
    
    def _is_major_holiday(self, target_date: date) -> bool:
        """
        判断是否为重大节假日（元旦/五一/国庆当天）
        """
        # 元旦：1月1日
        # 五一劳动节：5月1日
        # 国庆节：10月1日
        return (target_date.month == 1 and target_date.day == 1) or \
               (target_date.month == 5 and target_date.day == 1) or \
               (target_date.month == 10 and target_date.day == 1)
    
    def _is_other_holiday(self, target_date: date) -> bool:
        """
        判断是否为其他节假日或周末
        """
        # 周末
        if target_date.weekday() in [5, 6]:  # 周六、周日
            return True
        
        if not self.use_chinese_calendar:
            # 简化逻辑：手动指定常见节假日
            common_holidays = {
                (1, 1),   # 元旦
                (4, 4),   # 清明（近似）
                (4, 5),
                (5, 1),   # 五一（但会被 major_holiday 捕获）
                (6, 1),   # 端午（近似）
                (6, 2),
                (9, 8),   # 中秋（近似）
                (9, 9),
                (10, 1),  # 国庆（但会被 major_holiday 捕获）
            }
            return (target_date.month, target_date.day) in common_holidays
        
        # 使用 chinese_calendar 判断
        try:
            return calendar.is_holiday(target_date)
        except:
            return target_date.weekday() in [5, 6]
    
    def _is_pre_holiday(self, target_date: date) -> bool:
        """
        判断是否为节假日前一天
        
        如果明天是节假日（包括周末），则今天为 pre_holiday
        """
        next_day = target_date + timedelta(days=1)
        
        # 如果明天是除夕、春节、重大节假日或其他节假日
        if self._is_lunar_eve(next_day) or \
           self._is_spring_festival(next_day) or \
           self._is_major_holiday(next_day) or \
           self._is_other_holiday(next_day):
            return True
        
        return False
    
    def get_profile_description(self, profile_name: str) -> str:
        """获取 date_profile 的描述"""
        descriptions = {
            self.LUNAR_EVE: "除夕 - 下午至晚上负载极高",
            self.SPRING_FESTIVAL: "春节当天 - 凌晨高活跃，白天拜年",
            self.MAJOR_HOLIDAY: "重大节假日（五一/国庆）- 全天高负载",
            self.OTHER_HOLIDAY: "其他节假日/周末 - 无通勤高峰",
            self.PRE_HOLIDAY: "节假日前一天 - 晚上负载更高",
            self.NORMAL_FRIDAY: "普通周五 - 周末前夜",
            self.NORMAL_WEEKDAY: "普通工作日 - 早晚高峰明显"
        }
        return descriptions.get(profile_name, "未知类型")


# 便捷函数
def get_date_profile(target_date: date, use_chinese_calendar: bool = True) -> str:
    """
    获取指定日期的 date_profile
    
    Args:
        target_date: 目标日期
        use_chinese_calendar: 是否使用 chinese_calendar 库
        
    Returns:
        date_profile 名称
    """
    detector = DateProfileDetector(use_chinese_calendar=use_chinese_calendar)
    return detector.get_date_profile(target_date)
