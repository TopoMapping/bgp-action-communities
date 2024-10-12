import os
import argparse
import pickle
import networkx as nx
from utils import levenshtein_distance


# Global Variables
boundary_dict = {}

# save the info about the communities that appear with AS and the target sibling
community_sibling_relations = {}


def compute_sibling_candidates(inner_sibling, threshold, relevance, boundary, static, community_filter):
    # compute siblings candidates
    local_sibling_candidates = {}

    # asn = ASN Y
    for asn in inner_sibling:

        # check if we have the basic structure for the ASN
        if asn not in local_sibling_candidates:
            local_sibling_candidates[asn] = set()

        for i in inner_sibling[asn][1]:
            # noise filter
            # siblings[asn][1][i] = number of occurrences of on ASN over keys from the community AS (v1)
            # siblings[asn][0] = keys related to the community AS without the AS in the AS path (v2)
            if (float(inner_sibling[asn][1][i]) / len(inner_sibling[asn][0])) > relevance \
                    and (inner_sibling[asn][1][i] > static):

                # check if ASN_i exist into the counter
                if i in as_counter:
                    # compute prevalence
                    # siblings[asn][1][i] = number of occurrences of on ASN over keys from the community AS (v1)
                    asn_i_occurrences = float(inner_sibling[asn][1][i])

                    # as_counter = count the global occurrence of an ASN among all keys (v4)
                    asn_i_global_occurrences = float(as_counter[i])

                    # compute the relevance of the relation
                    prevalence = asn_i_occurrences / asn_i_global_occurrences

                    # check the user threshold, prevalence, and add to the sibling list
                    if prevalence >= threshold:
                        add_sibling = True

                        # remove the incorrect siblings related to 16 and 32 bits ASNs overflow on BGP routers
                        if len(asn) >= 5 and len(i) >= 5:
                            if levenshtein_distance(asn, i) == 1:
                                add_sibling = False

                        # check the overflow 16/32 bits ASN used in communities
                        # (32 bits ASN overflow when used in communities)
                        if (str(int(asn) % 2 ** 16) == i) or (str(int(i) % 2 ** 16) == asn):
                            add_sibling = False

                        # check the substrings (prefix/suffix) two digits before or after the main ASN ("fat fingers")
                        if asn[:-2] == i or asn[2:] == i:
                            add_sibling = False

                        if i[:-2] == asn or i[2:] == asn:
                            add_sibling = False

                        # verify if exists, at least, two communities to support the inference
                        if (asn, i) in community_sibling_relations:
                            if len(community_sibling_relations[(asn, i)]) < 2:
                                add_sibling = False
                        else:
                            local_communities = set()

                            # search in all keys related to ASN
                            for asn_keys in inner_sibling[asn][0]:

                                # if the sibling candidate is inside the key
                                if i in asn_keys:

                                    # look in all communities associeted with the key
                                    for comm in inner_sibling[asn][0][asn_keys]:
                                        local_asn, local_comm = comm.split(':')

                                        # if the community is from the ASN, then, save it
                                        if local_asn == asn:
                                            local_communities.add(comm)

                            # save all communities related to the partner association
                            community_sibling_relations[(asn, i)] = local_communities

                            if len(local_communities) < int(community_filter):
                                add_sibling = False

                        if add_sibling:
                            local_sibling_candidates[asn].add(i)

    # apply IXP ASN filter
    for asn in local_sibling_candidates.copy():
        # check if the ASN in relation is a IXP, if so, just ignore everything
        if asn in ixp_asn_set:
            del local_sibling_candidates[asn]
        else:
            for sib in local_sibling_candidates[asn].copy():
                # remove any entry that are IXP
                if sib in ixp_asn_set:
                    local_sibling_candidates[asn].remove(sib)

    # check the number of times ASN i appears without ASN j in all keys (v3)
    for asn_x in local_sibling_candidates:
        # create a relation between the inferred siblings candidates
        for asn_y in local_sibling_candidates[asn_x]:
            # only compute once the relation, this will reduce the number of RIB readings
            if (asn_x, asn_y) not in boundary_dict:
                boundary_dict[(asn_x, asn_y)] = 0

                # only track all times ASN i appears without j once - dynamic approach
                for key in mapped_set:
                    if asn_y in key:
                        if asn_x not in key:
                            boundary_dict[(asn_x, asn_y)] += 1

    # siblings[asn][1][i] = number of occurrences of on ASN over keys from the community AS (v1)
    # boundary_dict[(asn_x, asn_y)] = number of occurrences of X without Y (v3)
    for local_asn_x in local_sibling_candidates:
        for local_asn_y in local_sibling_candidates[local_asn_x].copy():
            # remove the possibility of ZeroDivisionError related to non-possible evaluation
            if boundary_dict[(local_asn_x, local_asn_y)] != 0:
                if inner_sibling[local_asn_x][1][local_asn_y] / boundary_dict[(local_asn_x, local_asn_y)] < boundary:
                    local_sibling_candidates[local_asn_x].remove(local_asn_y)

    # return computed sibling candidates
    return local_sibling_candidates


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Pickle file generated by search siblings.", required=True)
    parser.add_argument('-m', '--map', dest='map', help="Pickle file generated by simplify keys.", required=True)
    parser.add_argument('-x', '--ixp', dest='ixp', help="IXP Filter data from CAIDA.", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output directory", required=True)

    # parametrized input for output
    parser.add_argument('-t', '--threshold', dest='threshold', help="Scope.", required=True)
    parser.add_argument('-r', '--relation', dest='relation', help="Coverage.", required=True)
    parser.add_argument('-b', '--boundary', dest='boundary', help="Consistency.", required=True)
    parser.add_argument('-s', '--static', dest='static', help="Number of announcements.", required=True)
    parser.add_argument('-c', '--communities', dest='communities', help="Number of communities.", required=True)

    # env variables
    args = parser.parse_args()
    siblings_pkl = args.input
    map_pkl = args.map
    output = args.output

    # load the pickle structure
    with open(siblings_pkl, "rb") as file_to_process:
        # siblings = [all keys for the ASN from Community, number occur of each ASN]
        # as_counter = count the global occurrence of an ASN among all keys (v3)
        siblings, as_counter = pickle.load(file_to_process)

    with open(map_pkl, "rb") as file_to_process:
        # siblings = [all keys for the ASN from Community, number occur of each ASN]
        # as_counter = count the global occurrence of an ASN among all keys (v3)
        mapped_set = pickle.load(file_to_process)

    # populate the IXP filter
    ixp_asn_set = set()
    with open(args.ixp, "rt") as file_to_process:
        for ixp_line in file_to_process:
            ixp_asn_set.add(ixp_line.strip())

    # compute the worst scenario to build the first interaction of v3
    # threshold, relation, boundary, static, communities
    t = float(args.threshold)
    r = float(args.relation)
    b = float(args.boundary)
    s = int(args.static)
    c = int(args.communities)

    sibling_candidates = compute_sibling_candidates(siblings, t, r, b, s, c)

    # output the evaluated siblings
    G = nx.Graph()   # we need to use a simple graph to count the connected components
    for i in sibling_candidates:
        for j in sibling_candidates[i]:
            G.add_edge(i, j)

    # save into the file
    rib_name = output.split('/')[-1]
    # os.makedirs(output, exist_ok=True)
    # rib, threshold, relevance, boundary, static, community_filter
    # , f"{rib_name}-t{t}-r{r}-b{b}-s{s}-c{c}"
    arq = open(os.path.join(output), "wt")
    for component in nx.connected_components(G):
        sibling_candidate_list = []
        for element in component:
            sibling_candidate_list.append(int(element))

        sibling_candidate_list.sort()
        for sibling in sibling_candidate_list[:-1]:
            arq.write(f"{sibling},")
        arq.write(f"{sibling_candidate_list[-1]} \n")
    arq.close()

