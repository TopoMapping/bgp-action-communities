import os

# Variables
BASE_DIR = "output/"

# Squatting variables
squatting_scope = [0.7]  # threshold
squatting_coverage = [0.9]  # relation
squatting_consistency = [0.3]  # boundary
squatting_visibility = [6]  # visibility
squatting_community_count = [2]  # visibility


fractions = [0.01]
vp_count = [3]
vp_announces_count = [4]

# path_condition options
# u - only from UP/UP-HILL
# a - all paths
path_condition = ['a']

# cone_condition options
# l - only if the AS is in the customer cone
# x - ignore the customer cone and process all
cone_condition = ['x']


# Extract data for evaluation
rule dump_all_communities:
    input:
        rib = BASE_DIR + "textrib/{rib}.rib"
    output:
        all_com = BASE_DIR + "allcom/{rib}-{action_filter}-allcom"
    shell:
        "python3 communities/tools/allcommunities.py -f {wildcards.action_filter} -i {input.rib} -o {output}"


rule merge_all_communities:
    input:
        ribs = expand(BASE_DIR + "allcom/{rib}-{action_filter}-allcom",
            rib=[input for input in os.listdir('collectors')],
            allow_missing=True
        )
    output:
        all_com = BASE_DIR + "allcom/aggregated-{action_filter}-allcom"
    shell:
        "cat {input.ribs} | sort | uniq > {output.all_com}"


### Prepare the RIBs for scanning and evaluation
# All desired files to be process need to be in the 'collector' directory
rule scan_collectors_rib:
    input:
        rib_input = "collectors/{rib}"
    output:
        rib_out = BASE_DIR + "textrib/{rib}.rib"
    shell:
        "bgpscanner -L {input.rib_input} > {output.rib_out}"


### Squatting Inference

# Squatting automatic inference
rule search_squatter_keys:
    input:
        rib_input = BASE_DIR + "textrib/{rib}.rib"
    output:
        search_key = BASE_DIR + "squatters/search_keys/{rib}.key"
    shell:
        "python3 communities/squatter/searchsquatters.py -i {input.rib_input} -o {output.search_key}"


rule map_squatter_keys:
    input:
        search_key = BASE_DIR + "squatters/search_keys/{rib}.key"
    output:
        mapped_pkl = BASE_DIR + "squatters/mapped_pkl/{rib}.pkl"
    shell:
        "python3 communities/squatter/mapsquatters.py -i {input.search_key} -o {output.mapped_pkl}"


rule map_simplify_keys:
    input:
        search_key = BASE_DIR + "squatters/search_keys/{rib}.key"
    output:
        mapped_spy = BASE_DIR + "squatters/search_keys/{rib}.spfy"
    shell:
        "python3 communities/squatter/mapsquatterssimplify.py -i {input.search_key} -o {output.mapped_spy}"


rule squatter_candidates:
    input:
        mapped_pkl = BASE_DIR + "squatters/mapped_pkl/{rib}.pkl",
        search_spfy_key = BASE_DIR + "squatters/search_keys/{rib}.spfy"
    output:
        squatters = BASE_DIR + "squatters/squatter_candidates/{rib}/{rib}-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    shell:
        "python3 communities/squatter/squattercandidates.py -m {input.search_spfy_key} "
        "-i {input.mapped_pkl} -o {output.squatters} -x data/ixps "
        "-t {wildcards.thr} -r {wildcards.rel} -b {wildcards.bd} -s {wildcards.static} -c {wildcards.comm}"


rule merge_squatter_candidates_across_collectors:
    input:
        multiple_siblings = expand(BASE_DIR + "squatters/squatter_candidates/{rib}/{rib}-t{thr}-r{rel}-b{bd}-s{static}-c{comm}",
            rib = [input for input in os.listdir("collectors")],
            thr=squatting_scope,
            rel=squatting_coverage,
            bd=squatting_consistency,
            static=squatting_visibility,
            comm=squatting_community_count
        )
    output:
        aggregated = BASE_DIR + "squatters/inferred_squatters/agg-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    shell:
        "python3 communities/squatter/join_squatter_candidates.py {input} {output}"



# Inferrence of Action Communities
# Action Communities Inference
rule inference_of_action_without_prepend:
    input:
        rib_file = BASE_DIR + "textrib/{rib}.rib",
        squatters = BASE_DIR + "squatters/inferred_squatters/agg-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    output:
        inferred_action = BASE_DIR + "actioninference/{rib}/{removal_thr}-{action_filter}/n/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    shell:
        "python3 communities/action/actioninference.py -i {input.rib_file} -s {input.squatters} "
        "-t {wildcards.removal_thr} -f {wildcards.action_filter} -o {output.inferred_action}"


# Action Communities Inference (no VP) prepend relaxed
rule inference_of_action_with_prepend:
    input:
        rib_file = BASE_DIR + "textrib/{rib}.rib",
        squatters = BASE_DIR + "squatters/inferred_squatters/agg-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    output:
        inferred_action = BASE_DIR + "actioninference/{rib}/{removal_thr}-{action_filter}/p/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    shell:
        "python3 communities/action/actioninference.py -i {input.rib_file} -s {input.squatters} -p "
        "-t {wildcards.removal_thr} -f {wildcards.action_filter} -o {output.inferred_action}"


