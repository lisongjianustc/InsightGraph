# InsightGraph Stage 1 Benchmark 候选样本

## 1. 文档目的

本文件用于给 `Stage 1` 建立人工验收基准样本。

使用方式：

1. 由 Codex 先准备正样本候选和反样本候选。
2. 你逐条标记：
   - 是否应入选日报
   - 是否高优先级
   - 备注
3. 后续用这份标注结果检查：
   - 抓取是否完整
   - 去重与版本归并是否合理
   - 排序前列是否符合你的直觉
   - 精读级结论与证据是否足够可信

## 2. 选样原则

本轮选样遵循你已经确认的偏好：

- 分类优先级：`cs.AI > stat.ML > cs.CV`
- 正样本偏好：
  - 研究问题重要
  - 方法上有明显新意
  - 值得你后续精读
- 反样本偏好：
  - 标题很强但内容普通
  - 热点跟风论文
  - 摘要写得很大但证据不足

注意：

- 反样本候选**不等于低质量论文**。
- 它们只是更适合拿来测试系统“不要误选”的能力，或者测试排序是否会被热点标题和 buzzword 干扰。

## 3. 样本来源

本轮候选基于 `2026-03-27` 的 arXiv recent 列表人工初筛：

- [cs.AI recent](https://arxiv.org/list/cs.AI/recent)
- [stat.ML recent](https://arxiv.org/list/stat.ML/recent)
- [cs.CV recent](https://arxiv.org/list/cs.CV/recent)

初筛判断依据主要来自：

- 论文标题
- 分类信息
- 少量 comments / metadata 信号
- 与你的产品目标和研究偏好的匹配度

## 4. 你的标记说明

建议你按下面规则标：

- `是否应入选`：
  - `是`
  - `否`
- `是否高优先级`：
  - `是`
  - `否`
  - 或留空
- `备注`：
  - 记录你为什么这样判断

## 5. 正样本候选（20 篇）

| # | 分类 | arXiv | 标题 | 初步理由 | 你标记：是否应入选 | 你标记：是否高优先级 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cs.AI | [2603.25737](https://arxiv.org/abs/2603.25737) | Training the Knowledge Base through Evidence Distillation and Write-Back Enrichment | 与知识库增强、证据蒸馏直接相关，问题重要且和 InsightGraph 目标高度贴近。 |  |  |  |
| 2 | cs.AI | [2603.25720](https://arxiv.org/abs/2603.25720) | R-C2: Cycle-Consistent Reinforcement Learning Improves Multimodal Reasoning | 面向多模态推理，题目呈现出明确方法创新信号，值得判断是否真有增量。 |  |  |  |
| 3 | cs.AI | [2603.25450](https://arxiv.org/abs/2603.25450) | Cross-Model Disagreement as a Label-Free Correctness Signal | 正确性信号和可靠性评估是核心问题，若方法成立，对模型评估和推理质量控制都很重要。 |  |  |  |
| 4 | cs.AI | [2603.25412](https://arxiv.org/abs/2603.25412) | Beyond Content Safety: Real-Time Monitoring for Reasoning Vulnerabilities in Large Language Models | 从内容安全扩展到推理脆弱性监控，问题重要且具有长期价值。 |  |  |  |
| 5 | cs.AI | [2603.25293](https://arxiv.org/abs/2603.25293) | DAGverse: Building Document-Grounded Semantic DAGs from Scientific Papers | 面向科学论文的文档 grounded 结构化表示，与研究情报系统高度相关。 |  |  |  |
| 6 | cs.AI | [2603.25284](https://arxiv.org/abs/2603.25284) | SliderQuant: Accurate Post-Training Quantization for LLMs | LLM 量化仍是重要现实问题，若精度和效率权衡做得好，值得深入看方法。 |  |  |  |
| 7 | cs.AI | [2603.25158](https://arxiv.org/abs/2603.25158) | Trace2Skill: Distill Trajectory-Local Lessons into Transferable Agent Skills | 关注 agent 技能迁移，题目显示出较强的方法意识，适合作为 agent 方向样本。 |  |  |  |
| 8 | cs.AI | [2603.25133](https://arxiv.org/abs/2603.25133) | RubricEval: A Rubric-Level Meta-Evaluation Benchmark for LLM Judges in Instruction Following | LLM judge 的可信度是关键问题，benchmark 与 meta-eval 方向通常值得重点检查。 |  |  |  |
| 9 | cs.AI | [2603.25075](https://arxiv.org/abs/2603.25075) | Sparse Visual Thought Circuits in Vision-Language Models | 视觉语言模型的机制解释方向，具备方法新意和潜在长期研究价值。 |  |  |  |
| 10 | cs.AI | [2603.25035](https://arxiv.org/abs/2603.25035) | Mechanistically Interpreting Compression in Vision-Language Models | 机制解释 + 压缩现象分析，问题有深度，适合检验系统是否能抓出“值得深读”的论文。 |  |  |  |
| 11 | stat.ML | [2603.25579](https://arxiv.org/abs/2603.25579) | The Rules-and-Facts Model for Simultaneous Generalization and Memorization in Neural Networks | 试图同时解释泛化与记忆，问题本身重要，理论味较强。 |  |  |  |
| 12 | stat.ML | [2603.25466](https://arxiv.org/abs/2603.25466) | Residual-as-Teacher: Mitigating Bias Propagation in Student--Teacher Estimation | student-teacher 估计中的 bias propagation 是实际且基础的问题，方法角度明确。 |  |  |  |
| 13 | stat.ML | [2603.25311](https://arxiv.org/abs/2603.25311) | Practical Efficient Global Optimization is No-regret | EGO / BO 方向的问题经典且实用，若 no-regret 结果扎实，值得高优先级判断。 |  |  |  |
| 14 | stat.ML | [2603.25657](https://arxiv.org/abs/2603.25657) | Instance-optimal stochastic convex optimization: Can we improve upon sample-average and robust stochastic approximation? | 题目直接切中优化理论核心问题，理论价值高，适合做“值得精读”样本。 |  |  |  |
| 15 | stat.ML | [2603.25622](https://arxiv.org/abs/2603.25622) | The Geometry of Efficient Nonconvex Sampling | 非凸采样几何性质是有长期价值的理论问题，值得看是否有真正新见解。 |  |  |  |
| 16 | stat.ML | [2603.25017](https://arxiv.org/abs/2603.25017) | Discrete Causal Representation Learning | 因果表示学习本身重要，离散建模方向也具有明确的新意信号。 |  |  |  |
| 17 | cs.CV | [2603.25744](https://arxiv.org/abs/2603.25744) | MuRF: Unlocking the Multi-Scale Potential of Vision Foundation Models | 视觉基础模型的 multi-scale 能力是重要方向，方法题目有较强研究价值信号。 |  |  |  |
| 18 | cs.CV | [2603.25741](https://arxiv.org/abs/2603.25741) | Vega: Learning to Drive with Natural Language Instructions | 自动驾驶 + 自然语言指令是大问题，值得检验是否只是任务包装，还是方法有实质贡献。 |  |  |  |
| 19 | cs.CV | [2603.25739](https://arxiv.org/abs/2603.25739) | MegaFlow: Zero-Shot Large Displacement Optical Flow | 光流是经典问题，“zero-shot + large displacement”给出较强方法创新信号。 |  |  |  |
| 20 | cs.CV | [2603.25730](https://arxiv.org/abs/2603.25730) | PackForcing: Short Video Training Suffices for Long Video Sampling and Long Context Inference | 长视频与长上下文推理是热点但也确实重要，适合放入正样本看你是否认为它真正值得精读。 |  |  |  |

## 6. 反样本候选（10 篇）

| # | 分类 | arXiv | 标题 | 放入反样本池的原因 | 你标记：是否应入选 | 你标记：是否高优先级 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cs.AI | [2603.25719](https://arxiv.org/abs/2603.25719) | Agent Factories for High Level Synthesis: How Far Can General-Purpose Coding Agents Go in Hardware Optimization? | 题目看起来强，但场景偏硬件优化，与你当前主线研究情报目标的直接相关性较弱。 |  |  |  |
| 2 | cs.AI | [2603.25551](https://arxiv.org/abs/2603.25551) | Voxtral TTS | 大模型 / 大作者名单很容易吸引注意，但未必符合你当前“问题重要且值得深读”的筛选口径。 |  |  |  |
| 3 | cs.AI | [2603.25334](https://arxiv.org/abs/2603.25334) | Agentic Trust Coordination for Federated Learning through Adaptive Thresholding and Autonomous Decision Making in Sustainable and Resilient Industrial Networks | 标题存在明显 buzzword 堆叠信号，适合作为“不要被标题牵着走”的反样本。 |  |  |  |
| 4 | cs.AI | [2603.25097](https://arxiv.org/abs/2603.25097) | ElephantBroker: A Knowledge-Grounded Cognitive Runtime for Trustworthy AI Agents | 关键词密集、概念包装感强，适合测试系统是否会误把叙事型论文排得过高。 |  |  |  |
| 5 | stat.ML | [2603.25530](https://arxiv.org/abs/2603.25530) | Adaptive Subspace Modeling With Functional Tucker Decomposition | 更像方法专向或技术型样本，适合测试系统是否会把与你偏好不完全匹配的论文误抬高。 |  |  |  |
| 6 | stat.ML | [2603.25370](https://arxiv.org/abs/2603.25370) | A Distribution-to-Distribution Neural Probabilistic Forecasting Framework for Dynamical Systems | 题目偏框架型和应用型，适合放进反样本池验证系统是否过度偏好“看起来很全”的方法论文。 |  |  |  |
| 7 | stat.ML | [2603.25397](https://arxiv.org/abs/2603.25397) | A Causal Framework for Evaluating ICU Discharge Strategies | 问题可能有现实价值，但与你当前优先关注的 AI / ML 主线相关性相对较弱。 |  |  |  |
| 8 | cs.CV | [2603.25746](https://arxiv.org/abs/2603.25746) | ShotStream: Streaming Multi-Shot Video Generation for Interactive Storytelling | 热点生成方向，标题吸引力强，但很可能不是你当前最值得精读的研究问题。 |  |  |  |
| 9 | cs.CV | [2603.25738](https://arxiv.org/abs/2603.25738) | PSDesigner: Automated Graphic Design with a Human-Like Creative Workflow | “human-like creative workflow” 容易制造强叙事感，适合测试系统是否被包装性表述带偏。 |  |  |  |
| 10 | cs.CV | [2603.25736](https://arxiv.org/abs/2603.25736) | How good was my shot? Quantifying Player Skill Level in Table Tennis | 问题具体但较窄，适合测试系统是否会把局部有趣但整体优先级不高的工作误判为重点。 |  |  |  |

## 7. 建议你如何标注

建议你先不要一次性看 30 篇全文，先按以下顺序做：

1. 先看标题与摘要，快速标 `是否应入选`
2. 对你犹豫的样本，再看 PDF 和方法部分
3. 最后再标 `是否高优先级`

建议你在备注中优先写下面几类原因：

- 问题值得不值得长期关注
- 题目是否只是包装得强
- 方法到底有没有实质新意
- 即使做得不错，你愿不愿意花时间精读

## 8. 标注完成后的下一步

你标完之后，Codex 可以继续为你做两件事：

1. 把这份人工标注样本转成结构化 benchmark 数据文件。
2. 基于你的标注结果，反向修正 `Stage 1` 的排序、筛选与知识链接策略。
