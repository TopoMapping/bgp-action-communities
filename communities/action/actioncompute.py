import pickle
import argparse
from collections import Counter
from utils import canonical_aspath, has_loop, has_as_set, \
    customer_cone_caida, as_path_category, classify_relation, build_relation

# AS relations based on CAIDA
# Global variables
as_relation = {}  # have the relations between two ASes (asn1, asn2)
ases_set = set()
compute_community_dict = {}
squatter_relations = {}


def squatter_relationship(file_line):
    # relations for O(constant)
    asn_list = file_line.split(' ')[0]
    first_asn = asn_list.split(',')[0]
    squatter_relations[first_asn] = first_asn
    for asn in asn_list.split(',')[1:]:
        squatter_relations[asn] = first_asn


def process_annoucement(eval_type, as_path, comm_list):
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

    # if the type is set to 2 or 3, enable prepend relaxation
    if eval_type in (2, 3):
        prepend_relaxation = True
    else:
        prepend_relaxation = False

    # Remove prepends from the AS path
    # the best option is to check after the if's, but we need to track the ASN occurrence without repetitions
    local_as_path = canonical_aspath(as_path)

    # To classify relation we need, at least, 2 ASes
    canonical_path_len = len(local_as_path)
    if canonical_path_len == 1:
        return

    # change the ASes for its siblings in the AS-path
    original_local_as_path = local_as_path
    if squatter_file:
        for asn in local_as_path:
            if asn in squatter_relations:
                local_as_path[local_as_path.index(asn)] = squatter_relations[asn]

    # check if the evaluation is for path type configured
    if eval_type in (1, 3):
        for community in local_comm_list:
            community = community.strip()
            if len(community.split(':')) == 2:  # only 32 bits communities
                asn, comm = community.split(':')

                as_path_map = as_path_category(as_path, as_relation)
                vantage_point = local_as_path[0]  # the ASN connected to the collector

                # grant that all entries exist before accounting
                if community in compute_community_dict:
                    if vantage_point not in compute_community_dict[community]:
                        compute_community_dict[community][vantage_point] = {}
                        for entry_types in range(4):
                            compute_community_dict[community][vantage_point][entry_types] = [0, 0, 0, 0]
                else:
                    compute_community_dict[community] = {}
                    compute_community_dict[community][vantage_point] = {}
                    for entry_types in range(4):
                        compute_community_dict[community][vantage_point][entry_types] = [0, 0, 0, 0]

                # check the squatter relation
                squatter_asn = asn
                if squatter_file:
                    if asn in squatter_relations:
                        squatter_asn = squatter_relations[asn]

                # check if it is prepended
                prepend = False
                if prepend_relaxation:
                    if squatter_asn in local_as_path:
                        count_local_as_path = Counter(as_path.split(' '))
                        if count_local_as_path[asn] > 1:
                            prepend = True

                # check the rules and update accounting
                if (squatter_asn not in local_as_path) or prepend:
                    # case 1a
                    # compute UP or
                    # up, plateau_up
                    if classify_relation(as_path_map) in (0, 1):
                        # check if the target AS is in the customer cone of some AS of the AS-path before the VP

                        in_cone = False
                        if squatter_file:
                            # evaluate the original ASes, not the squatters, this changes de customer cone
                            for local_asn in original_local_as_path[1:]:
                                if local_asn in customer_cone:
                                    if asn in customer_cone[local_asn]:
                                        in_cone = True
                            if in_cone:
                                # case 1b
                                # print(f"1b: {as_path}")
                                compute_community_dict[community][vantage_point][eval_type][1] += 1
                            else:
                                # this is the case 1a, not in customer cone of any AS before the VP
                                # print(f"1a: {as_path}")
                                compute_community_dict[community][vantage_point][eval_type][0] += 1

                        else:
                            for local_asn in local_as_path[1:]:
                                if local_asn in customer_cone:
                                    if asn in customer_cone[local_asn]:
                                        in_cone = True
                            if in_cone:
                                # case 1b
                                # print(f"1b: {as_path}")
                                compute_community_dict[community][vantage_point][eval_type][1] += 1
                            else:
                                # this is the case 1a, not in customer cone of any AS before the VP
                                # print(f"1a: {as_path}")
                                compute_community_dict[community][vantage_point][eval_type][0] += 1
                    #else:
                        # case 1b
                        # print(f"1b: {as_path}")
                    #    compute_community_dict[community][vantage_point][eval_type][1] += 1

                elif asn == local_as_path[0]:
                    # case 2
                    # print(f"2: {as_path}")
                    compute_community_dict[community][vantage_point][eval_type][2] += 1
                else:
                    # case 3
                    # print(f"3: {as_path}")
                    compute_community_dict[community][vantage_point][eval_type][3] += 1
    else:
        # type evaluation: 0, 2, that means: do not consider the path to evaluate
        for community in local_comm_list:
            community = community.strip()
            if len(community.split(':')) == 2:  # only 32 bits communities
                asn, comm = community.split(':')
                vantage_point = local_as_path[0]  # the ASN connected to the collector

                # grant that all entries exist before accounting
                if community in compute_community_dict:
                    if vantage_point not in compute_community_dict[community]:
                        compute_community_dict[community][vantage_point] = {}
                        for entry_types in range(4):
                            compute_community_dict[community][vantage_point][entry_types] = [0, 0, 0, 0]
                else:
                    compute_community_dict[community] = {}
                    compute_community_dict[community][vantage_point] = {}
                    for entry_types in range(4):
                        compute_community_dict[community][vantage_point][entry_types] = [0, 0, 0, 0]

                # check the squatter relation
                squatter_asn = asn
                if squatter_file:
                    if asn in squatter_relations:
                        squatter_asn = squatter_relations[asn]

                # check if it is prepended
                prepend = False
                if prepend_relaxation:
                    if squatter_asn in local_as_path:
                        count_local_as_path = Counter(as_path.split(' '))
                        if count_local_as_path[asn] > 1:
                            prepend = True

                # check the rules and update accounting
                if (squatter_asn not in local_as_path) or prepend:
                    # check if the target AS is in the customer cone of some AS of the AS-path before the VP
                    in_cone = False
                    if squatter_file:
                        # evaluate the original ASes, not the squatters, this changes de customer cone
                        for local_asn in original_local_as_path[1:]:
                            if local_asn in customer_cone:
                                if asn in customer_cone[local_asn]:
                                    in_cone = True
                        if in_cone:
                            # case 1b
                            # print(f"1b: {as_path}")
                            compute_community_dict[community][vantage_point][eval_type][1] += 1
                        else:
                            # this is the case 1a, not in customer cone of any AS before the VP
                            # print(f"1a: {as_path}")
                            compute_community_dict[community][vantage_point][eval_type][0] += 1

                    else:
                        for local_asn in local_as_path[1:]:
                            if local_asn in customer_cone:
                                if asn in customer_cone[local_asn]:
                                    in_cone = True
                        if in_cone:
                            # case 1b
                            # print(f"1b: {as_path}")
                            compute_community_dict[community][vantage_point][eval_type][1] += 1
                        else:
                            # this is the case 1a, not in customer cone of any AS before the VP
                            # print(f"1a: {as_path}")
                            compute_community_dict[community][vantage_point][eval_type][0] += 1

                elif asn == local_as_path[0]:
                    # case 2
                    # print(f"2: {as_path}")
                    compute_community_dict[community][vantage_point][eval_type][2] += 1
                else:
                    # case 3
                    # print(f"3: {as_path}")
                    compute_community_dict[community][vantage_point][eval_type][3] += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help="RIB to be evaluated", required=True)
    parser.add_argument('-r', '--relation', dest='relation', help="AS relations (ex.: as-rel.txt).", required=True)
    parser.add_argument('-s', '--squatters', dest='squatters', help="Squatters file", required=True)
    parser.add_argument('-x', '--cone', dest='cone', help="CAIDA customers cone file", required=True)
    parser.add_argument('-o', '--output', dest='output', help="Output the evaluation", required=True)

    args = parser.parse_args()
    input_rib = args.input
    output_pkl = args.output
    relation_txt = args.relation
    squatter_file = args.squatters

    # customer cone
    customer_cone = customer_cone_caida(args.cone)

    # build the partner relations from the relations inference
    if squatter_file:
        with open(squatter_file, "rt") as file_to_process:
            for line in file_to_process:
                squatter_relationship(line)

    # AS relationships
    # Build the relation structure
    with open(relation_txt, "rt") as file_to_process:
        for relation_line in file_to_process:
            if '#' in relation_line:
                continue
            else:
                temp_relation = build_relation(relation_line)

                for i in temp_relation.keys():  # add one or two relations based on ASN relationship
                    as_relation[i] = temp_relation[i]

    # read all the rib and change and extract the relations using the sibling pre-processed
    with open(input_rib, "rt") as file_to_process:
        for rib_line in file_to_process:
            rib_extraction = rib_line.split('|')

            # Split just prefixes that we are tracking
            as_path = rib_extraction[2]
            comm_list = rib_extraction[7]

            # no path evaluation, no prepend
            process_annoucement(0, as_path, comm_list)

            # path evaluation, no prepend
            process_annoucement(1, as_path, comm_list)

            # no path evaluation, prepend
            process_annoucement(2, as_path, comm_list)

            # path evaluation, prepend
            process_annoucement(3, as_path, comm_list)

    # save the output file
    arq = open(output_pkl, 'wb')
    pickle.dump(compute_community_dict, arq)
    arq.close()

