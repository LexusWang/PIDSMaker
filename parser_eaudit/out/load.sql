\i /home/victim/Desktop/eaudit/parser_pidsmaker/out/schema.sql
\copy netflow_node_table(node_uuid,hash_id,src_addr,src_port,dst_addr,dst_port,index_id) FROM '/home/victim/Desktop/eaudit/parser_pidsmaker/out/netflow_node_table.csv' WITH (FORMAT csv);
\copy subject_node_table(node_uuid,hash_id,path,cmd,index_id) FROM '/home/victim/Desktop/eaudit/parser_pidsmaker/out/subject_node_table.csv' WITH (FORMAT csv);
\copy file_node_table(node_uuid,hash_id,path,index_id) FROM '/home/victim/Desktop/eaudit/parser_pidsmaker/out/file_node_table.csv' WITH (FORMAT csv);
\copy event_table(src_node,src_index_id,operation,dst_node,dst_index_id,event_uuid,timestamp_rec) FROM '/home/victim/Desktop/eaudit/parser_pidsmaker/out/event_table.csv' WITH (FORMAT csv);
