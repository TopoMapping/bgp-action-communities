import pickle
import argparse
from utils import has_loop, has_as_set, canonical_aspath

# Global Variables
all_communities = set()
sibling_structure = {}
as_relation = {}
as_counter_dict = {}


def squatter_ases(as_path, comm_list, router_ip):
    """
    Fullfill the structure geo_code_structure with the information about communities
    on each announcement on the RIB file

    :param as_path: as_path, list of ASN's, from the announcement
    :param comm_list: community list from the announcement
    :param router_ip:  the IP of the router that share the information with the collector
    :param lookahead: ASN after the target ASN
    """

    # ignore if the AS path has sets
    if has_as_set(as_path):
        return

    # ignore if the AS path has loops
    if has_loop(as_path):  # if it has loop, that AS-path does not process
        return

    # Remove prepends from the AS path
    # the best option is to check after the if's, but we need to track the ASN occurrence without repetitions
    local_as_path = canonical_aspath(as_path)

    #if len(local_as_path) < 2:  # impossible to evaluate short AS-paths
    #    return

    # Count the AS occurrence even with it is ignored
    for asn in local_as_path:
        if asn in as_counter_dict:
            as_counter_dict[asn] += 1
        else:
            as_counter_dict[asn] = 1

    # Split the community list
    local_comm_list = comm_list.split(' ')
    local_ases_from_comm = set()
    local_ases_from_comm_not_in_path = set()
    local_ases_from_comm_comunities = {}

    # Split all ASes from the communities as we are tracking possible siblings
    for comm in local_comm_list:
        if len(comm.split(':')) == 2:  # only consider now 32 bit communities
            as_comm, comm_comm = comm.split(':')
            local_ases_from_comm.add(as_comm.strip())

            # check if the ASN part of the community is in the AS path
            if as_comm not in local_as_path:
                if int(as_comm) not in range(64496, 65536) and \
                        int(as_comm) not in range(4200000000, 4294967295) and \
                        int(as_comm) not in [0, 23456]:  # do not add private ASN communities
                    # https://www.iana.org/assignments/as-numbers/as-numbers.xhtml
                    local_ases_from_comm_not_in_path.add(as_comm)

                    # save the communities
                    if as_comm in local_ases_from_comm_comunities:
                        local_ases_from_comm_comunities[as_comm].append(comm.strip())
                    else:
                        local_ases_from_comm_comunities[as_comm] = [comm.strip()]

    # Tracking the key ASes
    temporary_list = local_as_path
    temporary_list.insert(0, router_ip)

    # key tuple based on target plus the IP from the router that exchange traffic with the collector
    key = tuple(temporary_list)

    if key in sibling_structure:
        sibling_structure[key][0] += 1  # increment the number of key occurrences
        sibling_structure[key][2].add(local_as_path[-1])  # add the origin to the set

        # Update the occurrences of ASes
        for asn in local_ases_from_comm_not_in_path:
            if asn in sibling_structure[key][1]:
                sibling_structure[key][1][asn] += 1  # increment the occurrence of that ASN
            else:
                sibling_structure[key][1][asn] = 1

    else:
        # the key doesn't exist, need to create the structure
        # create the reference key with occurrence number: counter, sibling dict, origins, all communities
        sibling_structure[key] = [1, {}, set(), local_ases_from_comm_comunities]
        sibling_structure[key][2].add(local_as_path[-1])

        # As the key do not exist yet, all entries are the first
        for asn in local_ases_from_comm_not_in_path:
            sibling_structure[key][1][asn] = 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deep', dest='lookahead', help="How deep search after target ASN. (default=1))")
    parser.add_argument('-m', '--minimum-origin', dest='origin', help="Minimal ASN origin number. (default=1).")
    parser.add_argument('-i', '--input', dest='input', help="RIB/Pickle file processed by bgpscanner.",
                        required=True)
    parser.add_argument('-o', '--output', dest='output', help="Name of output file (default: rib-lookahead.pkl)",
                        required=True)

    args = parser.parse_args()
    rib = args.input
    output = args.output

    # check the minimal number of origin ASNs
    if args.origin:
        minimum_origin = int(args.origin)
    else:
        minimum_origin = 1

    with open(rib, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            as_path = rib_extraction[2]
            comm_list = rib_extraction[7]
            router_ip = rib_extraction[8].split(' ')[0]

            squatter_ases(as_path, comm_list, router_ip)

    # save the pickle file for the processed file
    arq = open(output, "wb")
    # save the structures
    pickle.dump([sibling_structure, as_counter_dict], arq)

    # close the descriptor
    arq.close()
