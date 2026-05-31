# 新人入职知识图谱

为新人构建系统化的学习知识图谱，生成个性化学习路径。

## 项目简介

新员工入职后面对海量信息往往无从下手。本工具通过构建知识图谱的方式，将公司的知识体系结构化呈现，并根据新人的角色和背景生成个性化的学习路径，让入职过程更加高效和系统。

## 核心功能

- **知识图谱构建**：解析文档和资料，构建知识点之间的关系网络
- **学习路径生成**：根据角色和目标生成个性化学习路径
- **前置依赖管理**：自动识别学习前需要掌握的前置知识
- **进度追踪**：记录学习进度，调整学习计划
- **可视化**：直观展示知识结构和学习路径

## 技术架构

```
新人入职知识图谱/
├── mapper.py            # 知识图谱构建框架
├── path_generator.py    # 学习路径生成
├── data/
│   └── sample.json      # 示例知识数据
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 构建知识图谱

```python
from mapper import KnowledgeMapper

mapper = KnowledgeMapper()
mapper.load_data("data/sample.json")
graph = mapper.build_graph()

print(f"节点数: {len(graph['nodes'])}")
print(f"关系数: {len(graph['edges'])}")
```

### 生成学习路径

```python
from path_generator import LearningPathGenerator

generator = LearningPathGenerator(graph)
path = generator.generate_path(
    role="后端工程师",
    target_knowledge=["微服务架构", "Docker"],
    existing_knowledge=["Python基础", "Git"]
)

for step in path:
    print(f"{step['order']}. {step['name']} - {step['estimated_hours']}小时")
```

## 数据格式

```json
{
  "nodes": [
    {
      "id": "python-basics",
      "name": "Python基础",
      "type": "language",
      "difficulty": 1,
      "estimated_hours": 20
    }
  ],
  "edges": [
    {
      "from": "python-basics",
      "to": "python-advanced",
      "type": "prerequisite"
    }
  ],
  "roles": [
    {
      "role": "后端工程师",
      "required": ["微服务架构", "Docker"],
      "optional": ["Kubernetes"]
    }
  ]
}
```

## 学习方法建议

| 学习阶段 | 方法 | 时间占比 |
|----------|------|----------|
| 认知建立 | 阅读文档 + 视频教程 | 20% |
| 实践操作 | 动手实操 + 练习项目 | 50% |
| 深度理解 | 参与真实项目 + code review | 30% |

## 许可证

MIT License