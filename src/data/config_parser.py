"""
配置文件解析器
用于解析 config_data.yaml 配置文件
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GlobalConfig:
    """全局配置"""
    seed: int = 42
    start_date: str = "2025-01-01"
    num_days: int = 90
    time_interval_minutes: int = 5
    output_format: str = "csv"
    output_path: str = "data/generated/"
    filename_prefix: str = "traffic"
    n_gnbs: int = 3


@dataclass
class DateProfileConfig:
    """日期配置"""
    name: str
    description: str
    enabled: bool
    hour_segments: Dict[str, Dict[str, float]]
    
    def get_load_for_hour(self, hour: int) -> Dict[str, float]:
        """
        获取指定小时的负载配置
        
        配置使用2小时粒度：
        "0-1" 覆盖 0点和1点
        "2-3" 覆盖 2点和3点
        ...
        "22-23" 覆盖 22点和23点
        """
        # 将小时映射到2小时时段的起始小时（偶数）
        # 0,1 -> 0; 2,3 -> 2; 4,5 -> 4; ... 22,23 -> 22
        segment_start = (hour // 2) * 2
        segment_key = f"{segment_start}-{segment_start + 1}"
        
        # 返回对应配置
        if segment_key in self.hour_segments:
            return self.hour_segments[segment_key]
        
        # 如果配置不存在，返回默认低负载
        return {"center": 0.1, "max": 0.3}


@dataclass
class DateMappingConfig:
    """日期映射配置"""
    use_chinese_calendar: bool = True
    major_holidays: list = field(default_factory=list)
    spring_festival_detection: Dict[str, Any] = field(default_factory=dict)
    lunar_eve_detection: Dict[str, Any] = field(default_factory=dict)
    pre_holiday_detection: Dict[str, Any] = field(default_factory=dict)
    weekday_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class AdvancedConfig:
    """高级配置"""
    smoothing_enabled: bool = True
    smoothing_method: str = "linear_interpolation"
    smoothing_window_minutes: int = 15
    validation_enabled: bool = True
    check_range: bool = True
    check_continuity: bool = True
    max_jump_per_step: float = 0.15
    use_vectorization: bool = True
    chunk_size: int = 1000
    parallel_gnbs: bool = True
    debug_enabled: bool = False
    log_level: str = "INFO"


class ConfigDataParser:
    """配置文件解析器"""
    
    def __init__(self, config_path: str = "config/config_data.yaml"):
        """
        初始化配置解析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._raw_config: Optional[Dict[str, Any]] = None
        self.global_config: Optional[GlobalConfig] = None
        self.date_profiles: Dict[str, DateProfileConfig] = {}
        self.date_mapping: Optional[DateMappingConfig] = None
        self.advanced: Optional[AdvancedConfig] = None
        
    def load(self) -> None:
        """加载并解析配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._raw_config = yaml.safe_load(f)
        
        self._parse_global()
        self._parse_date_profiles()
        self._parse_date_mapping()
        self._parse_advanced()
    
    def _parse_global(self) -> None:
        """解析全局配置"""
        global_dict = self._raw_config.get('global', {})
        output_dict = global_dict.get('output', {})
        network_dict = global_dict.get('network', {})
        
        self.global_config = GlobalConfig(
            seed=global_dict.get('seed', 42),
            start_date=global_dict.get('start_date', '2025-01-01'),
            num_days=global_dict.get('num_days', 90),
            time_interval_minutes=global_dict.get('time_interval_minutes', 5),
            output_format=output_dict.get('format', 'csv'),
            output_path=output_dict.get('path', 'data/generated/'),
            filename_prefix=output_dict.get('filename_prefix', 'traffic'),
            n_gnbs=network_dict.get('n_gnbs', 3)
        )
    
    def _parse_date_profiles(self) -> None:
        """解析日期配置"""
        profiles_dict = self._raw_config.get('date_profiles', {})
        
        for profile_name, profile_data in profiles_dict.items():
            self.date_profiles[profile_name] = DateProfileConfig(
                name=profile_name,
                description=profile_data.get('description', ''),
                enabled=profile_data.get('enabled', True),
                hour_segments=profile_data.get('hour_segments', {})
            )
    
    def _parse_date_mapping(self) -> None:
        """解析日期映射配置"""
        mapping_dict = self._raw_config.get('date_mapping', {})
        
        self.date_mapping = DateMappingConfig(
            use_chinese_calendar=mapping_dict.get('use_chinese_calendar', True),
            major_holidays=mapping_dict.get('major_holidays', []),
            spring_festival_detection=mapping_dict.get('spring_festival_detection', {}),
            lunar_eve_detection=mapping_dict.get('lunar_eve_detection', {}),
            pre_holiday_detection=mapping_dict.get('pre_holiday_detection', {}),
            weekday_map=mapping_dict.get('weekday_map', {})
        )
    
    def _parse_advanced(self) -> None:
        """解析高级配置"""
        advanced_dict = self._raw_config.get('advanced', {})
        smoothing_dict = advanced_dict.get('smoothing', {})
        validation_dict = advanced_dict.get('validation', {})
        performance_dict = advanced_dict.get('performance', {})
        debug_dict = advanced_dict.get('debug', {})
        
        self.advanced = AdvancedConfig(
            smoothing_enabled=smoothing_dict.get('enabled', True),
            smoothing_method=smoothing_dict.get('method', 'linear_interpolation'),
            smoothing_window_minutes=smoothing_dict.get('window_minutes', 15),
            validation_enabled=validation_dict.get('enabled', True),
            check_range=validation_dict.get('check_range', True),
            check_continuity=validation_dict.get('check_continuity', True),
            max_jump_per_step=validation_dict.get('max_jump_per_step', 0.15),
            use_vectorization=performance_dict.get('use_vectorization', True),
            chunk_size=performance_dict.get('chunk_size', 1000),
            parallel_gnbs=performance_dict.get('parallel_gnbs', True),
            debug_enabled=debug_dict.get('enabled', False),
            log_level=debug_dict.get('log_level', 'INFO')
        )
    
    def get_profile(self, profile_name: str) -> Optional[DateProfileConfig]:
        """
        获取指定的日期配置
        
        Args:
            profile_name: 配置名称
            
        Returns:
            DateProfileConfig 或 None
        """
        return self.date_profiles.get(profile_name)
    
    def __repr__(self) -> str:
        return (f"ConfigDataParser(config_path={self.config_path}, "
                f"profiles={len(self.date_profiles)}, "
                f"loaded={'Yes' if self._raw_config else 'No'})")
