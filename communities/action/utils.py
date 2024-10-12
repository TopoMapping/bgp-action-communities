import re

# Define all categories
up, up_hill, up_down, up_hill_down, hill_down, down, valley, missing, unexpected, inviable = range(0, 10)

visual = ["UP", "PLATEAU-UP", "DOWN-UP", "DOWN-PLATEAU-UP", "DOWN-PLATEAU",
          "DOWN", "VALLEY", "MISSING", "UNEXPECTED", "INVIABLE"]


# Classify an AS_Path based on the relations of the ASes
def as_path_category(as_path, as_relation):
    """
    Generate a list of relations between ASes into an AS-path and return

    :param as_path: AS-path
    :return: a list of relations
    """
    canonical_path = canonical_aspath(as_path)
    as_path_map = []

    # Flow of relations
    # inverted the logic from collector to the origin
    down, up, hill = range(0, 3)

    if len(canonical_path) == 1:
        # impossible to evaluate an AS-path with only one element
        return

    # build the as_path_map based on the ASes relationship
    for i in range(len(canonical_path) - 1):
        first_as = canonical_path[i]
        second_as = canonical_path[i + 1]

        # Check if the relation exist:
        if (first_as, second_as) in as_relation:
            # three situations: p2c, c2p, p2p
            if as_relation[(first_as, second_as)] == -1:   # p2c
                as_path_map.append(up)
            elif as_relation[(first_as, second_as)] == 0:  # p2p
                as_path_map.append(hill)
            elif as_relation[(first_as, second_as)] == 1:  # c2p
                as_path_map.append(down)
        else:
            # what to do?
            as_path_map.append(":")

    return as_path_map


def classify_relation(as_path_map):
    """
    all the logic of up-plateau-down is related to the collector, not the origin.

    Return a classification of the AS-path using its relation list as:
    - UP
    - PLATEAU-UP
    - DOWN-UP
    - DOWN-PLATEAU-UP
    - DOWN-PLATEAU
    - DOWN
    - VALLEY
    - INVALID

    :param as_path_map:
    :return:
    """

    # Transform into a simplified string to apply regex for speed
    evaluate = ''.join(str(x) for x in as_path_map)

    # Match expressions
    up_expr = "^[1]+$"
    up_hill_expr = "^2[1]+$"
    up_down_expr = "^[0]+[1]+$"
    up_hill_down_expr = "^[0]+2[1]+$"
    hill_down_expr = "^[0]+2$"
    down_expr = "^[0]+$"

    # Search expression
    missing_expr = ":"
    valley_expr = "010|101"

    # Match expressions
    if re.match(up_expr, evaluate):
        return up

    if re.match(up_hill_expr, evaluate):
        return up_hill

    if re.match(up_down_expr, evaluate):
        return up_down

    if re.match(up_hill_down_expr, evaluate):
        return up_hill_down

    if re.match(hill_down_expr, evaluate):
        return hill_down

    if re.match(down_expr, evaluate):
        return down

    # Search expression
    if re.search(missing_expr, evaluate):
        if as_path_map[0] == 0:
            return up
        elif as_path_map[0] == 2:
            return hill_down
        elif as_path_map[0] == 1:
            return down
        else:
            return missing

    if re.search(valley_expr, evaluate):
        return valley

    # if nothing matches, then, the expression is invalid
    return unexpected


def levenshtein_distance(first_string, second_string):
    # source code adapted from: https://www.educative.io/answers/the-levenshtein-distance-algorithm
    # Declaring the strings 'a' and 'b':
    a = first_string
    b = second_string

    # Declaring array 'D' with rows = len(a) + 1 and columns = len(b) + 1:
    D = [[0 for i in range(len(b) + 1)] for j in range(len(a) + 1)]

    # Initialising first row:
    for i in range(len(a) + 1):
        D[i][0] = i

    # Initialising first column:
    for j in range(len(b) + 1):
        D[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                D[i][j] = D[i - 1][j - 1]
            else:
                # Adding 1 to account for the cost of operation:
                insertion = 1 + D[i][j - 1]
                replacement = 1 + D[i - 1][j - 1]
                deletion = 1 + D[i - 1][j]

                # Choosing the best option:
                D[i][j] = min(insertion, deletion, replacement)

    return D[len(a)][len(b)]


def has_loop(path):
    status = False

    local_path = path.split(' ')

    if len(local_path) < 3:
        return False

    for i in range(len(local_path) - 2):
        if local_path[i] in local_path[i + 2:]:
            if local_path[i] != local_path[i + 1]:
                status = True

    return status


def canonical_aspath(path):
    local_path = path.split(' ')
    canonical = []

    for asn in local_path:
        if asn not in canonical:
            canonical.append(asn)

    return canonical


def has_as_set(path):
    status = False

    if '{' in path:
        status = True

    return status


def build_relation(relation):
    asn_rel = {}
    asn1, asn2, value = relation.split('|')[:3]

    if value == '0':
        asn_rel[(asn1, asn2)] = 0
        asn_rel[(asn2, asn1)] = 0
    else:
        asn_rel[(asn1, asn2)] = -1
        asn_rel[(asn2, asn1)] = 1

    return asn_rel


def populate_ixp_from_peeringdb(file):
    """
    Populate the
    :param file: jsonl file from PeeringDB
    :return: populate the set
    """
    import json

    ixp_asn_set = set()
    with open(file, "r") as json_file:
        json_list = list(json_file)

    # iterate over JSONL entries
    for json_str in json_list[1:]:
        result = json.loads(json_str)
        ixp_asn_set.add(result['asn'])

    return ixp_asn_set


def customer_cone_caida(file):
    """
    Read CAIDA Customer Cone file
    :param file: filename
    :return: dict with all relations
    """

    customer_cone_dict = {}
    with open(file, "r") as filename:
        for line in filename:
            if '#' in line:
                continue
            splitted_line = line.split(' ')
            index = splitted_line[0].strip()
            customer_cone_dict[index] = set()

            for client_asn in splitted_line[1:]:
                    client_asn = client_asn.strip()
                    customer_cone_dict[index].add(client_asn)

    return customer_cone_dict


class TrieNode:
    def __init__(self, text=''):
        self.text = text
        self.mean = "inner"
        self.children = dict()
        self.is_word = False

    def __str__(self):
        if self.mean == "inner":
            return ""
        return f"{self.text} : {self.mean}"


class PrefixTree:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, mean):
        current = self.root
        for i, char in enumerate(word):
            if char not in current.children:
                prefix = word[0:i + 1]
                current.children[char] = TrieNode(prefix)
            current = current.children[char]
        current.is_word = True
        current.mean = mean

    def find(self, word):
        current = self.root
        for char in word:
            if char not in current.children:
                return current.mean
            current = current.children[char]
        return current.mean

