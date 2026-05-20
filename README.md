# 基于流量预测的智能负载均衡系统

## 项目概述

基于AI流量预测的主动式负载均衡系统，用于5G/6G无线网络。系统通过预测未来网络负载，提前进行资源分配决策，提升网络资源利用率和服务质量。

### 核心特性

- 🤖 **双模型支持**：LSTM 和 Transformer 预测模型
- 📊 **双预测模式**：负载预测（load）和增量预测（delta）
- 🔄 **多种策略**：预测式、反应式、无负载均衡基准对比
- 📈 **完整流程**：数据生成 → 预处理 → 训练 → 仿真 → 分析
- 🎯 **时间步过滤**：支持精确的时间范围分析

---

## 🚀 快速开始

### 环境准备

**系统要求**：
- 推荐：Python 3.11
- 推荐：8GB+ RAM，有 CUDA 支持的 GPU（可选）

**克隆项目**:
```bash
git clone <repository-url>
cd <project_root>
```

**激活python环境 (推荐方法1：conda)**：
```bash
# 创建并激活conda环境
conda create -n python3.11 python=3.11 -y
conda activate python3.11
```

**激活python环境(方法2：venv)**：
```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```


**安装 PyTorch + CUDA (三选一)**:
```bash
#首先查看你的电脑支持最高的 CUDA 版本是多少，后面用 cuda 130 还是 132取决于你支持的最高CUDA版本
nvidia-smi

## 如果有 NVIDIA 独显 RTX 50系列：安装 PyTorch（GPU，用 pip）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu132 [--force-reinstall]

## 如果有 NVIDIA 独显 RTX 40/30系列：：安装 PyTorch（GPU，用 pip）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 [--force-reinstall]

## 如果没有独显或者显卡不是NVIDIA的：安装 PyTorch（CPU 版，用 pip）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu [--force-reinstall]

## 说明：如果不指定软件源，可能会自动下载到CPU 版本，不是GPU版本
```

**验证安装的CUDA**
```bash
python -c "import torch; print('torch:', torch.__version__); print('torch.version.cuda:', torch.version.cuda); print('cuda available:', torch.cuda.is_available()); print('cuda device count:', torch.cuda.device_count())"
```

结果判读：
- 若 torch 版本后缀是 +cpu（例如 2.11.0+cpu）
- 或 torch.version.cuda 是 None
- 或 cuda available 是 False
则说明当前环境是 CPU 版 PyTorch，训练不会使用独立显卡。

**安装 PyTorch + CUDA**:
```bash
pip install torch torchvision torchaudio --index-url xxx
```

**安装其余依赖**
```bash
pip install -r requirements.txt
```

主要依赖：`torch`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `pyyaml`, `scikit-learn`

---

### 方法一：一键运行 ⚡

使用 `quick_start.py` 自动执行完整流程（推荐新手）：

```bash
python quick_start.py
```

**执行内容**：
1. ✅ 生成 7 天网络流量数据
2. ✅ 预处理数据
3. ✅ 训练 4 个模型（LSTM/Transformer × load/delta）
4. ✅ 运行 static 和 dynamic 两种仿真模式
5. ✅ 生成对比分析报告和可视化图表

**预计耗时**：约 10-20 分钟（取决于硬件配置）

---

### 方法二：分步执行 🔧

#### 步骤 1：生成数据

```bash
# 生成 7 天流量数据
python scripts/generate_data.py --days 7 --output data/raw/raw_traffic_7days.csv
```

**输出**：`data/raw/raw_traffic_7days.csv`

#### 步骤 2：预处理数据

```bash
python scripts/preprocess_data.py --input data/raw/raw_traffic_7days.csv --output data/processed/processed_traffic_7days.csv
```

**输出**：`data/processed/processed_traffic_7days.csv`

#### 步骤 3：训练模型

