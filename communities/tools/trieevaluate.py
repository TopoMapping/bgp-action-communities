import argparse
import pickle
from utils import PrefixTree


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Possible communities", required=True)
    parser.add_argument('-p', '--pickle', dest='pickle', help="Pickle with the Trie", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output the pickle captured communities", required=True)

    # env variables
    args = parser.parse_args()
    input_txt = args.input
    trie_pkl = args.pickle
    output_txt = args.output

    # global communities
    communities_trie = set()

    with open(trie_pkl, "rb") as file_to_process:
        trie = pickle.load(file_to_process)

    with open(input_txt, "rt") as file_to_process:
        for line in file_to_process:
            community = line.strip()

            # evaluate the 32 bits community inferred previously
            if len(community.split(':')) == 2:
                asn, comm = community.split(':')

                # check if we have enough data to evaluate
                if asn in trie:
                    if trie[asn].find("{:05d}".format(int(comm))) == '5':
                        communities_trie.add(community)

    arq = open(output_txt, "wt")
    for comm in communities_trie:
        arq.write(f"{comm}\n")
    arq.close()
