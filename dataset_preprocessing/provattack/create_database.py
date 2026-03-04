import hashlib
import re
import json
from psycopg2 import extras as ex
from tqdm import tqdm

from pidsmaker.config import get_runtime_required_args, get_yml_cfg
from pidsmaker.utils.dataset_utils import edge_reversed, exclude_edge_type, edge_with_d2
from pidsmaker.utils.utils import init_database_connection, log

from . import filelist

EVENT_TYPE_2_OPERATION = {
    "FileIoRead": "EVENT_READ",
    "FileIoWrite": "EVENT_WRITE",
    "FileIoRenamePath": "EVENT_RENAME",
    "ImageLoad": "EVENT_EXECUTE",
    "FileIoDelete": "EVENT_UNLINK",
    "ProcessStart": "EVENT_EXECUTE",
    "ProcessEnd": "EVENT_EXIT",
    "FileIoCreate": "EVENT_CREATE_OBJECT",
    "FileIoFileCreate": "EVENT_CREATE_OBJECT",
    "TcpIpConnectIPV4": "EVENT_CONNECT",
    "TcpIpAcceptIPV4": "EVENT_ACCEPT",
    "TcpIpDisconnectIPV4": "EVENT_CLOSE",
}

def stringtomd5(originstr):
    originstr = originstr.encode("utf-8")
    signaturemd5 = hashlib.sha256()  # TODO: check why we don't use hierarchical hashing here
    signaturemd5.update(originstr)
    return signaturemd5.hexdigest()


