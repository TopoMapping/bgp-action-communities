import argparse
from collections import Counter
from utils import has_loop, has_as_set, canonical_aspath


# Global variables
asn_communities_dict = {}
asn_com_occur_dict = {}
siblings_relations = {}
community_candidates = set()


def siblings_relationship(file_line):
    # relations for O(constant)
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    siblings_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        siblings_relations[asn] = first_asn


def process_line(as_path, comm_list, as_path_size=2):
    # ignore if the AS path has sets
    if has_as_set(as_path):
        return

    # ignore if the AS path has loops
    if has_loop(as_path):  # if it has loop, that AS-path does not process
        return

    # do not compute empty community list
    local_comm_list = comm_list.split(' ')
    if not len(local_comm_list):
        return

    # Remove prepends from the AS path
    # the best option is to check after if's, but we need to track the ASN occurrence without repetitions
    local_as_path = canonical_aspath(as_path)

    if len(local_as_path) < as_path_size:  # do not evaluate short AS-paths
        return

    # change the ASes for its siblings in the AS-path
    for asn in local_as_path:
        if asn in siblings_relations:
            local_as_path[local_as_path.index(asn)] = siblings_relations[asn]

    # remove potential redundancy
    local_as_path = canonical_aspath(as_path)

    # Process indexes for the community that appears
    for community in local_comm_list:
        if len(community.split(':')) == 2:  # only 32 bits communities
            asn, comm = community.split(':')

            if asn in asn_communities_dict:
                if community in asn_communities_dict[asn]:
                    # the community exists
                    count_local_as_path = Counter(as_path.split(' '))

                    for as_in_path in local_as_path:
                        if as_in_path in asn_communities_dict[asn][community]:
                            # check if the actual counter is bigger indicating prepend
                            if asn_communities_dict[asn][community][as_in_path] < count_local_as_path[as_in_path]:
                                # if the current number of AS-path occurrence is lower, then it is a "prepend" situation
                                asn_communities_dict[asn][community][as_in_path] = count_local_as_path[as_in_path]
                        else:
                            asn_communities_dict[asn][community][as_in_path] = count_local_as_path[as_in_path]
                else:
                    # the community do not exist yet
                    asn_communities_dict[asn][community] = {}

                    count_local_as_path = Counter(as_path.split(' '))
                    for as_in_path in local_as_path:
                        asn_communities_dict[asn][community][as_in_path] = count_local_as_path[as_in_path]
            else:
                # initialize the first occurrence of the ASN and its communities
                asn_communities_dict[asn] = {}
                asn_communities_dict[asn][community] = {}

                count_local_as_path = Counter(as_path.split(' '))
                for as_in_path in local_as_path:
                    asn_communities_dict[asn][community][as_in_path] = count_local_as_path[as_in_path]

    for community in local_comm_list:
        if len(community.split(':')) == 2:  # only 32 bits communities
            asn, comm = community.split(':')

            # check if the AS is prepended and do not count
            count_local_as_path = Counter(as_path.split(' '))

            # count how many times the community occur with the AS in the AS-path
            if community in asn_com_occur_dict:
                if asn in local_as_path:
                    if prepend_relaxation:
                        # prepend relaxation
                        if count_local_as_path[asn] > 1:
                            # count prepended ASN as do not appear
                            asn_com_occur_dict[community][1] += 1
                        else:
                            asn_com_occur_dict[community][0] += 1
                    else:
                        # if relaxation is not on, count any appearance as a fail
                        asn_com_occur_dict[community][0] += 1
                else:
                    asn_com_occur_dict[community][1] += 1

            else:
                # create an entry with a community with properties
                # 0 pos = appeared
                # 1 pos = not appeared
                asn_com_occur_dict[community] = [0, 0]

                if asn in local_as_path:
                    if count_local_as_path[asn] > 1:
                        # count prepended ASN as do not appear
                        asn_com_occur_dict[community][1] += 1
                    else:
                        asn_com_occur_dict[community][0] += 1
                else:
                    asn_com_occur_dict[community][1] = 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB File", required=True)
    parser.add_argument('-s', '--squatters', dest='squatters', help="Squatters.", required=True)
    parser.add_argument('-p', '--prepend', dest='prepend', help="Prepend relaxation.", action='store_true')
    parser.add_argument('-f', '--filter', dest='filter', help="Minimum occurences (default = 1)", required=False)
    parser.add_argument('-t', '--threshold', dest='threshold', help="Removal threshold.", required=False)
    parser.add_argument('-o', '--output', dest='output', help="Output of computed TE communities", required=True)

    args = parser.parse_args()
    rib_file = args.input
    squatters_file = args.squatters
    output = args.output

    # default threshold
    threshold = 0.1
    if args.threshold:
        threshold = float(args.threshold)

    # build the partner relations from the relations inference
    # snakemake adjustment to capture the correct squatter aggregated file output: inf-t0.8-r0.9-b0.3-s6-c2
    #squatters_file = os.path.join(squatters_file, 'agg-' + '-'.join(output.split('/')[-1].split('-')[1:]))
    with open(squatters_file, "rt") as file_to_process:
        for line in file_to_process:
            siblings_relationship(line)

    if args.prepend:
        prepend_relaxation = True
    else:
        prepend_relaxation = False

    if args.filter:
        filter = int(args.filter)
    else:
        filter = 1

    # read all the rib and change and extract the relations using the sibling pre-processed
    with open(rib_file, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            as_path = rib_extraction[2]
            comm_list = rib_extraction[7]

            # Compute the data structure
            process_line(as_path, comm_list)

    # cleanup the structure
    for as_comm in asn_communities_dict.copy():
        if int(as_comm) in range(64496, 65536) or \
                int(as_comm) in range(4200000000, 4294967295) or \
                int(as_comm) in [0, 23456]:  # do not add private ASN communities
            # https://www.iana.org/assignments/as-numbers/as-numbers.xhtml
            # remove all entries that are not expected
            del asn_communities_dict[as_comm]

    # remove entries that have the AS in the AS list
    for asn in asn_communities_dict:
        for community in asn_communities_dict[asn].copy():
            # if the ASN from the community is in the AS-path dict, remove it if it is not prepended
            if asn in asn_communities_dict[asn][community]:
                # check for the prepended ASes
                asn_in_path = asn
                # each ASN have a dict of communities with a dict of ASes that appears
                if asn_communities_dict[asn][community][asn_in_path] < 2:
                    del asn_communities_dict[asn][community]

    # now, compute the file list and save the TE communities
    for asn in asn_communities_dict:
        for community in asn_communities_dict[asn]:
            # capture the prepend communities
            for as_in_path in asn_communities_dict[asn][community]:
                if as_in_path == asn:
                    if asn_communities_dict[asn][community][as_in_path] >= 2:
                        #community_candidates.add(community)
                        pass
                        #print("prepend", community)

                #if asn_com_occur_dict[community][1]:
                #    if 0.4 <= float(asn_com_occur_dict[community][0] / asn_com_occur_dict[community][1]) <= 0.6:
                #        print(f"the AS {as_in_path} do not remove communities")

            if asn_com_occur_dict[community][1]:
                if float(asn_com_occur_dict[community][0] / asn_com_occur_dict[community][1]) <= threshold:
                    if asn_com_occur_dict[community][1] >= filter:
                        community_candidates.add(community)
                    #print("threshold", community)

    # save the inferred communities
    arq = open(f"{args.output}", "wt")
    for community in community_candidates:
        arq.write("{}\n".format(community))
    arq.close()

    # Save the structures
    #arq = open(f"{output}.pkl", "wb")
    #pickle.dump([asn_communities_dict, asn_com_occur_dict], arq)
    #arq.close()
