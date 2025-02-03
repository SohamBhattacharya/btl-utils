# Contents
- [Contents](#contents)
    - [Database tunnel](#database-tunnel)
    - [Get module and parts info from database](#get-module-and-parts-info-from-database)
    - [Module summaries](#module-summaries)
        - [SM summary examples](#sm-summary-examples)
            - [Plot](#plot)
            - [Pair SMs](#pair-sms)
        - [DM summary examples](#dm-summary-examples)
            - [Plot](#plot-1)
    - [Create tar file with results](#create-tar-file-with-results)


## Database tunnel
`./scripts/start_db_tunnel.sh <lxplus username>`

## Get module and parts info from database

* Run the scripts to get the information from the database
* Create the script for your BAC if not already there. For e.g.
  - `./scripts/cit/get_sipm_info.py`
  - `./scripts/cit/get_dm_info.py`
  - `./scripts/cit/get_sm_info.py`
* Simply changing `location_id = constants.LOCATION.XYZ` should be enough (`XYZ = CIT, UVA, MIB, PKU`).

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

## Create tar file with results

Update tar file with new results in directory:<br>
`./scripts/archive_dir.sh <directory>`