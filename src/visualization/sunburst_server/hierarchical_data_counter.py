from typing import List
import uuid
import pandas as pd


class Node:
    def __init__(self, name, parent_id=None):
        self.id = str(uuid.uuid4()) if parent_id is not None else ""
        self.name = name
        self.children = {}
        self.value = 0
        self.parent_id = parent_id
    
    def copy(self):
        copy = Node(self.name, self.parent_id)
        copy.id = self.id
        copy.name = self.name
        copy.children = self.children
        copy.value = self.value
        copy.parent_id = self.parent_id
        return copy


    def add(self, hierarchy: List):
        self.value += 1
        if len(hierarchy) == 0:
            return
        name = hierarchy.pop()
        if name not in self.children:
            self.children[name] = Node(name, self.id)
            self.children[name].add(hierarchy)
        else:
            self.children[name].add(hierarchy)

    def get_all_descendants(self):
        return self._get_all_descendants([])

    def _get_all_descendants(self, result=None):
        result = result if result is not None else []
        for child in self.children.values():
            result.append(child)
            child._get_all_descendants(result)

        return result

    def get_descendants_at_levels(self, levels):
        assert all(level >= 1 for level in levels)
        assert len(set(levels)) == len(levels)
        levels = list(sorted(levels))
        return self._get_descendants_at_levels(levels, [], 1)

    def _get_descendants_at_levels(self, levels, result, current_level):
        for child in self.children.values():
            if current_level == levels[0]:
                node = child.copy()
                node.parent_id = ""
                result.append(node)
            elif current_level in levels:
                result.append(child)
            child._get_descendants_at_levels(levels, result, current_level + 1)

        return result

    def to_dict(self):
        return {
            "id": self.id,
            "parent": self.parent_id,
            "name": self.name,
            "value": self.value
        }


class HierarchicalDataCounter():
    def __init__(self, hierarchies):
        self.tree = Node("TOTAL")
        reversed_hierarchies = [list(reversed(hierarchy))
                                for hierarchy in hierarchies]
        for hierarchy in reversed_hierarchies:
            self.tree.add(hierarchy)

    def nodes_to_df(self, nodes):
        return pd.DataFrame(
            [node.to_dict() for node in nodes]
        )

    def get_df(self):
        nodes = self.tree.get_all_descendants()
        return self.nodes_to_df(nodes)

    def get_df_at_levels(self, levels: List[int]):
        nodes = self.tree.get_descendants_at_levels(levels)
        return self.nodes_to_df(nodes)


if __name__ == "__main__":
    hierarchies = [
        ['home', 'momir', 'repos'],
        ['home', 'momir',],
        ['home', 'lost+found',],
        ['var', 'log'],
        ['lib',],
    ]

    counter = HierarchicalDataCounter(hierarchies)
    print(counter.get_df()[["parent", "name", "value"]])
    print()
    print(counter.get_df_at_levels([3, 5])[["parent", "name", "value"]])
