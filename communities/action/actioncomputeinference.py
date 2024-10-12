import sys
import pickle
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="Pickle file processed by actioncompute.py", required=True)

    # options that are mutually exclusive for the path, if none defined, consider all AS-paths
    group_path = parser.add_mutually_exclusive_group()
    group_path.add_argument("-u", "--uphill", dest='uphill', help="Check the path as uphill.", action="store_true")
    group_path.add_argument("-a", "--anypath", dest='anypath', help="Check all the AS-paths.", action="store_true")

    # group the options with and without customer cone check
    group_cone = parser.add_mutually_exclusive_group()
    group_cone.add_argument("-l", "--upcount", dest='upcount', help="Count the paths without customer cone.",
                            action="store_true")
    group_cone.add_argument("-x", "--anycount", dest='anycount', help="Count any path with AS or not (default)",
                            action="store_true")

    # options that are mutually exclusive for occurence
    group_fraction = parser.add_mutually_exclusive_group()
    group_fraction.add_argument("-f", "--fraction", dest='fraction',
                                help="Fraction of occurrences over total occurrences. (default: 0.0)")
    group_fraction.add_argument("-n", "--no_fraction", dest='no_fraction',
                                help="Disable fraction of occurrences over total occurrences.", action="store_true")

    parser.add_argument("-v", "--vantage_point", type=int, dest='vantage_point',
                        help="Number of vantage points to consider for each community. (default: 1)")
    parser.add_argument("-s", "--percent_of_vantage_points", type=float, dest='percent_of_vantage_points',
                        help="Percentage of vantage points that support the -v option. (default: 0.1, aka 10%)")
    parser.add_argument("-k", "--vantage_point_paths", type=int, dest='vantage_point_paths',
                        help="Number of paths per vantage point. (default: 1)")

    # extra options
    parser.add_argument('-p', '--prepend', dest='prepend', help="Prepend relaxation.", action='store_true')

    # output file
    parser.add_argument('-o', '--output', dest='output', help="Output of computed action communities", required=True)

    # default help if nothing
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    input_pkl = args.input
    output_file = args.output

    # define the profile to select
    # 0 = no path evaluation, no prepend
    # 1 = path evaluation, no prpepend
    if args.anypath:
        # anypath
        chosen_profile = 0
    else:
        # uphill
        chosen_profile = 1

    # increase 2 to change the profile
    # 2 = no path evaluation, prepend
    # 3 = path evaluation, prepend
    if args.prepend:
        chosen_profile += 2

    # selected options or default instead
    vp_number = 1
    if args.vantage_point:
        vp_number = args.vantage_point

    percent_of_vantage_points = 0.5
    if args.percent_of_vantage_points:
        percent_of_vantage_points = percent_of_vantage_points

    vp_paths = 1
    if args.vantage_point_paths:
        vp_paths = args.vantage_point_paths

    # adjust to help simplify Snakemake
    no_fraction = False
    if args.no_fraction or args.fraction == 'n':
        no_fraction = True

    fraction = 0.0
    if args.fraction and args.fraction != 'n':
        fraction = float(args.fraction)

    # load the pickle structure
    with open(input_pkl, "rb") as file_to_process:
        communities = pickle.load(file_to_process)

    # possible action communities
    action_communties_dict = {}

    inferred_communities_set = set()
    for comm in communities:
        as_comm, comm_comm = comm.split(':')

        # remove private AS communities
        if int(as_comm) not in range(64496, 65536) and \
                int(as_comm) not in range(4200000000, 4294967295) and \
                int(as_comm) not in [0, 23456]:

            # start evaluating the number of VPs and fraction of existence of the ASN in the AS-path
            number_of_valid_vps = 0

            paths_without_the_asn = 0
            paths_with_the_asn = 0
            for vp in communities[comm]:
                # check if the number of 1a and 1b for the VP is bigger than the number of announcements through the VP

                # check if we want to observe only the 1a situation with customer cone
                if args.upcount:
                    paths_without_the_asn += communities[comm][vp][chosen_profile][0]

                    paths_with_the_asn += communities[comm][vp][chosen_profile][2] + \
                                          communities[comm][vp][chosen_profile][3]
                else:
                    paths_without_the_asn += communities[comm][vp][chosen_profile][0] + \
                                             communities[comm][vp][chosen_profile][1]

                    paths_with_the_asn += communities[comm][vp][chosen_profile][2] + \
                                          communities[comm][vp][chosen_profile][3]

                if paths_without_the_asn >= vp_paths:
                    number_of_valid_vps += 1

            if number_of_valid_vps >= vp_number:
                if not no_fraction:
                    # add the fraction check too
                    if paths_with_the_asn + paths_without_the_asn > 0:
                        if (paths_with_the_asn / (paths_with_the_asn + paths_without_the_asn)) <= fraction:
                            # check for the percentage of the valid VPs
                            if (number_of_valid_vps / len(communities[comm])) >= percent_of_vantage_points:
                                inferred_communities_set.add(comm)
                else:
                    # check for the percentage of the valid VPs
                    if (number_of_valid_vps / len(communities[comm])) >= percent_of_vantage_points:
                        inferred_communities_set.add(comm)

    # save the inferred communities
    arq = open(f"{args.output}", "wt")
    for community in inferred_communities_set:
        arq.write("{}\n".format(community))
    arq.close()
