import os
import sys
import networkx as nx
from pathlib import Path


def compute_aggregation(buffer, output_file):
    # read the siblings file and use a graph G to support
    G = nx.Graph()

    for line in buffer:
        sibling_list = line.split(' ')[0].split(',')
        first_element = sibling_list[0]

        # link the first element with every other element
        for next_element in sibling_list[1:]:
            G.add_edge(first_element, next_element)

    # output the corrected file with independent connected components on Graph G
    arq = open(output_file, "wt")
    for component in nx.connected_components(G):
        sibling_candidate_list = []
        for element in component:
            sibling_candidate_list.append(int(element))

        sibling_candidate_list.sort()
        for sibling in sibling_candidate_list[:-1]:
            arq.write(f"{sibling},")
        arq.write(f"{sibling_candidate_list[-1]} \n")
    arq.close()


if __name__ == "__main__":
    input_files = sys.argv[1:-1]
    output_file = sys.argv[-1]

    # read to a memory buffer
    buffer = []
    for fname in input_files:
        with open(fname) as infile:
            for line in infile:
                buffer.append(line.strip())

    compute_aggregation(buffer, output_file)