def store_netflow(file_path, cur, connect, index_id, filelist):
    # Parse data from logs
    netobjset = set()
    netobj2hash = {}
    successful_num = 0
    failed_num = 0
    for file in tqdm(filelist):
        with open(file_path + file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("logType") == "NODE" and data["logData"].get("type") == "OBJECT_NETFLOW":
                        nodeid = data["logData"]["id"]
                        srcaddr = data["logData"]["sip"]
                        srcport = str(data["logData"]["sport"])
                        dstaddr = data["logData"]["dip"]
                        dstport = str(data["logData"]["dport"])

                        nodeproperty = ",".join([srcaddr, srcport, dstaddr, dstport])
                        hashstr = stringtomd5(nodeid)

                        netobj2hash[nodeid] = [hashstr, nodeproperty]
                        netobj2hash[hashstr] = nodeid
                        netobjset.add(hashstr)
                        successful_num += 1
                except Exception as e:
                    failed_num += 1
                    continue

    # Store data into database
    datalist = []
    net_uuid2hash = {}
    for i in netobj2hash.keys():
        if len(i) != 64:
            # srcaddr, srcport, dstaddr, dstport = netobj2hash[i][1].split(",")
            # datalist.append([i, netobj2hash[i][0], srcaddr, srcport, dstaddr, dstport, index_id])
            datalist.append([i] + [netobj2hash[i][0]] + netobj2hash[i][1].split(",") + [index_id])
            net_uuid2hash[i] = netobj2hash[i][0]
            index_id += 1

    sql = """insert into netflow_node_table
                         values %s
            """
    ex.execute_values(cur, sql, datalist, page_size=10000)
    connect.commit()

    log(f"Netflow: successful_num = {successful_num}, failed_num = {failed_num}")

    return index_id, net_uuid2hash


def store_subject(file_path, cur, connect, index_id, filelist):
    # Parse data from logs
    success_count = 0
    fail_count = 0
    subject_obj2hash = {}
    for file in tqdm(filelist):
        with open(file_path + file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("logType") == "NODE" and data["logData"].get("type") == "SUBJECT_PROCESS":
                        nodeid = data["logData"]["id"]
                        cmdline = data["logData"].get("cmdLine", "null")
                        path = data["logData"].get("processName", "null")  # 或用 processName
                        subject_obj2hash[nodeid] = [path, cmdline]
                        success_count += 1
                except:
                    fail_count += 1
                    continue
    # Store into database
    datalist = []
    subject_uuid2hash = {}
    for i in subject_obj2hash.keys():
        if len(i) != 64:
            datalist.append(
                [i] + [stringtomd5(i)] + subject_obj2hash[i] + [index_id]
            )  # ([uuid, hashstr, path, cmdLine, index_id]) and hashstr=stringtomd5(uuid)
            subject_uuid2hash[i] = stringtomd5(i)
            index_id += 1

    sql = """insert into subject_node_table
                         values %s
            """
    ex.execute_values(cur, sql, datalist, page_size=10000)
    connect.commit()

    log(f"Subject: success_count = {success_count}, fail_count = {fail_count}")

    return index_id, subject_uuid2hash


def store_file(file_path, cur, connect, index_id, filelist):
    file_obj2hash = {}
    success_count = 0
    fail_count = 0
    for file in tqdm(filelist):
        with open(file_path + file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("logType") == "NODE" and data["logData"].get("type") == "OBJECT_FILE":
                        nodeid = data["logData"]["id"]
                        filepath = data["logData"].get("path", "null")
                        file_obj2hash[nodeid] = filepath
                        success_count += 1
                except:
                    fail_count += 1
                    continue

    datalist = []
    file_uuid2hash = {}
    for i in file_obj2hash.keys():
        if len(i) != 64:
            datalist.append([i] + [stringtomd5(i), file_obj2hash[i]] + [index_id])
            file_uuid2hash[i] = stringtomd5(i)
            index_id += 1

    sql = """insert into file_node_table
                         values %s
            """
    ex.execute_values(cur, sql, datalist, page_size=10000)
    connect.commit()

    log(f"File: success_count = {success_count}, fail_count = {fail_count}")

    return index_id, file_uuid2hash


def create_node_list(cur):
    nodeid2msg = {}

    # netflow
    sql = """
        select * from netflow_node_table;
        """
    cur.execute(sql)
    records = cur.fetchall()
    for i in records:
        nodeid2msg[i[1]] = i[-1]

    # subject
    sql = """
    select * from subject_node_table;
    """
    cur.execute(sql)
    records = cur.fetchall()
    for i in records:
        nodeid2msg[i[1]] = i[-1]

    # file
    sql = """
    select * from file_node_table;
    """
    cur.execute(sql)
    records = cur.fetchall()
    for i in records:
        nodeid2msg[i[1]] = i[-1]

    return nodeid2msg  # {hash_id:index_id}


def write_event_in_DB(cur, connect, datalist):
    sql = """insert into event_table
                         values %s
            """
    ex.execute_values(cur, sql, datalist, page_size=10000)
    connect.commit()

import json

def parse_event_from_log(
    line,
    reverse,
    subject_uuid2hash,
    file_uuid2hash,
    net_uuid2hash,
    nodeid2msg,
):

    try:
        record = json.loads(line)
    except Exception:
        return None

    if record.get("logType") != "EVENT":
        return None

    log = record.get("logData", {})
    if not log:
        return None

    operation = log.get("type")
    if operation is None:
        return None

    if operation in exclude_edge_type:
        return None

    subject_uuid = log.get("s")
    object_uuid = log.get("d")
    object2_uuid = log.get("d2")
    if subject_uuid is None or object_uuid is None:
        return None

    if subject_uuid not in subject_uuid2hash:
        return None

    def resolve_uuid_to_hash(uuid_):
        if uuid_ is None:
            return None
        if uuid_ in subject_uuid2hash:
            return subject_uuid2hash[uuid_]
        if uuid_ in file_uuid2hash:
            return file_uuid2hash[uuid_]
        if uuid_ in net_uuid2hash:
            return net_uuid2hash[uuid_]
        return None
    subject_id = subject_uuid2hash[subject_uuid]
    object_id = resolve_uuid_to_hash(object_uuid)
    # if object_uuid in subject_uuid2hash:
    #     object_id = subject_uuid2hash[object_uuid]
    # elif object_uuid in file_uuid2hash:
    #     object_id = file_uuid2hash[object_uuid]
    # elif object_uuid in net_uuid2hash:
    #     object_id = net_uuid2hash[object_uuid]
    # else:
    #     return None
    if object_id is None:
        return None

    timestamp = log.get("time")
    if timestamp is None:
        return None

    event_uuid = log.get("id")

    def make_row(src_id, dst_id):
        return [
            src_id,
            nodeid2msg[src_id],
            operation,
            dst_id,
            nodeid2msg[dst_id],
            event_uuid,
            int(timestamp),
        ]

    if operation in reverse:
        src_id, dst_id = object_id, subject_id
    else:
        src_id, dst_id = subject_id, object_id

    # Default: single edge <s, d, op>
    events = [make_row(subject_id, object_id)]
    # Special handling: rename with d2
    if operation in edge_with_d2:
        object2_id = resolve_uuid_to_hash(object2_uuid)
        if object2_id is not None:
            # <s, d2, op>
            events.append(make_row(subject_id, object2_id))
            # <d, d2, op>
            events.append(make_row(object_id, object2_id))

    return events

    # if operation not in edge_with_d2:
    #     return [
    #         src_id,
    #         nodeid2msg[src_id],
    #         operation,
    #         dst_id,
    #         nodeid2msg[dst_id],
    #         event_uuid,
    #         int(timestamp),
    #     ]
    # else:
    #     object2_uuid = log.get("d2")
    #     if object2_uuid in subject_uuid2hash:
    #         object2_id = subject_uuid2hash[object2_uuid]
    #     elif object2_uuid in file_uuid2hash:
    #         object2_id = file_uuid2hash[object2_uuid]
    #     elif object2_uuid in net_uuid2hash:
    #         object2_id = net_uuid2hash[object2_uuid]
    #     else:
    #         return [
    #         src_id,
    #         nodeid2msg[src_id],
    #         operation,
    #         dst_id,
    #         nodeid2msg[dst_id],
    #         event_uuid,
    #         int(timestamp),
    #         ]

    #     dst2_id = object2_id

    #     return [
    #         src_id,
    #         nodeid2msg[src_id],
    #         operation,
    #         dst_id,
    #         nodeid2msg[dst_id],
    #         dst2_id,
    #         nodeid2msg[dst2_id],
    #         event_uuid,
    #         int(timestamp),
    #     ]


def store_event(
    file_path,
    cur,
    connect,
    reverse,
    nodeid2msg,
    subject_uuid2hash,
    file_uuid2hash,
    net_uuid2hash,
    filelist,
):
    datalist = []
    for file in tqdm(filelist):
        with open(file_path + file, "r") as f:
            for line in f:
                events = parse_event_from_log(
                    line,
                    reverse,
                    subject_uuid2hash,
                    file_uuid2hash,
                    net_uuid2hash,
                    nodeid2msg,
                )
                # if event is not None:
                    # datalist.append(event)
                if events:
                    datalist.extend(events)
                # if '{"datum":{"com.bbn.tc.schema.avro.cdm18.Event"' in line:
                #     relation_type = re.findall('"type":"(.*?)"', line)[0]
                #     if relation_type not in exclude_edge_type:
                #         subject_uuid = re.findall(
                #             '"subject":{"com.bbn.tc.schema.avro.cdm18.UUID":"(.*?)"', line
                #         )
                #         predicateObject_uuid = re.findall(
                #             '"predicateObject":{"com.bbn.tc.schema.avro.cdm18.UUID":"(.*?)"', line
                #         )

                #         if len(subject_uuid) > 0 and len(predicateObject_uuid) > 0:
                #             if subject_uuid[0] in subject_uuid2hash and (
                #                 predicateObject_uuid[0] in subject_uuid2hash
                #                 or predicateObject_uuid[0] in file_uuid2hash
                #                 or predicateObject_uuid[0] in net_uuid2hash
                #             ):
                #                 event_uuid = re.findall(
                #                     '{"datum":{"com.bbn.tc.schema.avro.cdm18.Event":{"uuid":"(.*?)",',
                #                     line,
                #                 )[0]
                #                 time_rec = re.findall('"timestampNanos":(.*?),', line)[0]
                #                 time_rec = int(time_rec)
                #                 subjectId = subject_uuid2hash[subject_uuid[0]]
                #                 if predicateObject_uuid[0] in file_uuid2hash:
                #                     objectId = file_uuid2hash[predicateObject_uuid[0]]
                #                 elif predicateObject_uuid[0] in net_uuid2hash:
                #                     objectId = net_uuid2hash[predicateObject_uuid[0]]
                #                 else:
                #                     objectId = subject_uuid2hash[predicateObject_uuid[0]]
                #                 if relation_type in reverse:
                #                     datalist.append(
                #                         [
                #                             objectId,
                #                             nodeid2msg[objectId],
                #                             relation_type,
                #                             subjectId,
                #                             nodeid2msg[subjectId],
                #                             event_uuid,
                #                             time_rec,
                #                         ]
                #                     )
                #                 else:
                #                     datalist.append(
                #                         [
                #                             subjectId,
                #                             nodeid2msg[subjectId],
                #                             relation_type,
                #                             objectId,
                #                             nodeid2msg[objectId],
                #                             event_uuid,
                #                             time_rec,
                #                         ]
                #                     )

    sql = """insert into event_table
                         values %s
            """
    ex.execute_values(cur, sql, datalist, page_size=50000)
    connect.commit()


if __name__ == "__main__":
    args = get_runtime_required_args()
    cfg = get_yml_cfg(args)

    filelist = filelist.get_filelist(cfg.dataset.name)
    # raw_dir = cfg.dataset.raw_dir
    raw_dir = "/home/pids/rawdata/"

    cur, connect = init_database_connection(cfg)

    index_id = 0

    log("Processing netflow data")
    index_id, net_uuid2hash = store_netflow(
        file_path=raw_dir, cur=cur, connect=connect, index_id=index_id, filelist=filelist
    )

    log("Processing subject data")
    index_id, subject_uuid2hash = store_subject(
        file_path=raw_dir, cur=cur, connect=connect, index_id=index_id, filelist=filelist
    )

    log("Processing file data")
    index_id, file_uuid2hash = store_file(
        file_path=raw_dir, cur=cur, connect=connect, index_id=index_id, filelist=filelist
    )

    log("Extracting the node list")
    nodeid2msg = create_node_list(cur=cur)

    log("Processing the events")
    store_event(
        file_path=raw_dir,
        cur=cur,
        connect=connect,
        reverse=edge_reversed,
        nodeid2msg=nodeid2msg,
        subject_uuid2hash=subject_uuid2hash,
        file_uuid2hash=file_uuid2hash,
        net_uuid2hash=net_uuid2hash,
        filelist=filelist,
    )