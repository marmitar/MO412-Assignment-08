from argparse import ArgumentParser, FileType
from enum import Enum, auto, unique
import networkx as nx
from networkx.algorithms import components
import os.path
from typing import BinaryIO, Iterator, TextIO


def iter_csv(file: TextIO, /, *, sep: str = ',') -> Iterator[tuple[str, ...]]:
    """Iterate over fields on a CSV file."""
    for line in file:
        fields = (field.strip() for field in line.strip().split(sep))
        fields = tuple(field for field in fields if field)
        if fields:
            yield fields


def read_graph(*, nodes: TextIO, links: TextIO):
    """Read nodes and links from the provided files."""
    graph = nx.DiGraph()

    for name, ident in iter_csv(nodes):
        graph.add_node(ident, label=name)

    for id_tail, id_head in iter_csv(links):
        graph.add_edge(id_tail, id_head)

    return graph


def strongly_connected_components(graph: nx.DiGraph, /) -> Iterator[set[str]]:
    """Static typing for the SCC algorithm on NetworkX."""
    return components.strongly_connected_components(graph)


def add_components(graph: nx.DiGraph, /):
    """Identify each strongly connected component on a digraph."""
    for comp_id, comp_nodes in enumerate(strongly_connected_components(graph)):
        comp = {node: comp_id for node in comp_nodes}
        nx.set_node_attributes(graph, comp, 'component')

    return graph


def node_colors(graph: nx.Graph, /):
    """List the color of each node on `graph` according to its component."""
    from matplotlib import rcParams

    colors: list[str] = rcParams['axes.prop_cycle'].by_key()['color']
    component: dict[str, int] = nx.get_node_attributes(graph, 'component')

    return tuple(colors[component[node]] for node in graph)


def draw_graph(graph: nx.DiGraph, /, output: BinaryIO | None = None, *, draw_components: bool = True):
    """Draw graph and its components using Matplotlib."""
    from matplotlib import pyplot as plt

    colors = node_colors(graph) if draw_components else None
    nx.draw_kamada_kawai(graph, node_color=colors, node_size=1000, labels=nx.get_node_attributes(graph, 'label'))

    if output is None:
        plt.show(block=True)
    else:
        plt.savefig(output)


try:
    DEFAULT_NODES = os.path.join(os.path.dirname(__file__), 'nodes.csv')
    DEFAULT_LINKS = os.path.join(os.path.dirname(__file__), 'links.csv')
except NameError:
    DEFAULT_NODES = 'nodes.csv'
    DEFAULT_LINKS = 'links.csv'


@unique
class OutputMode(Enum):
    """Special output modes where no file is generated."""
    NO_OUTPUT = auto()
    SHOW_OUTPUT = auto()


if __name__ == '__main__':
    parser = ArgumentParser('scc.py')
    parser.add_argument('-n', '--nodes', type=FileType(mode='r', encoding='utf8'), default=DEFAULT_NODES,
        help=f'Path for the \'node.csv\' file. (default: {DEFAULT_NODES})')
    parser.add_argument('-l', '--links', type=FileType(mode='r', encoding='utf8'), default=DEFAULT_LINKS,
        help=f'Path for the \'links.csv\' file. (default: {DEFAULT_LINKS})')
    parser.add_argument('-d', '--draw', type=FileType(mode='wb'),
        nargs='?', default=OutputMode.NO_OUTPUT, const=OutputMode.SHOW_OUTPUT,
        help='Draw NetworkX graph using Matplotlib.')
    args = parser.parse_intermixed_args()

    graph = read_graph(nodes=args.nodes, links=args.links)
    graph = add_components(graph)

    if args.draw is OutputMode.SHOW_OUTPUT:
        draw_graph(graph)
    elif args.draw is not OutputMode.NO_OUTPUT:
        draw_graph(graph, output=args.draw)
