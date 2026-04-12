# emotion/hormone_cycle.py

import datetime
from utils.log import logger

class HormoneCycle:
    """
    管理角色的生理周期状态并计算其对情绪参数的调节影响。
    """
    def __init__(self, cycle_length: int, cycle_day: int, last_update_timestamp: datetime.datetime):
        self.cycle_length = cycle_length
        self.cycle_day = cycle_day
        self.last_update_timestamp = last_update_timestamp

    def update_cycle(self):
        """
        根据真实时间的流逝来更新周期天数。
        """
        now = datetime.datetime.now()
        time_delta = now - self.last_update_timestamp
        
        days_passed = time_delta.days

        if days_passed > 0:
            logger.info(f"生理周期已过去 {days_passed} 天，更新周期天数")
            self.cycle_day += days_passed
            self.cycle_day = ((self.cycle_day - 1) % self.cycle_length) + 1
            self.last_update_timestamp = now.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_hormonal_modifiers(self) -> dict:
        """
        根据当前周期天数，计算并返回情绪调节参数。
        返回一个包含以下键的字典:
        - 'inertia_factor': 情绪惯性因子。值越低，情绪越不稳定。
        - 'sensitivity_multiplier': 负面情绪敏感度乘数。值越高，挫折感累积越快。
        - 'positive_valence_pull': 当valence为正时，将其拉回中性的力度。
        - 'negative_valence_pull': 当valence为负时，将其拉回中性的力度。
        """
        day = self.cycle_day
        
        # 1. 默认基准值
        inertia_factor = 1.5
        sensitivity_multiplier = 1.0
        positive_valence_pull = 0.03
        negative_valence_pull = 0.03


        if 1 <= day <= 5:
            phase_name = "月经期"
            inertia_factor = 1.3
            sensitivity_multiplier = 1.1
            
        elif 6 <= day <= 12:
            phase_name = "卵泡期"
            # 使用基准值
            
        elif 13 <= day <= 15:
            phase_name = "排卵期"
            inertia_factor = 1.8
            positive_valence_pull = 0.01
            negative_valence_pull = 0.05
            
        elif 16 <= day <= 21:
            phase_name = "黄体期"
            # 使用基准值

        elif 22 <= day <= self.cycle_length:
            phase_name = "黄体晚期 (PMS)"
            inertia_factor = 0.8
            sensitivity_multiplier = 1.4
            positive_valence_pull = 0.08
            negative_valence_pull = 0.01

        else:
            phase_name = "未知"

        logger.info(f"生理周期第 {day}/{self.cycle_length} 天，处于 {phase_name}")
        
        return {
            'inertia_factor': inertia_factor,
            'sensitivity_multiplier': sensitivity_multiplier,
            'positive_valence_pull': positive_valence_pull,
            'negative_valence_pull': negative_valence_pull
        }