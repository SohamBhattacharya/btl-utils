# Contents
- [Contents](#contents)
    - [Database tunnel](#database-tunnel)
    - [Create tar file with results](#create-tar-file-with-results)
    - [Module summaries](#module-summaries)
        - [SM summary examples](#sm-summary-examples)
            - [Plot](#plot)
            - [Pair SMs](#pair-sms)
        - [DM summary examples](#dm-summary-examples)
            - [Plot](#plot-1)


## Database tunnel
`./scripts/start_db_tunnel.sh <lxplus username>`

## Create tar file with results

Update tar file with new results in directory:<br>
`./scripts/archive_dir.sh <directory>`

## Module summaries

### SM summary examples

#### Plot
```bash
./python/summarize_modules.py \
--srcs /path/to/dir/with/runs \
--regexp "run(?P<run>\d+)/module_(?P<barcode>\d+)_analysis_both_calibs.root" \
--moduletype SensorModule \
--plotcfg configs/cit/config_sm_summary.yaml \
--catcfg configs/cit/config_sm_categorization.yaml \
--outdir results/sm_summary/w-calib \
--skipmodules info/cit/skip_sms.txt \
--sminfo info/cit/sm_info.yaml
```

#### Pair SMs
```bash
./python/summarize_modules.py \
--srcs /path/to/dir/with/runs \
--regexp "run(?P<run>\d+)/module_(?P<barcode>\d+)_analysis_both_calibs.root" \
--moduletype SensorModule \
--catcfg configs/cit/config_sm_categorization.yaml \
--outdir results/sm_summary/w-calib \
--skipmodules info/cit/skip_sms.txt \
--sminfo info/cit/sm_info.yaml \
--dminfo info/cit/dm_info.yaml \
--pairsms \
--location CIT
```

### DM summary examples

#### Plot
```bash
./python/summarize_modules.py \
--srcs /path/to/dir/with/runs \
--regexp "run-(?P<run>\d+)_DM-(?P<barcode>\d+).root" \
--moduletype DetectorModule \
--plotcfg configs/cit/config_dm_summary.yaml \
--catcfg configs/cit/config_dm_categorization.yaml \
--outdir results/dm_summary \
--sipminfo info/cit/sipm_info.yaml \
--sminfo info/cit/sm_info.yaml \
--dminfo info/cit/dm_info.yaml \
--skipmodules 32110040004215
```