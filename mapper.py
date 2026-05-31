"""
新人入职知识图谱 - 知识图谱构建框架
解析知识数据并构建关系网络
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional


class KnowledgeMapper:
    """知识图谱构建器"""

    def __init__(self):
        """初始化图谱构建器"""
        self.nodes = {}
        self.edges = []
        self.roles = {}
        self.weekly_plans = []
        self.graph = None

    def load_data(self, data_path: str) -> None:
        """
        加载知识数据

        Args:
            data_path: 数据文件路径
        """
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 加载节点
        for node_data in data.get('nodes', []):
            node_id = node_data['id']
            self.nodes[node_id] = {
                'id': node_id,
                'name': node_data['name'],
                'type': node_data.get('type', 'general'),
                'difficulty': node_data.get('difficulty', 1),
                'estimated_hours': node_data.get('estimated_hours', 0),
                'description': node_data.get('description', ''),
                'status': 'not_started',
                'progress': 0
            }

        # 加载边
        self.edges = data.get('edges', [])

        # 加载角色
        for role_data in data.get('roles', []):
            self.roles[role_data['role']] = {
                'required': role_data.get('required', []),
                'optional': role_data.get('optional', [])
            }

        # 加载周计划
        self.weekly_plans = data.get('weekly_plans', [])

        print(f"[图谱] 数据加载完成: {len(self.nodes)} 个知识节点, "
              f"{len(self.edges)} 条关系, {len(self.roles)} 个角色")

    def build_graph(self) -> dict:
        """
        构建完整知识图谱

        Returns:
            {
                'nodes': 节点列表,
                'edges': 边列表,
                'role_knowledge': 角色知识映射,
                'difficulty_distribution': 难度分布,
                'type_distribution': 类型分布
            }
        """
        self.graph = {
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'role_knowledge': {
                role: info for role, info in self.roles.items()
            },
            'statistics': self._calculate_statistics()
        }
        return self.graph

    def _calculate_statistics(self) -> dict:
        """计算图谱统计信息"""
        difficulty_dist = defaultdict(int)
        type_dist = defaultdict(int)
        total_hours = 0

        for node in self.nodes.values():
            difficulty_dist[node['difficulty']] += 1
            type_dist[node['type']] += 1
            total_hours += node['estimated_hours']

        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'total_estimated_hours': total_hours,
            'difficulty_distribution': dict(diff for diff in difficulty_dist.items()),
            'type_distribution': dict(t for t in type_dist.items()),
            'avg_difficulty': round(
                sum(n['difficulty'] for n in self.nodes.values()) / len(self.nodes), 1
            ) if self.nodes else 0,
            'available_roles': list(self.roles.keys())
        }

    def get_node(self, node_id: str) -> Optional[dict]:
        """获取节点信息"""
        return self.nodes.get(node_id)

    def get_prerequisites(self, node_id: str) -> list:
        """获取前置知识"""
        prereqs = []
        for edge in self.edges:
            if edge['to'] == node_id and edge['type'] == 'prerequisite':
                prereq = self.nodes.get(edge['from'])
                if prereq:
                    prereqs.append(prereq)
        return prereqs

    def get_downstream(self, node_id: str) -> list:
        """获取依赖此知识的后续节点"""
        downstream = []
        for edge in self.edges:
            if edge['from'] == node_id and edge['type'] == 'prerequisite':
                node = self.nodes.get(edge['to'])
                if node:
                    downstream.append(node)
        return downstream

    def find_related_nodes(self, node_id: str) -> list:
        """查找相关节点"""
        related = []
        for edge in self.edges:
            if edge['type'] == 'related':
                if edge['from'] == node_id:
                    node = self.nodes.get(edge['to'])
                    if node:
                        related.append({'node': node, 'relation': 'related'})
                elif edge['to'] == node_id:
                    node = self.nodes.get(edge['from'])
                    if node:
                        related.append({'node': node, 'relation': 'related'})
        return related

    def search_nodes(self, keyword: str) -> list:
        """搜索知识点"""
        results = []
        keyword_lower = keyword.lower()
        for node in self.nodes.values():
            if (keyword_lower in node['name'].lower()
                    or keyword_lower in node['description'].lower()):
                results.append(node)
        return results

    def get_path_between(self, from_id: str, to_id: str) -> list:
        """查找两个知识点之间的路径"""
        if from_id not in self.nodes or to_id not in self.nodes:
            return []

        # BFS查找
        visited = {from_id}
        queue = [[from_id]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == to_id:
                return [self.nodes[nid] for nid in path]

            for edge in self.edges:
                if edge['from'] == current and edge['type'] == 'prerequisite':
                    next_id = edge['to']
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append(path + [next_id])

        return []

    def generate_visualization_html(self, output_path: str = 'knowledge_graph.html') -> str:
        """生成可视化HTML"""
        if not self.graph:
            self.build_graph()

        nodes_json = json.dumps([
            {
                'id': n['id'],
                'name': n['name'],
                'type': n['type'],
                'difficulty': n['difficulty']
            }
            for n in self.graph['nodes']
        ], ensure_ascii=False)

        edges_json = json.dumps([
            {
                'source': e['from'],
                'target': e['to'],
                'type': e['type']
            }
            for e in self.graph['edges']
        ], ensure_ascii=False)

        type_colors = {
            'onboarding': '#6366f1',
            'tool': '#22c55e',
            'language': '#f59e0b',
            'database': '#3b82f6',
            'backend': '#ec4899',
            'architecture': '#8b5cf6',
            'devops': '#14b8a6',
            'process': '#f97316',
            'general': '#6b7280'
        }

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>知识图谱可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-4">
    <div class="max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold mb-4">知识图谱可视化</h1>
        <div id="graph" class="bg-white rounded-lg shadow" style="height:600px"></div>
    </div>
    <script>
        const width = document.getElementById('graph').clientWidth;
        const height = 600;

        const nodes = {nodes_json};
        const links = {edges_json};

        const colorMap = {json.dumps(type_colors, ensure_ascii=False)};

        const svg = d3.select('#graph').append('svg')
            .attr('width', width)
            .attr('height', height);

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));

        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => d.type === 'prerequisite' ? 2 : 1)
            .attr('stroke-dasharray', d => d.type === 'related' ? '5,5' : null);

        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .join('circle')
            .attr('r', d => 5 + d.difficulty * 3)
            .attr('fill', d => colorMap[d.type] || '#999')
            .call(d3.drag()
                .on('start', (event, d) => {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }})
                .on('drag', (event, d) => {{
                    d.fx = event.x;
                    d.fy = event.y;
                }})
                .on('end', (event, d) => {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}));

        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .join('text')
            .text(d => d.name)
            .attr('font-size', '12px')
            .attr('dx', 10)
            .attr('dy', 4);

        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node.attr('cx', d => d.x).attr('cy', d => d.y);
            label.attr('x', d => d.x).attr('y', d => d.y);
        }});

        const tooltip = d3.select('#graph').append('div')
            .attr('class', 'absolute hidden bg-white border rounded shadow-lg p-2 text-sm');

        node.on('mouseover', (event, d) => {{
            tooltip.html(`${{d.name}}<br>类型: ${{d.type}}<br>难度: ${{d.difficulty}}`)
                .style('left', (event.offsetX + 10) + 'px')
                .style('top', (event.offsetY + 10) + 'px')
                .classed('hidden', false);
        }}).on('mouseout', () => tooltip.classed('hidden', true));
    </script>
</body>
</html>"""

        Path(output_path).write_text(html, encoding='utf-8')
        print(f"可视化已生成: {output_path}")
        return output_path


if __name__ == '__main__':
    mapper = KnowledgeMapper()
    mapper.load_data('data/sample.json')
    graph = mapper.build_graph()

    stats = graph['statistics']
    print(f"\n图谱统计:")
    print(f"  知识节点数: {stats['total_nodes']}")
    print(f"  关系数: {stats['total_edges']}")
    print(f"  学习总时长: {stats['total_estimated_hours']} 小时")
    print(f"  可用角色: {', '.join(stats['available_roles'])}")

    mapper.generate_visualization_html('output/knowledge_graph.html')