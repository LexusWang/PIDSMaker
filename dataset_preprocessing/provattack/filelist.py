PROVATTACK = [
    "1.jsonl",
    "2.jsonl",
    "3.jsonl",
    "4.jsonl",
    "5.jsonl",
    "6.jsonl",
    "7.jsonl",
    "8.jsonl",
    "9.jsonl",
    "10.jsonl",
    "11.jsonl",
    "12.jsonl",
    "13.jsonl",
    "14.jsonl",
    "15.jsonl",
    "16.jsonl",
    "17.jsonl",
    "18.jsonl",
    "19.jsonl",
    "20.jsonl",
    "21.jsonl",
    "22.jsonl",
    "23.jsonl",
    "24.jsonl",
    "25.jsonl",
]

PROVATTACK1 = [
    "1.jsonl",
]

PROVATTACK2 = [
    "2.jsonl",
]

PROVATTACK3 = [
    "3.jsonl",
]

PROVATTACK4 = [
    "4.jsonl",
]

PROVATTACK5 = [
    "5.jsonl",
]

PROVATTACK6 = [
    "6.jsonl",
]

PROVATTACK7 = [
    "7.jsonl",
]

PROVATTACK8 = [
    "8.jsonl",
]

PROVATTACK9 = [
    "9.jsonl",
]

PROVATTACK10 = [
    "10.jsonl",
]

PROVATTACK11 = [
    "11.jsonl",
]

PROVATTACK12 = [
    "12.jsonl",
]

PROVATTACK13 = [
    "13.jsonl",
]

PROVATTACK14 = [
    "14.jsonl",
]

PROVATTACK15 = [
    "15.jsonl",
    "benign15.jsonl",
]

PROVATTACK16 = [
    "16.jsonl",
]

PROVATTACK17 = [
    "17.jsonl",
]

PROVATTACK18 = [
    "18.jsonl",
    "benign18.jsonl",
]

PROVATTACK19 = [
    "19.jsonl",
]

PROVATTACK20 = [
    "20.jsonl",
]

PROVATTACK21 = [
    "21.jsonl",
]

PROVATTACK22 = [
    "22.jsonl",
]

PROVATTACK23 = [
    "23.jsonl",
]

PROVATTACK24 = [
    "24.jsonl",
]

PROVATTACK25 = [
    "25.jsonl",
    "benign25.jsonl",
]

test123 = [
    "atk123.jsonl",
    "benign-1-5.jsonl",
    "benign_1_7.jsonl",
    "benign-1-8.jsonl",
    "benign-1-9.jsonl",
]

test100 = [
    "atk100.jsonl",
    "benign-1-5.jsonl",
    "benign_1_7.jsonl",
    "benign-1-8.jsonl",
    "benign-1-9.jsonl",
]

test105 = [
    "atk105.jsonl",
    "benign1-5.jsonl",
    "benign_1_7.jsonl",
    "benign-1-8.jsonl",
    "benign-1-9.jsonl",
]





d2test = [
    "d2test.jsonl",
]

training = [
    "benign_1_5.jsonl",
    "benign_1_8.jsonl",
    "benign_1_7.jsonl",
    "benign_1_9.jsonl",
]

aa23_341a=[
    "AA23_341A.jsonl",
    "benign_1_5.jsonl",
    "benign_1_8.jsonl",
]

aa24_046a=[
    "AA24_046A.jsonl",
]

alphvblackcat=[
    "ALPHVBlackcat.jsonl",
]
phobosransomware=[
    "PhobosRansomware.jsonl",
]

# Single unified database: full benign training set + ALL attack files
# Train once, test on each attack separately using different test_files in config
training_full = [
    "benign_1_5.jsonl",
    "benign_1_7.jsonl",
    "benign_1_8.jsonl",
    "benign_1_9.jsonl",
    "AA23_341A.jsonl",
    "AA24_046A.jsonl",
    "ALPHVBlackcat.jsonl",
    "PhobosRansomware.jsonl",
]

def get_filelist(dataset_name):
    if dataset_name == "PROVATTACK":
        return PROVATTACK
    elif dataset_name == "PROVATTACK1":
        return PROVATTACK1
    elif dataset_name == "PROVATTACK2":
        return PROVATTACK2
    elif dataset_name == "PROVATTACK3":
        return PROVATTACK3
    elif dataset_name == "PROVATTACK4":
        return PROVATTACK4
    elif dataset_name == "PROVATTACK5":
        return PROVATTACK5
    elif dataset_name == "PROVATTACK6":
        return PROVATTACK6
    elif dataset_name == "PROVATTACK7":
        return PROVATTACK7
    elif dataset_name == "PROVATTACK8":
        return PROVATTACK8
    elif dataset_name == "PROVATTACK9":
        return PROVATTACK9
    elif dataset_name == "PROVATTACK10":
        return PROVATTACK10
    elif dataset_name == "PROVATTACK11":
        return PROVATTACK11
    elif dataset_name == "PROVATTACK12":
        return PROVATTACK12
    elif dataset_name == "PROVATTACK13":
        return PROVATTACK13
    elif dataset_name == "PROVATTACK14":
        return PROVATTACK14
    elif dataset_name == "PROVATTACK15":
        return PROVATTACK15
    elif dataset_name == "PROVATTACK16":
        return PROVATTACK16
    elif dataset_name == "PROVATTACK17":
        return PROVATTACK17
    elif dataset_name == "PROVATTACK18":
        return PROVATTACK18
    elif dataset_name == "PROVATTACK19":
        return PROVATTACK19
    elif dataset_name == "PROVATTACK20":
        return PROVATTACK20
    elif dataset_name == "PROVATTACK21":
        return PROVATTACK21
    elif dataset_name == "PROVATTACK22":
        return PROVATTACK22
    elif dataset_name == "PROVATTACK23":
        return PROVATTACK23
    elif dataset_name == "PROVATTACK24":
        return PROVATTACK24
    elif dataset_name == "PROVATTACK25":
        return PROVATTACK25
    elif dataset_name == "test123":
        return test123
    elif dataset_name == "test100":
        return test100
    elif dataset_name == "test105":
        return test105
    elif dataset_name == "aa23":
        return aa23
    elif dataset_name == "d2test":
        return d2test
    elif dataset_name == "aa23_341a":
        return aa23_341a
    elif dataset_name == "aa24_046a":
        return aa24_046a
    elif dataset_name == "alphvblackcat":
        return alphvblackcat
    elif dataset_name == "phobosransomware":
        return phobosransomware
    elif dataset_name == "training":
        return training
    elif dataset_name == "training_full":
        return training_full