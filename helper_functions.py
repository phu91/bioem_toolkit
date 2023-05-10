#phu put the functions here. 
def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f"========== Function {func.__name__!r} executed in {(t2-t1):.4f}s")
        return result

    return wrap_func


def choosing_cluster(prechoice):
    if prechoice== 0:
        cluster_choice = input("Do you want to work on CLUSTER? Yes (1) or No (0): \n")
        if cluster_choice == "1":
            partition_choice = input("Please select your PARTITION on SLURM: \n")
            return partition_choice
        else:
            print("\n========== MULTIPLY_QUAT will be done on local machine")
            return None
    elif prechoice==1:
        partition_choice = input("Please select your PARTITION on SLURM: \n")
        return partition_choice


def counter(baseZero,count):
    return int(baseZero) + count

def clean_R1_Probability(working_dir, r1_output: str, bioEM_template,group_now):
    r1_read = open(r1_output, "r+")
    tmp_file = open("tmp_prob", "w+")
    lines = r1_read.readlines()
    for line in range(4, len(lines), 2):
        tmp_file.write(lines[line])
    tmp_file.close()
    r1_read.close()
    r1_result = pd.read_csv("tmp_prob", delim_whitespace="True", header=None,dtype=str)
    r1_result = r1_result.iloc[:, [1, 4, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]]
    label_list = [
        "particle",
        "MaxLogProb",
        "q1",
        "q2",
        "q3",
        "q4",
        "CTF_amp",
        "CTF_defocus",
        "CTF_B-Env",
