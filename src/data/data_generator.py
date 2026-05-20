"""
新版数据生成器 (基于 config_data.yaml)
生成符合设计文档规范的流量数据
"""

import numpy as np
import pandas as pd
import sys
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

from .config_parser import ConfigDataParser, DateProfileConfig
from .date_detector import DateProfileDetector


class TrafficDataGenerator:
    """流量数据生成器 V3 - 基于 config_data.yaml"""
    
    def __init__(self, config_path: str = "config/config_data.yaml", 
                 log_file: str = "logs/data_generator.log"):
        """
        初始化生成器
        
        Args:
            config_path: 配置文件路径
            log_file: 日志文件路径（默认: logs/data_generator.log）
        """
        # 加载配置
        self.config_parser = ConfigDataParser(config_path)
        self.config_parser.load()
        
        self.global_cfg = self.config_parser.global_config
        self.date_mapping = self.config_parser.date_mapping
        self.advanced = self.config_parser.advanced
        
        # 初始化日期检测器
        self.date_detector = DateProfileDetector(
            use_chinese_calendar=self.date_mapping.use_chinese_calendar
        )
        
        # 设置随机种子
        np.random.seed(self.global_cfg.seed)
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以捕获所有日志
        self.logger.propagate = False  # 阻止日志传播到父logger，避免重复输出
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 文件处理器 - 调试日志写入文件
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台处理器 - 只显示INFO及以上级别
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.advanced.log_level))
        console_formatter = logging.Formatter('%(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"数据生成器初始化完成，调试日志将写入 {log_file}")
    
    def generate(self) -> pd.DataFrame:
        """
        生成完整的流量数据
        
        Returns:
            DataFrame with columns: timestamp, gnb_0_load, gnb_1_load, gnb_2_load
        """
        self.logger.info(f"开始生成数据: {self.global_cfg.num_days} 天, "
                        f"间隔 {self.global_cfg.time_interval_minutes} 分钟")
        
        # 生成所有时间戳
        start_dt = datetime.strptime(self.global_cfg.start_date, "%Y-%m-%d")
        timestamps = self._generate_timestamps(start_dt, self.global_cfg.num_days,
                                               self.global_cfg.time_interval_minutes)
        
        # 为每个基站生成负载数据
        n_gnbs = self.global_cfg.n_gnbs
        gnb_loads = []
        
        for gnb_id in range(n_gnbs):
            self.logger.info(f"生成基站 {gnb_id} 的数据...")
            loads = self._generate_gnb_loads(timestamps, gnb_id)
            gnb_loads.append(loads)
        
        # 构建 DataFrame
        data = {'timestamp': timestamps}
        for gnb_id in range(n_gnbs):
            data[f'gnb_{gnb_id}_load'] = gnb_loads[gnb_id]
        
        df = pd.DataFrame(data)
        
        # 数据验证
        if self.advanced.validation_enabled:
            self._validate_data(df)
        
        self.logger.info(f"数据生成完成: {len(df)} 条记录")
        return df
    
    def _generate_timestamps(self, start_dt: datetime, num_days: int, 
                            interval_minutes: int) -> List[datetime]:
        """生成时间戳序列"""
        timestamps = []
        current_dt = start_dt
        end_dt = start_dt + timedelta(days=num_days)
        
        while current_dt < end_dt:
            timestamps.append(current_dt)
            current_dt += timedelta(minutes=interval_minutes)
        
        return timestamps
    
    def _generate_gnb_loads(self, timestamps: List[datetime], gnb_id: int) -> np.ndarray:
        """
        为单个基站生成负载序列
        
        Args:
            timestamps: 时间戳列表
            gnb_id: 基站 ID
            
        Returns:
            负载数组
        """
        loads = np.zeros(len(timestamps))
        
        # 按天生成
        current_date = None
        current_profile = None
        daily_loads = []
        
        for i, ts in enumerate(timestamps):
            ts_date = ts.date()
            
            # 如果是新的一天，获取对应的 date_profile
            new_day = False
            if ts_date != current_date:
                new_day = True
                current_date = ts_date
                profile_name = self.date_detector.get_date_profile(ts_date)
                current_profile = self.config_parser.get_profile(profile_name)
                
                if current_profile is None:
                    self.logger.warning(f"未找到配置: {profile_name}, 使用默认配置")
                    current_profile = self.config_parser.get_profile('normal_weekday')
                
                self.logger.debug(f"日期 {ts_date}: {profile_name}")
                
                # 重置每日负载缓存
                daily_loads = []
            
            # 获取当前小时的负载配置
            hour = ts.hour
            load_config = current_profile.get_load_for_hour(hour)
            center = load_config['center']
            max_val = load_config['max']
            
            # 在 [center, max] 范围内随机生成
            # 使用 Beta 分布使得值更接近 center
            alpha, beta = 2.0, 5.0  # Beta 分布参数（偏向低值）
            random_factor = np.random.beta(alpha, beta)
            load = center + (max_val - center) * random_factor
            
            # 添加小量噪声
            noise = np.random.normal(0, 0.02)
            # 允许超载场景：最大可达1.2
            load = np.clip(load + noise, 0.0, 1.3)  # 设置为1.3以留余量
            
            # 调试日志 - 记录详细的生成过程
            if new_day == True:
                self.logger.debug(
                    f"[GNB_{gnb_id}] {ts.strftime('%Y-%m-%d %H:%M')} | "
                    f"Profile: {profile_name:20s} | "
                    f"Hour: {hour:2d} | "
                    f"Center: {center:.3f} | "
                    f"Max: {max_val:.3f} | "
                    f"RandomFactor: {random_factor:.3f} | "
                    f"Noise: {noise:+.4f} | "
                    f"FinalLoad: {load:.4f}"
                )
                
            daily_loads.append(load)
            loads[i] = load
        
        # 平滑处理
        if self.advanced.smoothing_enabled:
            loads = self._smooth_loads(loads, timestamps)
        
        # 基站差异化（轻微调整）
        loads = self._apply_gnb_variation(loads, gnb_id)
        
        return loads
    
    def _smooth_loads(self, loads: np.ndarray, timestamps: List[datetime]) -> np.ndarray:
        """
        平滑负载数据（避免跳变）
        
        Args:
            loads: 原始负载数组
            timestamps: 时间戳列表
            
        Returns:
            平滑后的负载数组
        """
        if self.advanced.smoothing_method == "linear_interpolation":
            # 使用移动平均
            window_size = max(1, self.advanced.smoothing_window_minutes // 
                            self.global_cfg.time_interval_minutes)
            
            smoothed = np.copy(loads)
            for i in range(len(loads)):
                start_idx = max(0, i - window_size // 2)
                end_idx = min(len(loads), i + window_size // 2 + 1)
                smoothed[i] = np.mean(loads[start_idx:end_idx])
            
            return smoothed
        
        return loads
    
    def _apply_gnb_variation(self, loads: np.ndarray, gnb_id: int) -> np.ndarray:
        """
        应用基站差异化
        
        不同基站略有不同的负载模式
        
        Args:
            loads: 负载数组
            gnb_id: 基站 ID
            
        Returns:
            调整后的负载数组
        """
        # 基站 0: 中心基站，负载略高 (+5%)
        # 基站 1: 边缘基站，负载正常
        # 基站 2: 边缘基站，负载略低 (-5%)
        
        if gnb_id == 0:
            multiplier = 1.05
        elif gnb_id == 2:
            multiplier = 0.95
        else:
            multiplier = 1.0
        
        adjusted = loads * multiplier
        # 允许超载场景：最大可达1.2
        return np.clip(adjusted, 0.0, 1.3)  # 设置为1.3以留余量
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """
        验证生成的数据
        
        Args:
            df: 生成的数据 DataFrame
        """
        self.logger.info("开始数据验证...")
        
        # 检查值域范围
        if self.advanced.check_range:
            for gnb_id in range(self.global_cfg.n_gnbs):
                col = f'gnb_{gnb_id}_load'
                # 允许超载场景：required_load 可达 1.2
                if df[col].min() < 0.0 or df[col].max() > 1.2:
                    self.logger.warning(f"{col} 超出范围 [0, 1.2]: "
                                      f"min={df[col].min():.3f}, max={df[col].max():.3f}")
        
        # 检查连续性（避免突变）
        if self.advanced.check_continuity:
            for gnb_id in range(self.global_cfg.n_gnbs):
                col = f'gnb_{gnb_id}_load'
                diffs = df[col].diff().abs()
                max_diff = diffs.max()
                
                if max_diff > self.advanced.max_jump_per_step:
                    self.logger.warning(f"{col} 存在较大跳变: max_diff={max_diff:.3f}")
        
        self.logger.info("数据验证完成")
    
    def save(self, df: pd.DataFrame, output_path: Optional[str] = None) -> str:
        """
        保存生成的数据
        
        Args:
            df: 数据 DataFrame
            output_path: 输出路径（可选，覆盖配置）
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            output_dir = Path(self.global_cfg.output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{self.global_cfg.filename_prefix}_{self.global_cfg.num_days}days.csv"
            output_path = output_dir / filename
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 格式化时间戳
        df_copy = df.copy()
        df_copy['timestamp'] = df_copy['timestamp'].dt.strftime('%m/%d/%Y %I:%M:%S %p')
        
        # 保存
        if self.global_cfg.output_format == 'csv':
            df_copy.to_csv(output_path, index=False)
        elif self.global_cfg.output_format == 'json':
            df_copy.to_json(output_path, orient='records', indent=2)
        else:
            raise ValueError(f"不支持的输出格式: {self.global_cfg.output_format}")
        
        self.logger.info(f"数据已保存到: {output_path}")
        return str(output_path)


def generate_traffic_data(config_path: str = "config/config_data.yaml",
                         output_path: Optional[str] = None,
                         num_days: Optional[int] = None,
                         seed: Optional[int] = None) -> pd.DataFrame:
    """
    便捷函数：生成流量数据
    
    Args:
        config_path: 配置文件路径
        output_path: 输出路径（可选）
        num_days: 覆盖配置中的天数（可选）
        seed: 覆盖配置中的随机种子（可选）
        
    Returns:
        生成的数据 DataFrame
    """
    generator = TrafficDataGenerator(config_path)
    
    # 覆盖参数
    if num_days is not None:
        generator.global_cfg.num_days = num_days
    if seed is not None:
        generator.global_cfg.seed = seed
        np.random.seed(seed)
    
    # 生成数据
    df = generator.generate()
    
    # 保存
    if output_path:
        generator.save(df, output_path)
    else:
        generator.save(df)
    
    return df
