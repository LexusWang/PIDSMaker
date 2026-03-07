# Update for new supported dataset PROVATTACK

We made updates for PIDSMAKER to support a new dataset PROVATTACK we're currently making and benchmarking.

To use our dataset, simply follow the guidelines.



## Dataset Preprocessing

### Import database with a shared dump file

1. If you already have a dump file, get a shell into the postgres container:

   ```shell
   docker exec -it postgres bash
   ```

2. Create database:

   ```shell
   psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE {DATASET_NAME};"
   ```

3. Load database:

   ```shell
   pg_restore -U postgres -h localhost -p 5432 -d {DATASET_NAME} /data/{DATASET_NAME}.dump
   ```

4. Once databases are loaded, we won't need to touch this container anymore:

   ```shell
   exit
   ```

### Preprocess with rawdata

1. If you want to load dataset from rawdata, set your rawdata directory `/path/to/raw/data:/data` in `compose-pidsmaker.yml`

2. Modify `/home/PIDSMaker/dataset_preprocessing/provattack/filelist.py`, add `{DATASET_NAME}` with corresponding rawfile you want to load. `{DATASET_NAME}`is in lowercase.

3. Get a shell into the postgres container

   ```shell
   docker exec -it postgres bash
   ```

4. Create a database in postgres for `{DATASET_NAME}` 

   ```shell
   bash dataset_preprocessing/create_database.sh {DATASET_NAME}
   ```

5. Get a shell into the pidsmaker container

   ```shell
   docker exec -it pidsmaker-pids bash
   ```

6. Load database from rawdata

   ```shell
   python -m dataset_preprocessing.provattack.create_database orthrus {DATASET_NAME}
   ```

7. To export your database as a dump file for sharing, do:

   ```shell
   PGPASSWORD=postgres pg_dump -U postgres -h postgres -p 5432 -F c -d {DATASET_NAME} -f {DATASET_NAME}.dump
   ```

## Run in pipeline

1. Before run our dataset in pipeline, there are several configurations we need to update.

2. Download the ground-truth file of your loaded dataset in `./Ground_Truth/orthrus/PROVATTACK` folder.

3. In `./pidsmaker/config/config.py`, add loaded `{DATASET_NAME}` with train/validation/test partition and set `ground_truth_relative_path`.

4. In `./pidsmaker/utils/dataset_utils.py`, add `{DATASET_NAME}` to `PROVATTACK_DATASETS`.

5. Get a shell into the pidsmaker container

   ```shell
   docker exec -it pidsmaker-pids bash
   ```

6. Run in the shell:

   ```shell
   python pidsmaker/main.py SYSTEM DATASET_NAME
   ```

   阶段一：用训练数据集正常训练（test_files 随便填 val 即可）                                                                                                                                                                                                                                                                  
                  
  python pidsmaker/main.py flash MYDATA_TRAIN

  训练完后模型权重保存在 _trained_models_dir/model_epoch_X.pt，val loss 保存在 gnn_training/_edge_losses_dir/val/。

  阶段二：换测试集，只重跑 inference 和 evaluation

  在 config.py 里新增 MYDATA_TEST_A（train_files/val_files 完全相同，只换 test_files），然后：

  python pidsmaker/main.py flash MYDATA_TEST_A --force_restart gnn_inference

  因为 test_files 现在加入了 gnn_inference 的 hash，换测试集会自动生成新的 _task_path，framework 会判断需要重跑 gnn_inference 和 evaluation，而 gnn_training 因为 hash 不变直接复用。

  换第二个测试集：

  python pidsmaker/main.py flash MYDATA_TEST_B

  python pidsmaker/main.py flash CADETS_E3

  不需要 --force_restart，因为 MYDATA_TEST_B 的 test_files 不同，hash 自然不同，framework 会自动判断 gnn_inference 需要重跑。