# Merge Inference Across Collectors
rule merge_inferences_of_action_communities:
    input:
        inferred_te = expand(BASE_DIR + "actioninference/{rib}/{removal_thr}-{action_filter}/{prep}/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}",
            rib=[input for input in os.listdir('collectors')],
            allow_missing=True
        )
    output:
        joined_inferred_te = BASE_DIR + "actioninference/aggregated/{removal_thr}-{action_filter}/{prep}/agginf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    shell:
        "cat {input.inferred_te} | sort | uniq > {output.joined_inferred_te}"


# Compute all Strategies at Once
rule compute_action_communities:
    input:
        rib_file = BASE_DIR + "textrib/{rib}.rib",
        squatters = BASE_DIR + "squatters/inferred_squatters/agg-t{thr}-r{rel}-b{bd}-s{static}-c{comm}"
    output:
        vps = BASE_DIR + "actioncommunities/{rib}/computed/acom-t{thr}-r{rel}-b{bd}-s{static}-c{comm}.pkl"
    shell:
        "python3 communities/action/actioncompute.py -i {input.rib_file} -s {input.squatters} "
        "-x data/20231201.ppdc-ases.txt -r data/relations/20231201.as-rel.txt -o {output.vps}"


# Evaluate all Computed strategies at once
rule compute_action_communities_without_prepend:
    input:
        mix = BASE_DIR + "actioncommunities/{rib}/computed/acom-t{thr}-r{rel}-b{bd}-s{static}-c{comm}.pkl"
    output:
        inf = BASE_DIR + "actioncommunities/{rib}/inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "python3 communities/action/actioncomputeinference.py -i {input.mix} "
        " -o {output.inf} -{wildcards.pcon} -{wildcards.ccon} -v {wildcards.vpcon}"
        " -k {wildcards.vpacon} -f {wildcards.frac}"


rule compute_action_communities_with_prepend:
    input:
        mix = BASE_DIR + "actioncommunities/{rib}/computed/acom-t{thr}-r{rel}-b{bd}-s{static}-c{comm}.pkl"
    output:
        inf = BASE_DIR + "actioncommunities/{rib}/inferred-prep/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "python3 communities/action/actioncomputeinference.py -p -i {input.mix} "
        " -o {output.inf} -{wildcards.pcon} -{wildcards.ccon} -v {wildcards.vpcon}"
        " -k {wildcards.vpacon} -f {wildcards.frac}"


# Merged Inference Across Collectors
rule merge_across_collectors_inferred_action_communities_without_prepend:
    input:
        inferred_te = expand(BASE_DIR + "actioncommunities/{rib}/inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}",
            rib=[input for input in os.listdir('collectors')],
            allow_missing=True
        )
    output:
        joined_inferred = BASE_DIR + "actioncommunities/aggregated/inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "cat {input.inferred_te} | sort | uniq > {output.joined_inferred}"


# Merged Inference with Prepend Across Collectors
rule merge_across_collectors_inferred_action_communities_with_prepend:
    input:
        inferred_te = expand(BASE_DIR + "actioncommunities/{rib}/inferred-prep/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}",
            rib=[input for input in os.listdir('collectors')],
            allow_missing=True
        )
    output:
        joined_inferred = BASE_DIR + "actioncommunities/aggregated/inferred-prep/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "cat {input.inferred_te} | sort | uniq > {output.joined_inferred}"


# Compute the prefix tree for the inferred action communities
rule compute_prefix_tree_for_inferred_action_communities:
    input:
        inferred = BASE_DIR + "actioncommunities/aggregated/inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    output:
        dynamic_trie = BASE_DIR + "actioncommunities/aggregated/trie/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}.pkl"
    shell:
        "python3 communities/tools/triecategorize.py -i {input.inferred} -p -o {output.dynamic_trie}"


rule communities_inferred_by_the_prefix_tree:
    input:
        dynamic_trie = BASE_DIR + "actioncommunities/aggregated/trie/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}.pkl",
        all_com= BASE_DIR + "allcom/aggregated-{vpacon}-allcom"
    output:
        dynamic_trie_inf = BASE_DIR + "actioncommunities/aggregated/trie-inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "python3 communities/tools/trieevaluate.py -i {input.all_com} -p {input.dynamic_trie} -o {output.dynamic_trie_inf}"


# Inference with prepend using the prefix tree built from inference without prepend.
rule merge_all_inferred_communities:
    input:
        inferred = BASE_DIR + "actioncommunities/aggregated/inferred-prep/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}",
        dtrie_inf= BASE_DIR + "actioncommunities/aggregated/trie-inferred/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    output:
        joined = BASE_DIR + "inferred_action_communities/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}"
    shell:
        "cat {input.inferred} {input.dtrie_inf} | sort | uniq > {output.joined}"



# Process all steps for all collectors
rule bgpaction:
    input:
        expand(BASE_DIR + "inferred_action_communities/inf-t{thr}-r{rel}-b{bd}-s{static}-c{comm}-{pcon}-{ccon}-{frac}-{vpcon}-{vpacon}",
            thr=squatting_scope,
            rel=squatting_coverage,
            bd=squatting_consistency,
            static=squatting_visibility,
            comm=squatting_community_count,
            pcon=path_condition,
            ccon=cone_condition,
            frac=fractions,
            vpcon=vp_count,
            vpacon=vp_announces_count
        )


onsuccess:
    print("Workflow finished")

onerror:
    print("error")
