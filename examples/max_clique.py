import networkx as nx
from itertools import combinations

from algoworkbench import compute, feasibility, score


@compute
def max_clique(graph: nx.Graph) -> set:
    pass

@feasibility
def evaluate(graph: nx.Graph, clique: set):
    if len(clique - graph.nodes()) > 0:
        return False
    if len(set(combinations(clique, 2)) - graph.edges()) > 0:
        return False
    return True
        

@score
def clique_score(clique: set):
    return len(clique)


G = nx.path_graph(10)
max_clique(G)