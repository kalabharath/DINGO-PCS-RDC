import collections
import glob
import os

import io_util as io


def deprecated(func):
    import warnings
    import functools
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func

def enum(*sequential, **named):
    """

    :param sequential:
    :param named:
    :return:
    """
    # fake an enumerated type in Python

    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def checkFile(i):
    regex = str(i) + "_*.gzip"
    file_list = glob.glob(regex)
    if len(file_list) > 0:
        return True
    else:
        return False


def getNextSmotif(map_route):
    # [[6, 7, 'start'], [5, 6, 'left'], [4, 5, 'left'], [3, 4, 'left'], [2, 3, 'left'], [1, 2, 'left'], [0, 1, 'left']
    for i in range(0, len(map_route)):
        if not checkFile(i):
            return i, map_route[i]


def scoreCombination(score_list):
    """

    :param score_list:
    :return:
    """

    import itertools
    min_score = 999
    combi_list = list(itertools.combinations(score_list, 2))

    for combi in combi_list:
        c1 = combi[0]
        c2 = combi[1]
        if c1 and c2:
            if c1 + c2 < min_score:
                min_score = c1 + c2
    return min_score


def scoreCombination4t(score_list):
    """

    :param score_list:
    :return:
    """

    import itertools
    min_score = 999
    combi_list = list(itertools.combinations(score_list, 3))

    for combi in combi_list:
        c1 = combi[0]
        c2 = combi[1]
        c3 = combi[2]
        if c1 and c2 and c3:
            if c1 + c2 + c3 < min_score:
                min_score = c1 + c2 + c3
    return min_score


def getNchiSum(pcs_filter, stage):
    """

    :param pcs_filter:
    :return:
    """
    snchi = 999.999
    tensors = pcs_filter[1]

    if len(tensors) == 1:
        # Discourage single tag scoring by returning high score
        return 999.999  # discourage double tag score only for 4 tags

    if len(tensors) == 2 and stage == 2:  # stage 2
        snchi = 0
        for tensor in tensors:
            nchi = tensor[1]
            snchi += nchi
            # return 999.999 #discourage double tag score only for 4 tags

    if len(tensors) == 3 and stage <= 3:  # stage 2 & 3
        # Scoring three tags, get lowest Nchi for 2
        score_list = []
        for tensor in tensors:
            score_list.append(tensor[1])
        snchi = scoreCombination(score_list)

    if len(tensors) >= 4 and stage <= 3:  # stage 2,3 & 4
        # For 4 tags, get lowest Nchi for 3
        score_list = []
        for tensor in tensors:
            score_list.append(tensor[1])
        snchi = scoreCombination4t(score_list)
        snchi /= 100.0  # artificially increase the priority

    if len(tensors) >= 4 and stage == 4:  # stage 4
        # For 4 tags, get lowest Nchi for 3
        score_list = []
        for tensor in tensors:
            score_list.append(tensor[1])
        snchi = scoreCombination4t(score_list)

    if len(tensors) ==3 and  stage == 99:
        score_list = []
        for tensor in tensors:
            score_list.append(tensor[1])
        snchi = score_list[0] + score_list[1] + score_list[2]

    if stage == 999:
        if len(tensors) < 4:
            snchi = 999.999
        else:
            score_list = []
            for tensor in tensors:
                score_list.append(tensor[1])
            snchi = score_list[0] + score_list[1] + score_list[2]+ score_list[3]

    return snchi

def rdcSumChi(rdc_data, stage):
    snchi = 999.999
    tensors = rdc_data[1]
    if len(tensors) == 1:
        for tensor in tensors:
            return tensor[0]

    if len(tensors) == 2 and stage == 2:
        snchi = 0
        for tensor in tensors:
            nchi = tensor[0]
            snchi += nchi
    if len(tensors) == 2:
        snchi = 0
        for tensor in tensors:
            nchi = tensor[0]
            snchi += nchi

    return snchi

def start_top_hits(num_hits, stage):
    """
    generate run seq, a seq list of pairs of
    indexes of profiles for job scheduling
    """
    map_route = []
    ss_profiles = io.readPickle("ss_profiles.pickle")
    if os.path.isfile("contacts_route.pickle"):
        map_route = io.readPickle("contacts_route.pickle")
    elif os.path.isfile("pcs_route.pickle"):
        map_route = io.readPickle("pcs_route.pickle")
    elif os.path.isfile("rdc_route.pickle"):
        map_route = io.readPickle("rdc_route.pickle")

    try:
        next_index, next_smotif = getNextSmotif(map_route)
        print next_index, next_smotif
    except TypeError:
        return [999], 999

    direction = next_smotif[-1]
    if direction == 'left':
        next_ss_list = ss_profiles[next_smotif[0]]
    else:
        next_ss_list = ss_profiles[next_smotif[1]]
    # get and make a list of top 10(n) of the previous run

    # top_hit_file = str((next_index) - 1) + "_tophits.pickle"
    top_hit_file = str((next_index) - 1) + "_tophits.gzip"

    top_hits = []
    if os.path.isfile(top_hit_file):
        top_hits = io.readGzipPickle(top_hit_file)
        print "loading from prevously assembled tophits.pickle file"
        print "# hits :", len(top_hits)
    else:
        print "No previous tophits file found, Generating a new one"
        return "exception"

    # delete two stages down pickled files
    # check_pickle = str(next_index - 2) + str("_*_*.pickle")
    check_pickle = str(next_index - 2) + str("_*_*.gzip")
    file_list = glob.glob(check_pickle)

    if len(file_list) > 10:
        remove = "rm "+check_pickle
        os.system(remove)

    if top_hits:
        run_seq = []
        for i in range(len(top_hits)):
            for j in range(len(next_ss_list)):
                run_seq.append([i, j])
        return run_seq, next_index
    else:
        return False, False

def getPreviousSmotif(index):
    map_route = []
    if os.path.isfile("contacts_route.pickle"):
        map_route = io.readPickle("contacts_route.pickle")
    elif os.path.isfile("pcs_route.pickle"):
        map_route = io.readPickle("pcs_route.pickle")
    elif os.path.isfile("rdc_route.pickle"):
        map_route = io.readPickle("rdc_route.pickle")

    next_index, next_smotif = getNextSmotif(map_route)
    # top_hits = io.readPickle(str(next_index - 1) + "_tophits.pickle")  # Read in previous index hits
    top_hits = io.readGzipPickle(str(next_index - 1) + "_tophits.gzip")  # Read in previous index hits
    
    # print len(top_hits)
    return top_hits[index]


def getSS2(index):
    map_route = []
    if os.path.isfile("contacts_route.pickle"):
        map_route = io.readPickle("contacts_route.pickle")
    elif os.path.isfile("pcs_route.pickle"):
        map_route = io.readPickle("pcs_route.pickle")
    elif os.path.isfile("rdc_route.pickle"):
        map_route = io.readPickle("rdc_route.pickle")

    ss_profiles = io.readPickle("ss_profiles.pickle")
    
    next_index, next_smotif = getNextSmotif(map_route)
    direction = next_smotif[-1]

    if direction == 'left':
        next_ss_list = ss_profiles[next_smotif[0]]
    else:
        next_ss_list = ss_profiles[next_smotif[1]]

    return next_ss_list[index], direction


def rename_pickle(index):
    import glob, os

    # file_list = glob.glob("tx_*.pickle")
    file_list = glob.glob("tx_*.gzip")
    for file in file_list:
        mv_cmd = "mv " + file + " " + str(index) + file[2:]
        os.system(mv_cmd)
    return True