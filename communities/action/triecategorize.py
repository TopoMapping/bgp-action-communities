import argparse
import pickle
from utils import PrefixTree


def lcs(s1, s2):
    """Longest common subsequence"""
    matrix = [["" for x in range(len(s2))] for x in range(len(s1))]
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                if i == 0 or j == 0:
                    matrix[i][j] = s1[i]
                else:
                    matrix[i][j] = matrix[i - 1][j - 1] + s1[i]
            else:
                matrix[i][j] = max(matrix[i - 1][j], matrix[i][j - 1], key=len)
    cs = matrix[-1][-1]
    return len(cs), cs


def lcp(strs):
    """Longest common prefix"""
    prefix = ''
    for char in zip(*strs):
        if len(set(char)) == 1:
            prefix += char[0]
        else:
            break
    return prefix


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Text file with the communities", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output pickle file with Tries computed", required=True)

    # env variables
    args = parser.parse_args()
    input_text = args.input
    output_pkl = args.output

    # list of communities to evaluate
    community_dict = {}

    # list of ASNs to create a PrefiTree to each
    asn_dict = {}

    for line in open(input_text, "rt").readlines():
        comm, meaning, comment = line.split(';')
        community_dict[comm] = meaning

    # group communities with the same meaning for the same AS
    community_meanings = {}
    for community in community_dict:
        asn, comm = community.split(':')

        if asn in community_meanings:
            if community_dict[community] in community_meanings[asn]:
                community_meanings[asn][community_dict[community]].add(community)
            else:
                community_meanings[asn][community_dict[community]] = set()
                community_meanings[asn][community_dict[community]].add(community)
        else:
            community_meanings[asn] = {}
            community_meanings[asn][community_dict[community]] = set()
            community_meanings[asn][community_dict[community]].add(community)

        # add the ASN into the ASes to create a PrefixTree
        if asn not in asn_dict:
            asn_dict[asn] = PrefixTree()

    # group communities with the same meaning for the same AS and the same size
    community_asn_same_size = {}
    for asn in community_meanings:
        for meaning in community_meanings[asn]:
            for community in community_meanings[asn][meaning]:
                if asn in community_asn_same_size:
                    if meaning in community_asn_same_size[asn]:
                        if len(community.split(':')[1]) in community_asn_same_size[asn][meaning]:
                            community_asn_same_size[asn][meaning][len(community.split(':')[1])].add(community)
                        else:
                            community_asn_same_size[asn][meaning][len(community.split(':')[1])] = set()
                            community_asn_same_size[asn][meaning][len(community.split(':')[1])].add(community)
                    else:
                        community_asn_same_size[asn][meaning] = {}
                        # add the community inside its community size
                        community_asn_same_size[asn][meaning][len(community.split(':')[1])] = set()
                        community_asn_same_size[asn][meaning][len(community.split(':')[1])].add(community)
                else:
                    community_asn_same_size[asn] = {}
                    community_asn_same_size[asn][meaning] = {}
                    # add the community inside its community size
                    community_asn_same_size[asn][meaning][len(community.split(':')[1])] = set()
                    community_asn_same_size[asn][meaning][len(community.split(':')[1])].add(community)

    # compute the LCP for each block
    for asn in community_asn_same_size:
        for meaning in community_asn_same_size[asn]:
            for comsize in community_asn_same_size[asn][meaning]:
                groups_of_communities = {}

                for community in community_asn_same_size[asn][meaning][comsize]:
                    asn, comm = community.split(':')

                    if comm[0] in groups_of_communities:
                        groups_of_communities[comm[0]].add(comm)
                    else:
                        groups_of_communities[comm[0]] = set()
                        groups_of_communities[comm[0]].add(comm)

                for each in groups_of_communities:
                    base_set = set()
                    for each_comm in groups_of_communities[each]:
                        comm = "{:05d}".format(int(each_comm))

                        base_set.add(comm)

                    lcp_for_group = lcp(base_set)
                    asn_dict[asn].insert(lcp_for_group, meaning)

    arq = open(output_pkl, "wb")
    pickle.dump(asn_dict, arq)
    arq.close()

