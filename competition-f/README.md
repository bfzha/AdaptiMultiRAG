# 2026 研赛 F 题：算力约束下提升大语言模型能力的资源配置建模

Python 实现四问递进建模流水线。

## 结构

```
competition-f/
├── config/paths.yaml       # 数据根目录
├── scripts/
│   ├── bootstrap_data.py   # 补齐缺失附件（公开源 + 半合成）
│   └── download_data.py    # 下载 RegMix 等公开 CSV
├── src/
│   ├── q1_quality.py       # 质量评分 Q
│   ├── q1_conflict.py      # 冲突消解
│   ├── q1_mixture.py       # clr 配比-Loss 模型
│   ├── q2_scaling_law.py   # 广义标度律 + 弹性
│   ├── q3_optimization.py  # 算力约束优化
│   └── q4_forecast.py      # 桥接 + 分解 + 预测
├── run_all.py
└── outputs/                # 各问结果
```

## 运行

```bash
cd /workspace/competition-f
pip install -r requirements.txt
python run_all.py
```

将官方 `real_attachments/` 放到 `/workspace/real_attachments` 后重新运行，会自动使用真实数据（优先于 bootstrap 合成数据）。

## 输出

| 问题 | 主要文件 |
|------|---------|
| Q1 | `outputs/q1/quality_scores_*.csv`, `mixture_validation.json` |
| Q2 | `outputs/q2/scaling_law_params.json`, `elasticity_table.csv` |
| Q3 | `outputs/q3/optimal_configs.csv`, `structural_shift_analysis.json` |
| Q4 | `outputs/q4/decomposition_results.csv`, `frontier_forecast_*.csv` |
