"""
新人入职知识图谱 - 学习路径生成
基于知识图谱生成个性化学习路径
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Optional


class LearningPathGenerator:
    """学习路径生成器"""

    def __init__(self, graph: dict):
        """
        初始化路径生成器

        Args:
            graph: 知识图谱数据
        """
        self.graph = graph
        self.nodes = {n['id']: n for n in graph.get('nodes', [])}
        self.edges = graph.get('edges', [])
        self.role_knowledge = graph.get('role_knowledge', {})

    def generate_path(self, role: str, target_knowledge: list = None,
                      existing_knowledge: list = None,
                      learning_hours_per_week: int = 20) -> dict:
        """
        生成学习路径

        Args:
            role: 角色名称
            target_knowledge: 目标知识点列表（可选，不指定则使用角色默认）
            existing_knowledge: 已有知识列表
            learning_hours_per_week: 每周学习时间

        Returns:
            学习路径
        """
        existing_knowledge = existing_knowledge or []

        # 确定目标知识点
        if not target_knowledge and role in self.role_knowledge:
            target_knowledge = self.role_knowledge[role].get('required', [])

        if not target_knowledge:
            return self._empty_path('未找到目标知识点')

        # 计算前置依赖链
        required_nodes = self._resolve_prerequisites(target_knowledge, existing_knowledge)

        # 按依赖顺序排序
        ordered_nodes = self._topological_sort(required_nodes)

        if not ordered_nodes:
            return self._empty_path('无法确定学习顺序')

        # 生成周计划
        weekly_plan = self._create_weekly_plan(ordered_nodes, learning_hours_per_week)

        return {
            'role': role,
            'target_knowledge': target_knowledge,
            'total_knowledge_points': len(ordered_nodes),
            'new_knowledge_points': len(ordered_nodes) - len(existing_knowledge),
            'total_estimated_hours': sum(n.get('estimated_hours', 0) for n in ordered_nodes),
            'estimated_weeks': len(weekly_plan),
            'existing_knowledge_skipped': existing_knowledge,
            'weekly_plan': weekly_plan,
            'ordered_nodes': ordered_nodes,
            'milestones': self._generate_milestones(weekly_plan)
        }

    def _resolve_prerequisites(self, targets: list,
                                existing: list) -> list:
        """解析前置依赖链"""
        required_set = set(targets)
        queue = deque(targets)

        # BFS遍历前置依赖
        while queue:
            node_id = queue.popleft()
            for edge in self.edges:
                if edge['to'] == node_id and edge['type'] == 'prerequisite':
                    prereq_id = edge['from']
                    if prereq_id not in required_set and prereq_id not in existing:
                        required_set.add(prereq_id)
                        queue.append(prereq_id)

        # 排除已掌握的知识
        result = []
        for node_id in required_set:
            if node_id not in existing:
                node = self.nodes.get(node_id)
                if node:
                    result.append(node)

        return result

    def _topological_sort(self, nodes: list) -> list:
        """拓扑排序"""
        if not nodes:
            return []

        node_ids = set(n['id'] for n in nodes)
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)

        for n in nodes:
            nid = n['id']
            if nid not in in_degree:
                in_degree[nid] = 0

        for edge in self.edges:
            if edge['type'] == 'prerequisite':
                if edge['from'] in node_ids and edge['to'] in node_ids:
                    adjacency[edge['from']].append(edge['to'])
                    in_degree[edge['to']] += 1

        # Kahn算法
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        sorted_ids = []

        while queue:
            current = queue.popleft()
            sorted_ids.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # 按难度排序未在依赖图中的节点
        remaining = [n for n in nodes if n['id'] not in sorted_ids]
        remaining.sort(key=lambda n: (n.get('difficulty', 1), n.get('estimated_hours', 0)))

        result_ids = sorted_ids + [n['id'] for n in remaining]
        id_to_node = {n['id']: n for n in nodes}
        return [id_to_node[nid] for nid in result_ids if nid in id_to_node]

    def _create_weekly_plan(self, ordered_nodes: list,
                            hours_per_week: int) -> list:
        """创建周学习计划"""
        weekly_plan = []
        current_week_hours = 0
        current_week_nodes = []
        week_number = 1

        for node in ordered_nodes:
            node_hours = node.get('estimated_hours', 0)

            if current_week_hours + node_hours > hours_per_week and current_week_nodes:
                weekly_plan.append({
                    'week': week_number,
                    'nodes': current_week_nodes,
                    'total_hours': current_week_hours,
                    'focus': current_week_nodes[0].get('type', 'general')
                })
                week_number += 1
                current_week_nodes = []
                current_week_hours = 0

            current_week_nodes.append(node)
            current_week_hours += node_hours

        if current_week_nodes:
            weekly_plan.append({
                'week': week_number,
                'nodes': current_week_nodes,
                'total_hours': current_week_hours,
                'focus': current_week_nodes[0].get('type', 'general')
            })

        return weekly_plan

    def _generate_milestones(self, weekly_plan: list) -> list:
        """生成里程碑节点"""
        milestones = []

        for week in weekly_plan:
            # 每个里程碑标注本周最核心的知识点
            hardest_node = max(week['nodes'], key=lambda n: n.get('difficulty', 0))
            milestones.append({
                'week': week['week'],
                'milestone': f"完成{hardest_node['name']}学习",
                'difficulty': hardest_node.get('difficulty', 1)
            })

        return milestones

    def _empty_path(self, reason: str) -> dict:
        return {
            'role': '',
            'error': reason,
            'target_knowledge': [],
            'total_knowledge_points': 0,
            'total_estimated_hours': 0,
            'estimated_weeks': 0,
            'weekly_plan': [],
            'ordered_nodes': []
        }

    def generate_role_path(self, role: str, existing_knowledge: list = None) -> dict:
        """为指定角色生成默认路径"""
        if role not in self.role_knowledge:
            role_knowledge = self.role_knowledge
            available = list(role_knowledge.keys()) if role_knowledge else []
            return self._empty_path(f'未找到角色"{role}"，可用角色: {", ".join(available)}')

        return self.generate_path(role=role, existing_knowledge=existing_knowledge)

    def estimate_completion_date(self, path: dict,
                                 start_date: str = None) -> str:
        """估算完成日期"""
        weeks = path.get('estimated_weeks', 0)
        if not weeks:
            return ''

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = datetime.now()

        end = start + timedelta(weeks=weeks)
        return end.strftime('%Y-%m-%d')

    def get_progress_status(self, path: dict, completed_nodes: list) -> dict:
        """获取学习进度状态"""
        all_nodes = [n['name'] for n in path.get('ordered_nodes', [])]
        if not all_nodes:
            return {'progress': 0, 'completed': 0, 'total': 0}

        completed_set = set(completed_nodes)
        completed_count = sum(1 for n in all_nodes if n in completed_set)
        remaining = [n for n in all_nodes if n not in completed_set]

        return {
            'progress': round(completed_count / len(all_nodes) * 100, 1),
            'completed': completed_count,
            'total': len(all_nodes),
            'remaining': remaining,
            'next_to_learn': remaining[0] if remaining else None
        }


if __name__ == '__main__':
    from mapper import KnowledgeMapper

    mapper = KnowledgeMapper()
    mapper.load_data('data/sample.json')
    graph = mapper.build_graph()

    generator = LearningPathGenerator(graph)

    path = generator.generate_path(
        role='后端工程师',
        existing_knowledge=['Python基础', 'Git基础']
    )

    print(f"角色: {path['role']}")
    print(f"总知识点: {path['total_knowledge_points']}")
    print(f"预计总时长: {path['total_estimated_hours']} 小时")
    print(f"预计周数: {path['estimated_weeks']} 周")
    print(f"完成日期: {generator.estimate_completion_date(path)}")
    print()

    for week in path['weekly_plan']:
        print(f"第{week['week']}周 ({week['total_hours']}小时):")
        for node in week['nodes']:
            print(f"  - {node['name']} ({node['estimated_hours']}h)")
        print()

    print("里程碑:")
    for ms in path['milestones']:
        print(f"  第{ms['week']}周: {ms['milestone']}")