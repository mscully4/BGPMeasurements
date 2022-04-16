#!/usr/bin/env python3

import os
import sys
import traceback
import json
import pickle
import matplotlib.pyplot
from pathlib import Path
from termcolor import colored

err_pyplot_calls = False
err_bullet = colored("  >>>", "red")
inf_bullet = colored("  >>>", "green")

stdout_orig = sys.stdout
stderr_orig = sys.stdout


def shadow_pyplot(*arg):
    global err_pyplot_calls
    err_pyplot_calls = True


# pickle files are a standard way of serializing data in Python
# https://docs.python.org/3/library/pickle.html
def load_p(task):
    try:
        with open(Path(f"solution/{task}.p"), "rb") as f:
            return pickle.load(f)
    except Exception as e:
        msg = f"{err_bullet} {task} (pickle): {repr(e)}\n"
        print(msg, file=stderr_orig)


# pickle files are a standard way of serializing data in Python
# https://docs.python.org/3/library/pickle.html
def write_p(data, task):
    try:
        with open(Path(f"{task}.p"), "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        msg = f"{err_bullet} {task} (pickle): {repr(e)}\n"
        print(msg, file=stderr_orig)

# Python also allow serialization of data to JSON, but you're not guaranteed to be able to capture all Python type
# https://docs.python.org/3/library/pickle.html#comparison-with-json
def write_j(data, task):
    try:
        with open(Path(f"{task}.json"), "w") as f:
            json.dump(data, f)
            f.write("\n")
    except Exception as e:
        msg = f"{err_bullet} {task} (json): {repr(e)}\n"
        print(msg, file=stderr_orig)


if __name__ == "__main__":
    BASE_DIR = Path(os.path.abspath(__file__)).parent
    # if BASE_DIR != Path(os.getcwd()):
    #     # print(f"{BASE_DIR} != {os.getcwd()} - changing")
    #     os.chdir(BASE_DIR)

    #
    # There should be no plotting code in bgpm.py!!!
    #
    # change pyplot to non-interactive mode
    matplotlib.pyplot.ioff()
    # catch calls to show(), matshow(), and savefig()
    matplotlib.pyplot.show = shadow_pyplot
    matplotlib.pyplot.matshow = shadow_pyplot
    matplotlib.pyplot.savefig = shadow_pyplot

    # set up cache file lists
    rib_files = sorted([str(p) for p in Path(BASE_DIR, "rib_files").glob("*.cache")])
    update_files = sorted([str(p) for p in Path(BASE_DIR, "update_files").glob("*.cache")])
    update_files_blackholing = sorted([str(p) for p in Path(BASE_DIR, "update_files_blackholing").glob("*.cache")])

    try:
        stdout_capture = Path("stdout.txt")
        sys.stdout = open(stdout_capture, "w")

        # import all the functions and exit with error if any fail
        msg = colored("Overall:", attrs=["bold"])
        print(msg, file=stderr_orig)
        try:
            from bgpm import calculateUniquePrefixes
            from bgpm import calculateUniqueAses
            from bgpm import examinePrefixes
            from bgpm import calculateShortestPath
            from bgpm import calculateRTBHDurations
            from bgpm import calculateAWDurations
            print(f"{inf_bullet} All functions imported\n", file=stderr_orig)
        except (ImportError, Exception) as e:
            print(f"{err_bullet} {repr(e)}", file=stderr_orig)

        tasks = [
            ("task_1a", calculateUniquePrefixes, rib_files),
            # ("task_1b", calculateUniqueAses, rib_files),
            # ("task_1c", examinePrefixes, rib_files),
            # ("task_2", calculateShortestPath, rib_files),
            # ("task_3", calculateRTBHDurations, update_files_blackholing),
            # ("task_4", calculateAWDurations, update_files),
        ]

        for task, func, arg in tasks:
            task_name = colored(task, attrs=["bold"])
            msg = f"{task_name}: {func.__name__}()"
            # msg = colored(f"{task}: {func.__name__}()", attrs=["bold"])
            print(msg, file=stderr_orig)
            try:
                res = func(arg)
                if not res:
                    # res is empty, so nothing need be cached to disk - student skipped this task
                    msg = f"{err_bullet} nothing returned for this task"
                    print(msg, file=stderr_orig)
                else:
                    # something was returned - check signature of result
                    if task in ["task_1a", "task_1b", "task_1c"]:
                        if type(res) is not list:
                            msg = f"{err_bullet} return type should be list (not {type(res)})"
                            print(msg, file=stderr_orig)
                        else:
                            msg = f"{inf_bullet} return type is correct ({type(res)})"
                            print(msg, file=stderr_orig)
                    
                    if task in ["task_2", "task_3", "task_4"]:
                        if type(res) is not dict:
                            msg = f"{err_bullet} return type should be dict (not {type(res)})"
                            print(msg, file=stderr_orig)
                        else:
                            msg = f"{inf_bullet} return type is correct ({type(res)})"
                            print(msg, file=stderr_orig)

                    # something was returned - compare and report
                    solution = load_p(task)
                    if solution != res:
                        msg = f"{err_bullet} returned value is incorrect (output from your code is contained in the file student_{task}.json)"
                        print(msg, file=stderr_orig)
                    else:
                        msg = f"{inf_bullet} returned value is correct"
                        print(msg, file=stderr_orig)

                    # if you really want to create a pickle file (https://docs.python.org/3/library/pickle.html), you can uncomment this
                    # write_p(res, task)
                    write_j(res, f"student_{task}")
                # print(f"{inf_bullet} {task}: completed", file=stderr_orig)
            except (ImportError, Exception) as e:
                msg = f"{err_bullet} {task}: {repr(e)}\n"
                print(msg, file=stderr_orig)
                traceback.print_exc(file=stderr_orig)
    except Exception as e:
        # something bad happened, so print it to real stderr
        print(repr(e), file=stderr_orig)
    finally:
        # clean up stdout
        sys.stdout.flush()
        sys.stdout = stdout_orig
        if stdout_capture.exists() and stdout_capture.stat().st_size == 0:
            stdout_capture.unlink()
        else:
            msg = f"{err_bullet} your solution should not print anything to the console"
            print(msg, file=stderr_orig)

        if err_pyplot_calls:
            msg = f"{err_bullet} your solution contains calls to pyplot, which will result in a deduction"
            print(msg, file=stderr_orig)
