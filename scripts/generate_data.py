"""
Generate network traffic data (script).

Purpose:
    Create a synthetic, spatio-temporal dataset of gNB traffic suitable for
    training and simulation. Data includes per-gNB normalized load and
    time/business features based on config_data.yaml.

Params:
    --config: str (path)
        Path to YAML config (default: config/config_data.yaml). The config must
        provide global settings, date_profiles, and date_mapping.
    --days: int
        Optional override for number of days to generate.
    --seed: int
        Optional random seed override.
    --output: str (path)
        Optional output CSV path (overrides config.output.data_dir).

Example:
    python scripts/generate_data.py --days 30 --output data/traffic_data.csv

This script writes a CSV with columns: timestamp, gnb_0_load, gnb_1_load, gnb_2_load
"""

# 中文使用说明：
# 目的：基于 config_data.yaml 生成用于训练和仿真的合成流量数据。
# 参数：
#   --config: YAML配置路径（默认：config/config_data.yaml），需包含global、date_profiles等配置。
#   --days: 可选，覆盖配置中的num_days以指定生成天数。
#   --seed: 可选，随机种子覆盖。
#   --output: 可选，指定输出CSV路径，覆盖配置中的输出目录。
# 示例：
#   python scripts/generate_data.py --days 7 --output data/traffic_7days.csv
# 输出：
#   在输出目录生成CSV文件（timestamp, gnb_0_load, gnb_1_load, gnb_2_load）

import argparse
import yaml
from pathlib import Path
import sys
import logging

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.data_generator import TrafficDataGenerator


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="生成网络流量数据（基于 config_data.yaml）"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config_data.yaml',
        help='配置文件路径（YAML格式）'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='生成天数（覆盖配置文件）'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='随机种子（覆盖配置文件）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径（覆盖配置文件）'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    return parser.parse_args()


def main():
    """主函数"""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    args = parse_args()
    
    # 加载配置
    import yaml
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        sys_config = yaml.safe_load(f)
    
    # 从config读取日志配置
    from datetime import datetime
    log_dir = Path(sys_config['paths']['logs'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成带时间戳的日志文件名
    script_name = Path(__file__).stem
    timestamp = datetime.now().strftime(sys_config['logging']['timestamp_format'])
    log_file = log_dir / f'{script_name}_{timestamp}.log'
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format=sys_config['logging']['format'],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log file: {log_file}")
    
    try:
        # 创建生成器（使用从config.yaml读取的日志路径）
        logger.info(f"加载配置文件: {args.config}")
        generator = TrafficDataGenerator(args.config, log_file=str(log_file))
        
        # 覆盖参数
        if args.days is not None:
            logger.info(f"覆盖配置: num_days = {args.days}")
            generator.global_cfg.num_days = args.days
        
        if args.seed is not None:
            logger.info(f"覆盖配置: seed = {args.seed}")
            generator.global_cfg.seed = args.seed
            import numpy as np
            np.random.seed(args.seed)
        
        # 生成数据
        logger.info("开始生成数据...")
        df = generator.generate()
        
        # 保存数据
        output_path = generator.save(df, args.output)
        
        # 显示统计信息
        logger.info(f"\n数据统计:")
        logger.info(f"  记录数: {len(df)}")
        logger.info(f"  时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        for gnb_id in range(generator.global_cfg.n_gnbs):
            col = f'gnb_{gnb_id}_load'
            logger.info(f"  {col}: min={df[col].min():.3f}, "
                       f"mean={df[col].mean():.3f}, max={df[col].max():.3f}")
        
        logger.info(f"\n✓ 数据生成成功! 保存于: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ 数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