[![方式1: 增量预测模式](https://img.shields.io/badge/方式1-%E5%A2%9E%E9%87%8F%E9%A2%84%E6%B5%8B%E6%A8%A1%E5%BC%8F-blue)](https://shields.io/) <span style="color:red">(推荐)</span>

```bash
# LSTM - 增量预测模式（默认 --mode delta）
python scripts/train_model.py --model lstm --mode delta --data data/processed/processed_traffic_7days.csv --epochs 50

# Transformer - 增量预测模式（默认 --mode delta）
python scripts/train_model.py --model transformer --mode delta --data data/processed/processed_traffic_7days.csv --epochs 50
```

[![方式2: 负载预测模式](https://img.shields.io/badge/方式2-%E8%B4%9F%E8%BD%BD%E9%A2%84%E6%B5%8B%E6%A8%A1%E5%BC%8F-blue)](https://shields.io/)

```bash
# LSTM - 负载预测模式
python scripts/train_model.py --model lstm --mode load --data data/processed/processed_traffic_7days.csv --epochs 50

# Transformer - 负载预测模式
python scripts/train_model.py --model transformer --mode load --data data/processed/processed_traffic_7days.csv --epochs 50
```

**输出**：4 个模型文件保存在 `models/` 目录

#### 步骤 4：运行仿真

[![方式1: 动态模式](https://img.shields.io/badge/方式1-%E5%8A%A8%E6%80%81%E6%A8%A1%E5%BC%8F-blue)](https://shields.io/) <span style="color:red">(推荐)</span>

```bash
# 动态模式仿真（动态生成负载） --默认模式：dynamic
python scripts/run_simulation.py --sim_mode dynamic --data data/processed/processed_traffic_7days.csv --lbMode all
```

[![方式2: 静态模式](https://img.shields.io/badge/方式2-%E9%9D%99%E6%80%81%E6%A8%A1%E5%BC%8F-blue)](https://shields.io/)

```bash
# 静态模式仿真（固定负载）
python scripts/run_simulation.py --sim_mode static --data data/processed/processed_traffic_7days.csv --lbMode all
```

**输出**：仿真结果保存在 `results/simulation/`

#### 步骤 5：对比分析

[![方式1: 动态分析](https://img.shields.io/badge/方式1-%E5%8A%A8%E6%80%81%E5%88%86%E6%9E%90-blue)](https://shields.io/) <span style="color:red">(推荐)</span>

```bash
# 分析动态模式仿真的结果（前 301 个时间步） --默认模式：dynamic
python scripts/run_comparison.py --sim_mode dynamic --start_timestep 0 --end_timestep 300
```

[![方式2: 静态分析](https://img.shields.io/badge/方式2-%E9%9D%99%E6%80%81%E5%88%86%E6%9E%90-blue)](https://shields.io/)

```bash
# 分析静态模式仿真的结果（前 301 个时间步）
python scripts/run_comparison.py --sim_mode static --start_timestep 0 --end_timestep 300
```

**输出**：分析报告和图表保存在 `results/comparison/{static,dynamic}/`

---

## 📚 系统模块

本项目包含 5 个核心模块，每个模块都有详细的设计文档和使用指南：

### 1. 数据生成模块
生成具有时空相关性的网络流量数据，支持多种流量模式和节假日检测。

- 📖 [模块设计文档](docs/数据生成模块设计.md)

### 2. 数据预处理模块
对原始流量数据进行清洗、归一化和特征工程。

- 📖 [模块设计文档](docs/数据预处理模块设计.md)

### 3. 模型训练模块
训练 LSTM 和 Transformer 预测模型，支持负载预测和增量预测。

- 📖 [模块设计文档](docs/模型训练模块设计.md)

### 4. 仿真模块
完整的 5G/6G 网络仿真环境，包含预测式和反应式负载均衡决策。

- 📖 [模块设计文档](docs/仿真模块设计.md)

### 5. 对比分析模块
多维度性能指标分析和可视化工具，支持时间步范围过滤。

- 📖 [模块设计文档](docs/对比分析模块设计.md)

---

## 📁 项目结构

```
项目根目录/
├── quick_start.py              # 一键运行脚本
├── README.md                   # 本文档
├── requirements.txt            # 依赖清单
├── config/
│   ├── config.yaml            # 系统配置
│   └── config_data.yaml       # 数据生成配置
├── data/
│   ├── raw/                   # 原始数据
│   └── processed/             # 预处理后数据
├── docs/                      # 详细文档
├── models/                    # 训练好的模型
├── results/
│   ├── simulation/           # 仿真结果 CSV
│   ├── comparison/           # 对比分析结果
│   │   ├── static/          # 静态模式分析
│   │   └── dynamic/         # 动态模式分析
│   └── training/            # 训练过程记录
├── logs/                     # 运行日志
├── scripts/                  # 可执行脚本
└── src/                      # 源代码
    ├── data/                # 数据处理模块
    └── models/              # 预测模型
```

---

## 🔧 常见问题

### Q1: 如何快速测试项目？

使用少量数据和训练轮数：
```bash
# 生成 2 天数据
python scripts/generate_data.py --days 2 --output data/raw/raw_traffic_2days.csv

# 预处理
python scripts/preprocess_data.py \
    --input data/raw/raw_traffic_2days.csv \
    --output data/processed/processed_traffic_2days.csv

# 快速训练（5 轮）
python scripts/train_model.py --model lstm --mode load \
    --data data/processed/processed_traffic_2days.csv --epochs 5
```

### Q2: 如何只分析特定时间段？

使用 `--start_timestep` 和 `--end_timestep` 参数：
```bash
# 只分析前 100 个时间步 --默认模式：dynamic
python scripts/run_comparison.py --sim_mode dynamic -s 0 -e 99

# 跳过预热阶段（前 24 步）
python scripts/run_comparison.py --sim_mode static -s 24

# 分析最后 200 个时间步
python scripts/run_comparison.py --sim_mode dynamic -s -200
```

### Q3: 训练时间太长怎么办？

**优化方法**：
- 减少训练轮数：`--epochs 10`
- 减少数据量：`--days 2`
- 使用 GPU（如果可用）
- 调小批大小：修改 `config/config.yaml` 中的 `batch_size`

### Q4: 模型文件保存在哪里？

```
models/
├── lstm_predictor_load_best.pth          # LSTM 负载预测
├── lstm_predictor_delta_best.pth         # LSTM 增量预测
├── transformer_predictor_load_best.pth   # Transformer 负载预测
└── transformer_predictor_delta_best.pth  # Transformer 增量预测
```

### Q5: 如何查看分析结果？

**方式 1：查看 Markdown 报告**
```bash
# 在 VS Code 中打开
code results/comparison/dynamic/analysis_report.md
```

**方式 2：查看图表**
- 打开 `results/comparison/dynamic/figures/` 目录
- 包含对比图表（负载、切换、预测精度等）

**方式 3：查看 JSON 数据**
```bash
# 使用 Python 读取
python -c "import json; print(json.dumps(json.load(open('results/comparison/dynamic/comparison_summary.json')), indent=2))"
```

### Q6: 如何自定义配置？
编辑 `config/config.yaml` 文件：

### Q7: 依赖安装失败怎么办？

```bash
# 升级 pip
python -m pip install --upgrade pip

# 单独安装 PyTorch（根据您的系统）
# CPU 版本
pip install torch --index-url https://download.pytorch.org/whl/cpu

# GPU 版本（CUDA 11.8 示例）
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 安装其他依赖
pip install numpy pandas scikit-learn matplotlib seaborn scipy pyyaml
```

---

## 📊 预期性能

基于默认配置的参考结果（**动态模式 dynamic**，全量 7-day 数据，1992 timesteps）：

| Strategy | gnb_0 Handover Succ | gnb_0 Drop Packet| gnb_0 avg Req Load | gnb_0 avg Served Load | All gnbs avg Req Load | All gnbs avg Served Load |
|------|----------------:|------------:|------------------:|---------------------:|---------------------:|------------------------:|
| **No LB** | 0.000 | 0.264 | 0.350 | 0.350 | 1.156 | 1.156 |
| **Reactive (History)** | 0.038 | 0.226 | 0.350 | 0.350 | 1.186 | 1.186 |
| **Predictive Transformer** | **1.343** | **0.000** | **0.257** | **0.256** | 1.820 | **1.820** |
| **Predictive LSTM** | **1.317** | **0.000** | **0.255** | **0.254** | 1.849 | **1.849** |

**关键发现**（动态模式）：
- **gnb_0 切换成功量** ↑：Predictive LB 通过提前主动触发切换，handover_succ 是 Reactive 的 30 倍以上
- **gnb_0 丢包** → 0：Predictive LB 完全消除了 gnb_0 的丢包（No LB 丢包 0.264）
- **gnb_0 avg Required Load** ↓：Predictive 将 gnb_0 的平均到达负载从 0.350 降到 0.255/0.257，说明持续卸载了流量到邻居基站
- **gnb_0 avg Served Load** ↓：同步降低，gnb_0 自身承载更少流量
- **All gnbs avg Served Load** ↑：整体网络平均服务负载从 1.156 提升到 1.849/1.820，**整体网络利用率显著提高**

---

## 📖 参考文档

### 完整文档列表

**设计文档**（5个）：
- [数据生成模块设计.md](docs/数据生成模块设计.md)
- [数据预处理模块设计.md](docs/数据预处理模块设计.md)
- [模型训练模块设计.md](docs/模型训练模块设计.md)
- [仿真模块设计.md](docs/仿真模块设计.md)
- [对比分析模块设计.md](docs/对比分析模块设计.md)

---

**文档维护**：
- 作者：Yu Qiaoli

