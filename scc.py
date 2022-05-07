# Python 3.8+ required
from __future__ import annotations
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


def path_to(filename: str):
    """Relative path to `filename` from current 'scc.py' file."""
    try:
        program = __file__
    # some environemnts (like bpython) don't define '__file__',
    # so we assume that the file is in the current directory
    except NameError:
        return filename

    basedir = os.path.dirname(program)
    fullpath = os.path.join(basedir, filename)
    return os.path.relpath(fullpath)


# Default input files
DEFAULT_NODES = path_to('nodes.csv')
DEFAULT_LINKS = path_to('links.csv')
# Special output modes where no file is generated
NO_OUTPUT = object()
SHOW_OUTPUT = object()


if __name__ == '__main__':
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser('scc.py')
    parser.add_argument('-n', '--nodes', metavar='PATH',
        type=FileType(mode='r', encoding='utf8'), default=DEFAULT_NODES,
        help=f'Path for the \'node.csv\' file. (default: {DEFAULT_NODES})')
    parser.add_argument('-l', '--links', metavar='PATH',
        type=FileType(mode='r', encoding='utf8'), default=DEFAULT_LINKS,
        help=f'Path for the \'links.csv\' file. (default: {DEFAULT_LINKS})')
    parser.add_argument('-d', '--draw', metavar='OUTPUT', nargs='?',
        type=FileType(mode='wb'), default=NO_OUTPUT, const=SHOW_OUTPUT,
        help=('Draw NetworkX graph to OUTPUT using Matplotlib. If no argument is provided,'
            ' the graph is drawn on a new window.'))
    args = parser.parse_intermixed_args()

    graph = read_graph(nodes=args.nodes, links=args.links)
    graph = add_components(graph)

    if args.draw is SHOW_OUTPUT:
        draw_graph(graph)
    elif args.draw is not NO_OUTPUT:
        draw_graph(graph, output=args.draw)
