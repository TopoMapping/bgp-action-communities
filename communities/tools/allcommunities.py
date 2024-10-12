import argparse

# Global Variables
all_communities = {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB file processed by bgpscanner.", required=True)
    parser.add_argument('-f', '--filter', dest='filter', help="Filter by the number of occurrences (default=1).")
    parser.add_argument('-o', '--output', dest='output', help="Name of output file.", required=True)

    args = parser.parse_args()
    rib = args.input
    output = args.output

    if args.filter:
        filter_occurrences = int(args.filter)
    else:
        filter_occurrences = 1

    with open(rib, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            comm_list = rib_extraction[7]

            # Save all communities on the RIB
            for comm in comm_list.split(' '):
                if comm.split(':')[0].isdigit():
                    comm = comm.strip()
                    if comm in all_communities:
                        all_communities[comm] += 1
                    else:
                        all_communities[comm] = 1

    # Only save communities with more than filter occurrences number, the defautl is everything
    arq = open(output, "wt")
    for comm in all_communities:
        if all_communities[comm] >= filter_occurrences:
            arq.write("{}\n".format(comm))
    arq.close()
