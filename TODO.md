# TODO

## Pending Scripts

- [ ] Write `parser_eaudit/make_ground_truth.py`: reads a `ground_truth.json` (attack window + malicious node descriptions), looks up each node in the generated node tables by its identifying fields (path for files, path+cmd for subjects, dst_addr+dst_port for netflow), and emits the `node_uuid,label_dict_string,index_id` CSV ready to place under `Ground_Truth/orthrus/<DATASET_NAME>/`.
- [x] Write `parser_eaudit/split_days.py`: post-processing script that shifts all `timestamp_rec` values in `event_table.csv` by a fixed offset so a chosen split time lands on a day boundary, enabling sub-day train/test splits without modifying PIDSMaker itself. Files updated: `event_table.csv` (shift timestamps), `load.sql` (update `\copy` paths). `schema.sql` and `ground_truth.csv` are unchanged — neither contains timestamps.

## Known Limitations

- [ ] Multi-month datasets are not supported. The construction stage builds time windows by string-concatenating `year_month` + day number (`build_default_graphs.py:249`), so all days must fall within the same calendar month. Fix would require replacing `year_month` + `start_end_day_range` with explicit date ranges.

## New Dataset Integration (eAudit)

- [ ] Create a real ground truth file to replace the placeholder `Ground_Truth/orthrus/EAUDIT_TEST/node_eaudit_test_0420.csv`. The current file is a random sample with no real attack nodes. A real ground truth CSV should list the actual malicious nodes (one per line: `node_uuid,label_dict,index_id`).
- [ ] Update the attack time window in `pidsmaker/config/config.py` under `EAUDIT_TEST` once the real attack timestamps are known.
- [ ] Replace `train_files`/`val_files` in the `EAUDIT_TEST` dataset config with a separate benign-only training dataset (currently both point to `graph_20`, the same day as the test set).
