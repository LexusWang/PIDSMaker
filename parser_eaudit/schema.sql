-- PIDSMaker target schema. 4 node/event tables.

DROP TABLE IF EXISTS event_table;
DROP TABLE IF EXISTS netflow_node_table;
DROP TABLE IF EXISTS subject_node_table;
DROP TABLE IF EXISTS file_node_table;
DROP SEQUENCE IF EXISTS event_table__id_seq;

CREATE TABLE netflow_node_table (
    node_uuid  CHARACTER VARYING NOT NULL,
    hash_id    CHARACTER VARYING NOT NULL,
    src_addr   CHARACTER VARYING,
    src_port   CHARACTER VARYING,
    dst_addr   CHARACTER VARYING,
    dst_port   CHARACTER VARYING,
    index_id   BIGINT,
    PRIMARY KEY (node_uuid, hash_id)
);

CREATE TABLE subject_node_table (
    node_uuid  CHARACTER VARYING NOT NULL,
    hash_id    CHARACTER VARYING NOT NULL,
    path       CHARACTER VARYING,
    cmd        CHARACTER VARYING,
    index_id   BIGINT,
    PRIMARY KEY (node_uuid, hash_id)
);

CREATE TABLE file_node_table (
    node_uuid  CHARACTER VARYING NOT NULL,
    hash_id    CHARACTER VARYING NOT NULL,
    path       CHARACTER VARYING,
    index_id   BIGINT,
    PRIMARY KEY (node_uuid, hash_id)
);

CREATE SEQUENCE event_table__id_seq;
CREATE TABLE event_table (
    src_node       CHARACTER VARYING,
    src_index_id   CHARACTER VARYING,
    operation      CHARACTER VARYING,
    dst_node       CHARACTER VARYING,
    dst_index_id   CHARACTER VARYING,
    event_uuid     CHARACTER VARYING NOT NULL,
    timestamp_rec  BIGINT,
    _id            INTEGER NOT NULL DEFAULT nextval('event_table__id_seq'::regclass)
);
CREATE UNIQUE INDEX event_table__id_uindex ON event_table (_id);
CREATE INDEX event_table_ts_idx ON event_table (timestamp_rec);
CREATE INDEX event_table_src_idx ON event_table (src_node);
CREATE INDEX event_table_dst_idx ON event_table (dst_node);
