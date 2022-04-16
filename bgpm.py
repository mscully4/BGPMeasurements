#!/usr/bin/env python3

import pybgpstream

"""Code file for CS 6250 BGPM Project

Edit this file according to the provided docstrings and assignment description. 
Do not change the existing function name or arguments.
You may add additional functions but they need to be contained entirely in this file.
"""

def calculateUniquePrefixes(cache_files):
    """Retrieve the number of unique IP prefixes from input BGP data files.

    Args:
        cache_files: A list of files.

    Returns:
        A list containing the number of unique IP prefixes for each input file.
        For example: [2, 5]
    """
    result = []
    for f in sorted(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", f)
        stream.add_filter("ipversion", "4")
        
        unique_prefixes = set()
        for el in stream:
            prefix = el.fields['prefix']
            unique_prefixes.add(prefix)
        result.append(len(unique_prefixes))
    return result


def calculateUniqueAses(cache_files):
    """Retrieve the number of unique ASes from input BGP data files.

    Args:
        cache_files: A list of files.

    Returns:
        A list containing the number of the number of unique AS for each input file.
        For example: [2, 5]
    """
    result = []
    for f in sorted(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", f)
        stream.add_filter("ipversion", "4")
        
        unique_ases = set()
        for el in stream:
            if el.fields['as-path'] == "": continue

            ases = el.fields["as-path"].split(" ")
            unique_ases.update(ases)
        result.append(len(unique_ases))
    return result


def examinePrefixes(cache_files):
    """A list of the top 10 origin ASes according to percentage increase of the advertised prefixes.

    Args:
        cache_files: A list of files.

    Returns:
        A list of the top 10 origin ASes according to percentage increase of the advertised prefixes from lowest to highest.
        For example: ["777", "1", "6"]
        corresponds to AS "777" as having the smallest percentage increase (of the top ten) and AS "6" having the highest increase (of the top ten).
        AS numbers should be strings.
    """
    results = []
    data = {}
    for f in sorted(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", f)
        stream.add_filter("ipversion", "4")

        counts = {}
        for el in stream:
            prefix = el.fields['prefix']
            if el.fields['as-path'] == "": continue

            origin = el.fields["as-path"].split(" ").pop()
            tmp = counts.get(origin, set())
            tmp.add(prefix)
            counts[origin] = tmp
        
        for key in counts:
            if key in data:
                data[key][1] = len(counts[key])
            else:
                data[key] = [len(counts[key]), 0]

    for key in data:
        if data[key][1] == 0: continue
        perc_diff = (float(data[key][1]) / float(data[key][0])) - 1
        results.append([key, perc_diff])

    results.sort(key=lambda r: -r[1])
    return [r[0] for r in results[:10]]


def calculateShortestPath(cache_files):
    """Compute the shortest AS path length for every origin AS from input BGP data files.

    Retrieves the shortest AS path length for every origin AS for every input file.
    Your code should return a dictionary where every key is the AS string and every value associated with the key is
    a list of the shortest path lengths for that AS.

    Note: For any AS that is not present in every input file, fill the corresponding entry in its list with a zero.
    Every value in the dictionary should have the same length.

    Args:
        cache_files: A list of files.

    Returns:
        A dictionary where every key is the AS and every value associated with the key is a list of the shortest path
        lengths for that AS, for every input file.
        For example: {"455": [4, 2, 3], "533": [4, 1, 2]}
        corresponds to the AS "455" with the shortest path lengths 4, 2 and 3 and the AS "533" with the shortest paths 4, 1 and 2.
        AS numbers should be strings.
    """
    results = {}
    for i, f in enumerate(sorted(cache_files)):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "rib-file", f)
        stream.add_filter("ipversion", "4")
       
        tmp = {}
        for el in stream:
            prefix = el.fields['prefix']
            if el.fields['as-path'] == "": continue
            
            ases = el.fields["as-path"].split(" ")
            origin = ases[-1]
            
            unique_ases = set(ases)
            if len(unique_ases) == 1:
                continue

            if len(unique_ases) < tmp.get(origin, float('inf')):
                tmp[origin] = len(unique_ases)
        
        for key in tmp:
            if key not in results:
                results[key] = [0 for _ in range(len(cache_files))]
            results[key][i] = tmp[key]

    return results

from collections import defaultdict
def calculateRTBHDurations(cache_files):
    """Identify blackholing events and compute the duration of all RTBH events from input BGP data files.

    Identify events where the IPV4 prefixes are tagged with at least one Remote Triggered Blackholing (RTBH) community.

    Args:
        cache_files: A list of files.

    Returns:
        A dictionary where each key is a peerIP and each value is another dictionary with key equal to a prefix and each
        value equal to a list of explicit RTBH event durations.
        For example: {"127.0.0.1": {"12.13.14.0/24": [4.0, 1.0, 3.0]}}
        corresponds to the peerIP "127.0.0.1", the prefix "12.13.14.0/24" and event durations of 4.0, 1.0 and 3.0.
        AS numbers should be strings.
    """
    #result = defaultdict(lambda: defaultdict(list))
    result = {}

    # Credit to https://stackoverflow.com/questions/5369723/multi-level-defaultdict-with-variable-depth
    nested_dict = lambda: defaultdict(nested_dict)
    data = nested_dict()
    

    for f in sorted(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "upd-file", f)
        stream.add_filter("ipversion", "4")

        for record in stream.records():
            for el in record:
                addr = el.peer_address
                prefix = el.fields["prefix"]
               
                if el.type == "A":
                    comms = el.fields["communities"]
                    if "666" in " ".join(comms):
                        data[addr][prefix]["start"] = el.time
                    elif prefix in data[addr]:
                        del data[addr][prefix]

                if el.type == "W" and prefix in data[addr]:
                    time_diff = el.time - data[addr][prefix]["start"]
                    if time_diff > 0:
                        tmp = result.get(addr, {})
                        tmp[prefix] = tmp.get(prefix, []) + [time_diff]
                        result[addr] = tmp

    return result


def calculateAWDurations(cache_files):
    """Identify Announcement and Withdrawal events and compute the duration of all explicit AW events in the input data.

    Args:
        cache_files: A list of files.

    Returns:
        A dictionary where each key is a peerIP and each value is another dictionary with key equal to a prefix and each
        value equal to a list of explicit AW event durations.
        For example: {"127.0.0.1": {"12.13.14.0/24": [4.0, 1.0, 3.0]}}
        corresponds to the peerIP "127.0.0.1", the prefix "12.13.14.0/24" and event durations of 4.0, 1.0 and 3.0.
        AS numbers should be strings.
    """
    result = {}
    
    # Credit to https://stackoverflow.com/questions/5369723/multi-level-defaultdict-with-variable-depth
    nested_dict = lambda: defaultdict(nested_dict)
    data = nested_dict()
    
    for f in sorted(cache_files):
        stream = pybgpstream.BGPStream(data_interface="singlefile")
        stream.set_data_interface_option("singlefile", "upd-file", f)
        stream.add_filter("ipversion", "4")

        for record in stream.records():
            for el in record:
                addr = el.peer_address
                prefix = el.fields["prefix"]

                if el.type == "A":
                    data[addr][prefix] = el.time

                if el.type == "W" and prefix in data[addr]:
                    time_diff = el.time - data[addr][prefix]
                    if time_diff > 0:
                        tmp = result.get(addr, {})
                        tmp[prefix] = tmp.get(prefix, []) + [time_diff]
                        result[addr] = tmp

                    del data[addr][prefix]
    
    return result

# The main function will not be run during grading.
# You may use it however you like during testing.
#
# NB: make sure that check_solution.py runs your
#     solution without errors prior to submission
if __name__ == '__main__':
    from pathlib import Path
    import os
    BASE_DIR = Path(os.path.abspath(__file__)).parent
    rib_files = sorted([str(p) for p in Path(BASE_DIR, "rib_files").glob("*.cache")])
    calculateUniquePrefixes(rib_files)
    calculateUniqueAses(rib_files)
    examinePrefixes(rib_files)
    calculateShortestPath(rib_files)
    
    update_files_blackholing = sorted([str(p) for p in Path(BASE_DIR, "update_files_blackholing").glob("*.cache")])
    calculateRTBHDurations(update_files_blackholing)
        
    update_files = sorted([str(p) for p in Path(BASE_DIR, "update_files").glob("*.cache")])
    calculateAWDurations(update_files)
