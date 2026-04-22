#!/usr/bin/env python3
"""Translate eAudit human-readable logs into PIDSMaker PostgreSQL schema CSVs.

Input:  one or more eAudit text files (output of `./eaudit -P file.txt`).
Output: 4 CSVs ready for `\\copy` into PostgreSQL:
            netflow_node_table.csv
            subject_node_table.csv
            file_node_table.csv
            event_table.csv
        plus load.sql that runs schema.sql and \\copy's all four.

Mapping from eAudit syscalls to PIDSMaker DARPA-TC operation names:

    execve        -> EVENT_EXECUTE   (file -> subject; subject's path/cmd updated)
    open          -> EVENT_OPEN      (subject -> file; binds fd in pid's table)
    read/readv/   -> EVENT_READ      (file|netflow -> subject; resolved via fd)
      pread/recv*    EVENT_RECVFROM / EVENT_RECVMSG for net reads
    write/writev/ -> EVENT_WRITE     (subject -> file|netflow)
      pwrite/send*   EVENT_SENDTO / EVENT_SENDMSG for net writes
    close         -> EVENT_CLOSE     (subject -> resource; clears fd)
    socket        -> (no edge) creates pending netflow placeholder bound to fd
    connect/bind  -> EVENT_CONNECT   (subject -> netflow; fills in endpoint)
    accept        -> EVENT_CONNECT   (netflow -> subject; new fd)
    clone/fork    -> EVENT_EXECUTE   (parent subject -> child subject; cmd inherited)
    dup2          -> copies fd entry, no edge

Anything else is dropped (mmap, mprotect, kill, setuid, ...). Add to OP_MAP
and the dispatch in handle() if you want them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional


# ---------- Regex parsers ----------

LINE_RE = re.compile(
    r'^(?P<ts>\d+\.\d+):(?P<seq>\d+):\s+'
    r'pid=(?P<pid>\d+)(?:: tid=(?P<tid>\d+))?: '
    r'(?P<rest>.*)$'
)

# syscall(...) [ret=...]
CALL_RE = re.compile(r'^(?P<call>\w+)\((?P<args>.*?)\)\s*(?P<tail>.*)$')

# Specific arg parsers
RE_FILE_ARG  = re.compile(r'file="([^"]*)"')
RE_FD_ARG    = re.compile(r'fd=(-?\d+)')
RE_RET       = re.compile(r'ret=(-?\d+)')
RE_RET_HEX   = re.compile(r'ret=([0-9a-fA-F]+)')
RE_ARGV      = re.compile(r'argv=(.*?)\s+env=')
RE_ENDPOINT  = re.compile(r'endpoint=(\S+)')


# ---------- Data model ----------

OP_MAP = {
    'execve': 'EVENT_EXECUTE',
    'open':   'EVENT_OPEN',
    'openat': 'EVENT_OPEN',
    'creat':  'EVENT_OPEN',
    'read':   'EVENT_READ',
    'readv':  'EVENT_READ',
    'pread':  'EVENT_READ',
    'preadv': 'EVENT_READ',
    'write':  'EVENT_WRITE',
    'writev': 'EVENT_WRITE',
    'pwrite': 'EVENT_WRITE',
    'pwritev':'EVENT_WRITE',
    'close':  'EVENT_CLOSE',
    'connect':'EVENT_CONNECT',
    'bind':   'EVENT_CONNECT',
    'accept': 'EVENT_CONNECT',
    'sendto': 'EVENT_SENDTO',
    'sendmsg':'EVENT_SENDMSG',
    'recvfrom':'EVENT_RECVFROM',
    'recvmsg':'EVENT_RECVMSG',
    'clone':  'EVENT_EXECUTE',
    'fork':   'EVENT_EXECUTE',
    'vfork':  'EVENT_EXECUTE',
}

# Syscalls that target a network resource via fd
NET_OPS_VIA_FD = {'EVENT_CONNECT', 'EVENT_SENDTO', 'EVENT_SENDMSG',
                  'EVENT_RECVFROM', 'EVENT_RECVMSG'}


@dataclass
class NodeStore:
    # key (varies per node type) -> dict of row fields incl. node_uuid, hash_id, index_id
    rows: dict = field(default_factory=dict)

    def get_or_create(self, key, factory) -> dict:
        row = self.rows.get(key)
        if row is None:
            row = factory()
            self.rows[key] = row
        return row


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8', 'replace')).hexdigest()

def new_uuid() -> str:
    return str(uuid.uuid4()).upper()


# ---------- Parser ----------

class Parser:
    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        self.netflows = NodeStore()  # key: (uuid_for_socket) or (saddr,sport,daddr,dport)
        self.subjects = NodeStore()  # key: (pid, exec_epoch_seq)
        self.files    = NodeStore()  # key: path

        # per-pid: {fd: ('file'|'netflow', node_dict)}
        self.fdtab: dict[int, dict[int, tuple[str, dict]]] = {}
        # current subject node per pid
        self.cur_subj: dict[int, dict] = {}
        # number of execves seen per pid (used to disambiguate pid reuse)
        self.exec_epoch: dict[int, int] = {}

        self.events: list[list] = []  # rows for event_table

    # --- node creation helpers ---

    def get_subject(self, pid: int, ts_ns: int, path: str = '', cmd: str = '') -> dict:
        epoch = self.exec_epoch.get(pid, 0)
        key = (pid, epoch)
        def make():
            node_uuid = new_uuid()
            unique = f'{node_uuid}_{path}_{cmd}'
            return {
                'node_uuid': node_uuid,
                'hash_id': sha256(unique),
                'path': path,
                'cmd': cmd or f'pid:{pid}',
                'index_id': None,  # assigned at flush
                '_pid': pid,
            }
        node = self.subjects.get_or_create(key, make)
        self.cur_subj[pid] = node
        return node

    def get_file(self, path: str) -> dict:
        def make():
            node_uuid = new_uuid()
            return {
                'node_uuid': node_uuid,
                'hash_id': sha256(f'{node_uuid}_{path}'),
                'path': path,
                'index_id': None,
            }
        return self.files.get_or_create(path, make)

    def get_netflow(self, key: tuple, src_addr='', src_port='', dst_addr='', dst_port='') -> dict:
        def make():
            node_uuid = new_uuid()
            unique = f'{node_uuid}_{src_addr}_{src_port}_{dst_addr}_{dst_port}'
            return {
                'node_uuid': node_uuid,
                'hash_id': sha256(unique),
                'src_addr': src_addr,
                'src_port': src_port,
                'dst_addr': dst_addr,
                'dst_port': dst_port,
                'index_id': None,
            }
        return self.netflows.get_or_create(key, make)

    # --- main dispatch ---

    def handle_line(self, line: str):
        m = LINE_RE.match(line)
        if not m:
            return
        ts_str, seq, pid_s = m['ts'], m['seq'], m['pid']
        rest = m['rest']
        cm = CALL_RE.match(rest)
        if not cm:
            return
        call = cm['call']
        args = cm['args']
        tail = cm['tail']

        op = OP_MAP.get(call)
        if op is None:
            return

        pid = int(pid_s)
        ts_ns = int(float(ts_str) * 1_000_000_000)
        ret_m = RE_RET.search(tail) or RE_RET.search(args)
        ret = int(ret_m.group(1)) if ret_m else None

        # Ensure subject exists for this pid (stub if pre-existing)
        subj = self.cur_subj.get(pid)
        if subj is None:
            subj = self.get_subject(pid, ts_ns)

        if call in ('execve',):
            path_m = RE_FILE_ARG.search(args)
            argv_m = RE_ARGV.search(rest)
            path = path_m.group(1) if path_m else ''
            argv = argv_m.group(1) if argv_m else path
            self.exec_epoch[pid] = self.exec_epoch.get(pid, 0) + 1
            new_subj = self.get_subject(pid, ts_ns, path=path, cmd=argv[:512])
            file_node = self.get_file(path)
            self._emit(file_node, new_subj, op, ts_ns)
            return

        if call in ('clone', 'fork', 'vfork'):
            if ret is None or ret <= 0:
                return
            child_pid = ret
            child = self.get_subject(child_pid, ts_ns,
                                     path=subj.get('path', ''),
                                     cmd=subj.get('cmd', ''))
            # inherit parent's fd table (shallow)
            self.fdtab[child_pid] = dict(self.fdtab.get(pid, {}))
            self._emit(subj, child, op, ts_ns)
            return

        if call in ('open', 'openat', 'creat'):
            if ret is None or ret < 0:
                return
            path_m = RE_FILE_ARG.search(args)
            if not path_m:
                return
            path = path_m.group(1)
            f = self.get_file(path)
            self.fdtab.setdefault(pid, {})[ret] = ('file', f)
            self._emit(subj, f, op, ts_ns)
            return

        if call == 'socket':
            if ret is None or ret < 0:
                return
            # placeholder netflow keyed by (pid, fd, ts) until connect/bind fills in
            key = ('sock', pid, ret, ts_ns)
            n = self.get_netflow(key)
            self.fdtab.setdefault(pid, {})[ret] = ('netflow', n)
            return

        if call in ('connect', 'bind'):
            fd_m = RE_FD_ARG.search(args)
            if not fd_m:
                return
            fd = int(fd_m.group(1))
            ep_m = RE_ENDPOINT.search(args) or RE_ENDPOINT.search(tail)
            endpoint = ep_m.group(1) if ep_m else ''
            saddr, sport, daddr, dport = parse_endpoint(endpoint, is_connect=(call == 'connect'))
            # reuse existing socket node if present, else create
            existing = self.fdtab.get(pid, {}).get(fd)
            if existing and existing[0] == 'netflow':
                n = existing[1]
                # update endpoint fields in-place
                n['src_addr'] = n['src_addr'] or saddr
                n['src_port'] = n['src_port'] or sport
                n['dst_addr'] = n['dst_addr'] or daddr
                n['dst_port'] = n['dst_port'] or dport
            else:
                key = ('ep', endpoint, pid, fd)
                n = self.get_netflow(key, saddr, sport, daddr, dport)
                self.fdtab.setdefault(pid, {})[fd] = ('netflow', n)
            self._emit(subj, n, op, ts_ns)
            return

        if call == 'accept':
            if ret is None or ret < 0:
                return
            ep_m = RE_ENDPOINT.search(tail) or RE_ENDPOINT.search(args)
            endpoint = ep_m.group(1) if ep_m else ''
            saddr, sport, daddr, dport = parse_endpoint(endpoint, is_connect=False)
            key = ('ep', endpoint, pid, ret)
            n = self.get_netflow(key, saddr, sport, daddr, dport)
            self.fdtab.setdefault(pid, {})[ret] = ('netflow', n)
            self._emit(n, subj, op, ts_ns)
            return

        if call == 'dup2':
            fd_m = RE_FD_ARG.search(args)
            if not fd_m or ret is None or ret < 0:
                return
            old = int(fd_m.group(1))
            entry = self.fdtab.get(pid, {}).get(old)
            if entry:
                self.fdtab.setdefault(pid, {})[ret] = entry
            return

        if call == 'close':
            fd_m = RE_FD_ARG.search(args)
            if not fd_m:
                return
            fd = int(fd_m.group(1))
            entry = self.fdtab.get(pid, {}).pop(fd, None)
            if entry:
                kind, node = entry
                self._emit(subj, node, op, ts_ns)
            return

        # read / write / send* / recv* — all need fd resolution
        fd_m = RE_FD_ARG.search(args)
        if not fd_m:
            return
        fd = int(fd_m.group(1))
        entry = self.fdtab.get(pid, {}).get(fd)
        if not entry:
            return  # unknown fd (pre-existing process); drop
        kind, node = entry

        # Promote read/write to net variants if fd is a netflow
        if kind == 'netflow' and op in ('EVENT_READ', 'EVENT_WRITE'):
            op = 'EVENT_RECVFROM' if op == 'EVENT_READ' else 'EVENT_SENDTO'

        if op in ('EVENT_READ', 'EVENT_RECVFROM', 'EVENT_RECVMSG'):
            self._emit(node, subj, op, ts_ns)
        else:
            self._emit(subj, node, op, ts_ns)

    def _emit(self, src: dict, dst: dict, op: str, ts_ns: int):
        # we store full row dicts here; index_id resolved at flush time
        self.events.append([src, dst, op, ts_ns, new_uuid()])

    # --- output ---

    def flush(self):
        # Assign globally unique index_id ranges: netflow, then subject, then file.
        idx = 0
        for n in self.netflows.rows.values():
            n['index_id'] = idx; idx += 1
        for n in self.subjects.rows.values():
            n['index_id'] = idx; idx += 1
        for n in self.files.rows.values():
            n['index_id'] = idx; idx += 1

        # Write CSVs (no header — load.sql uses HEADER FALSE)
        with open(os.path.join(self.out_dir, 'netflow_node_table.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            for n in self.netflows.rows.values():
                w.writerow([n['node_uuid'], n['hash_id'],
                            n['src_addr'], n['src_port'],
                            n['dst_addr'], n['dst_port'], n['index_id']])

        with open(os.path.join(self.out_dir, 'subject_node_table.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            for n in self.subjects.rows.values():
                w.writerow([n['node_uuid'], n['hash_id'],
                            n['path'], n['cmd'], n['index_id']])

        with open(os.path.join(self.out_dir, 'file_node_table.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            for n in self.files.rows.values():
                w.writerow([n['node_uuid'], n['hash_id'],
                            n['path'], n['index_id']])

        with open(os.path.join(self.out_dir, 'event_table.csv'), 'w', newline='') as f:
            w = csv.writer(f)
            for src, dst, op, ts_ns, ev_uuid in self.events:
                w.writerow([src['hash_id'], str(src['index_id']), op,
                            dst['hash_id'], str(dst['index_id']),
                            ev_uuid, ts_ns])

        # Copy schema.sql next to the CSVs for self-contained loading.
        import shutil
        schema_src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'schema.sql')
        if os.path.exists(schema_src):
            shutil.copy(schema_src, os.path.join(self.out_dir, 'schema.sql'))

        load_sql = os.path.join(self.out_dir, 'load.sql')
        here = os.path.abspath(self.out_dir)
        with open(load_sql, 'w') as f:
            f.write(f"\\i {here}/schema.sql\n")
            for tbl in ('netflow_node_table', 'subject_node_table',
                        'file_node_table', 'event_table'):
                cols = {
                    'netflow_node_table': '(node_uuid,hash_id,src_addr,src_port,dst_addr,dst_port,index_id)',
                    'subject_node_table': '(node_uuid,hash_id,path,cmd,index_id)',
                    'file_node_table':    '(node_uuid,hash_id,path,index_id)',
                    'event_table':        '(src_node,src_index_id,operation,dst_node,dst_index_id,event_uuid,timestamp_rec)',
                }[tbl]
                f.write(f"\\copy {tbl}{cols} FROM '{here}/{tbl}.csv' WITH (FORMAT csv);\n")

        return {
            'netflow': len(self.netflows.rows),
            'subject': len(self.subjects.rows),
            'file': len(self.files.rows),
            'events': len(self.events),
        }

    # --- ground truth + metadata ---

    def write_ground_truth(self, out_path: str, n_samples: int, seed: int):
        """Write a *placeholder* ground-truth CSV by random-sampling some real
        nodes. No actual attacks in this capture — values are stand-ins so
        downstream tooling can be exercised end-to-end.
        """
        import random
        rng = random.Random(seed)

        candidates = []  # (node_uuid, label_dict_str, index_id)
        # subjects: prefer ones with a known cmd
        for n in self.subjects.rows.values():
            label = f"{{'subject': '{(n['path'] or 'None')} {n['cmd']}'}}"
            candidates.append(('subject', n['node_uuid'], label, n['index_id']))
        for n in self.netflows.rows.values():
            src = (f"{n['src_addr']}:{n['src_port']}"
                   if n['src_port'] else n['src_addr'])
            dst = (f"{n['dst_addr']}:{n['dst_port']}"
                   if n['dst_port'] else n['dst_addr'])
            ep = f"{src}->{dst}"
            label = f"{{'netflow': '{ep}'}}"
            candidates.append(('netflow', n['node_uuid'], label, n['index_id']))
        for n in self.files.rows.values():
            label = f"{{'file': '{n['path']}'}}"
            candidates.append(('file', n['node_uuid'], label, n['index_id']))

        # take a stratified-ish mix: a few subjects, a few netflows, a few files
        by_kind = {'subject': [], 'netflow': [], 'file': []}
        for kind, *rest in candidates:
            by_kind[kind].append(rest)
        target = max(1, n_samples // 3)
        chosen = []
        for kind in ('subject', 'netflow', 'file'):
            pool = by_kind[kind]
            if not pool:
                continue
            rng.shuffle(pool)
            chosen.extend(pool[:target])
        rng.shuffle(chosen)
        chosen = chosen[:n_samples]

        with open(out_path, 'w', newline='') as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for node_uuid, label, idx in chosen:
                w.writerow([node_uuid, label, idx])
        return len(chosen)

    def write_metadata(self, out_path: str, n_gt: int):
        """Emit a metadata.md describing time range, operations, attack windows
        (placeholder), and benign/attack-day classification.
        """
        from collections import Counter
        from datetime import datetime, timezone, timedelta

        if not self.events:
            return
        ts_min = min(e[3] for e in self.events)
        ts_max = max(e[3] for e in self.events)
        dt_min = datetime.fromtimestamp(ts_min / 1e9, tz=timezone.utc)
        dt_max = datetime.fromtimestamp(ts_max / 1e9, tz=timezone.utc)
        op_counts = Counter(e[2] for e in self.events)

        # Placeholder attack window: middle 25% of the capture
        span = ts_max - ts_min
        a_start = ts_min + span // 3
        a_end   = ts_min + (2 * span) // 3
        a_start_dt = datetime.fromtimestamp(a_start / 1e9, tz=timezone.utc)
        a_end_dt   = datetime.fromtimestamp(a_end   / 1e9, tz=timezone.utc)

        # Day classification: mark any UTC day overlapping the attack window
        # as "attack (placeholder)", every other day as benign.
        day_lines = []
        cur = datetime(dt_min.year, dt_min.month, dt_min.day, tzinfo=timezone.utc)
        last = datetime(dt_max.year, dt_max.month, dt_max.day, tzinfo=timezone.utc)
        while cur <= last:
            day_start_ns = int(cur.timestamp() * 1e9)
            day_end_ns   = day_start_ns + 86_400 * 1_000_000_000
            overlaps = not (a_end < day_start_ns or a_start > day_end_ns)
            day_lines.append(
                f"- {cur.date()}: "
                f"{'ATTACK (placeholder)' if overlaps else 'benign'}")
            cur += timedelta(days=1)

        with open(out_path, 'w') as f:
            f.write("# eAudit capture — PIDSMaker metadata\n\n")
            f.write("**Source**: eAudit (`./eaudit -P`) on Ubuntu 22.04 / kernel 6.8\n\n")
            f.write("## Time range\n\n")
            f.write(f"- start: `{dt_min.isoformat()}`  (`timestamp_rec={ts_min}`)\n")
            f.write(f"- end:   `{dt_max.isoformat()}`  (`timestamp_rec={ts_max}`)\n")
            f.write(f"- span:  ~{(ts_max - ts_min) / 1e9:.1f} seconds\n\n")
            f.write("## Attack time window(s)\n\n")
            f.write("**No real attacks in this capture.** "
                    "The following window and the rows in `ground_truth.csv` "
                    "are RANDOM PLACEHOLDERS so downstream tooling can be "
                    "exercised end-to-end. Replace before any evaluation.\n\n")
            f.write(f"- Attack-PLACEHOLDER: `{a_start_dt.isoformat()}` "
                    f"to `{a_end_dt.isoformat()}`\n")
            f.write(f"  (timestamp_rec range: `{a_start}` .. `{a_end}`)\n\n")
            f.write("## Day classification (benign vs. attack)\n\n")
            for line in day_lines:
                f.write(line + "\n")
            f.write("\n## Operation types present\n\n")
            f.write(f"Total distinct operations: **{len(op_counts)}**\n\n")
            f.write("| operation | count |\n|---|---:|\n")
            for op, c in op_counts.most_common():
                f.write(f"| `{op}` | {c} |\n")
            f.write("\n## Node / event counts\n\n")
            f.write(f"- netflow_node_table: {len(self.netflows.rows)}\n")
            f.write(f"- subject_node_table: {len(self.subjects.rows)}\n")
            f.write(f"- file_node_table:    {len(self.files.rows)}\n")
            f.write(f"- event_table:        {len(self.events)}\n")
            f.write(f"- ground_truth.csv:   {n_gt} (placeholder)\n")


def parse_endpoint(ep: str, is_connect: bool):
    """Return (src_addr, src_port, dst_addr, dst_port) from an eAudit endpoint
    string. eAudit emits formats like:
        IP4:10.0.2.3:53          -> addr=10.0.2.3, port=53
        IP6:[::1]:443            -> addr=::1,      port=443
        unix:/run/foo.sock       -> addr=unix:/run/foo.sock, port=''
        netlink:0/0              -> addr=netlink:0/0, port=''
        1.2.3.4:80               -> addr=1.2.3.4,  port=80
        [::1]:443                -> addr=::1,      port=443
    For `connect`, the endpoint is the destination; src left blank.
    For `bind` / `accept`, it's the local (src) side.
    """
    if not ep:
        return ('', '', '', '')
    addr, port = ep, ''
    s = ep
    if s.startswith('IP4:'):
        s = s[4:]
        if ':' in s:
            addr, port = s.rsplit(':', 1)
        else:
            addr = s
    elif s.startswith('IP6:'):
        s = s[4:]
        if s.startswith('[') and ']:' in s:
            host, _, port = s[1:].partition(']:')
            addr = host
        elif ':' in s:
            addr, port = s.rsplit(':', 1)
        else:
            addr = s
    elif s.startswith('unix:') or s.startswith('netlink:'):
        addr, port = s, ''
    elif s.startswith('[') and ']:' in s:
        host, _, port = s[1:].partition(']:')
        addr = host
    elif ':' in s and s.count(':') == 1:
        addr, port = s.split(':', 1)
    if is_connect:
        return ('', '', addr, port)
    else:
        return (addr, port, '', '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inputs', nargs='+',
                    help='eaudit human-readable text files (or directories)')
    ap.add_argument('-o', '--out-dir', default='./out',
                    help='where to write CSVs and load.sql (default: ./out)')
    ap.add_argument('--gt-samples', type=int, default=15,
                    help='# of placeholder ground-truth rows to sample')
    ap.add_argument('--seed', type=int, default=42,
                    help='RNG seed for placeholder ground-truth sampling')
    args = ap.parse_args()

    # expand directories
    files = []
    for p in args.inputs:
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                full = os.path.join(p, fn)
                if os.path.isfile(full):
                    files.append(full)
        else:
            files.append(p)

    parser = Parser(args.out_dir)

    # Collect all lines, sort by (ts, seq) for correct ordering, then process
    all_lines = []
    for fp in files:
        # tolerate stray NULs in the file (eaudit binary-mode quirk)
        with open(fp, 'rb') as f:
            data = f.read().replace(b'\x00', b'')
        for line in data.decode('utf-8', 'replace').splitlines():
            m = LINE_RE.match(line)
            if not m:
                continue
            all_lines.append((float(m['ts']), int(m['seq']), line))

    all_lines.sort(key=lambda r: (r[0], r[1]))
    print(f'parsed {len(all_lines)} log lines from {len(files)} file(s)',
          file=sys.stderr)

    for _, _, line in all_lines:
        parser.handle_line(line)

    counts = parser.flush()
    n_gt = parser.write_ground_truth(
        os.path.join(args.out_dir, 'ground_truth.csv'),
        n_samples=args.gt_samples, seed=args.seed)
    parser.write_metadata(
        os.path.join(args.out_dir, 'metadata.md'), n_gt=n_gt)
    print(f"netflow_nodes={counts['netflow']} "
          f"subject_nodes={counts['subject']} "
          f"file_nodes={counts['file']} "
          f"events={counts['events']}", file=sys.stderr)
    print(f"output written to {os.path.abspath(args.out_dir)}", file=sys.stderr)
    print("To load into Postgres:", file=sys.stderr)
    print(f"  createdb pidsmaker_eaudit && "
          f"psql -d pidsmaker_eaudit -f {args.out_dir}/load.sql",
          file=sys.stderr)


if __name__ == '__main__':
    main()
