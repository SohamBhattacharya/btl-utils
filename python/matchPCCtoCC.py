#! /usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import argparse
import pathlib
import os
import sys
import subprocess

LOCATION_IDs = {}
LOCATION_IDs['MIB'] = 5380
LOCATION_IDs['UVA'] = 1003
LOCATION_IDs['CIT'] = 5023
LOCATION_IDs['PKU'] = 3800
LOCATION_IDs['CERN'] = 1005
LOCATION_IDs['TRANSIT'] = 2880


api_path = str(pathlib.Path(__file__).parent.resolve())
myenv = os.environ.copy()
myenv_path = myenv.get("PATH", "")

if api_path not in myenv_path:
    myenv_path = f"{api_path}:{myenv_path}"

myenv["PATH"] = myenv_path

parser = argparse.ArgumentParser(description='Get list of SiPM')
parser.add_argument('-l', '--location', type=str, required=True, help="location (MIB, UVA, CIT, PKU, CERN, TRANSIT)")
args = parser.parse_args()

# Get list of PCCi 1.2 V
#query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'PCCIv1.2\' and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'PCCIv1.2\' and s.PART_PARENT_ID is NULL and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
output = subprocess.run(['rhapi.py', 
                         '-u', 'http://localhost:8113',
                         query,
                         '-a'],
                        stdout=subprocess.PIPE, env = myenv)
PCC12s = output.stdout.decode('utf-8').split()
PCC12s.pop(0)
print('Found %d PCCIv1.2'%len(PCC12s))
#print(PCC12s)

# Get list of PCCi 2.5 V
#query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'PCCIv2.5\' and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'PCCIv2.5\' and s.PART_PARENT_ID is NULL and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
output = subprocess.run(['rhapi.py', 
                         '-u', 'http://localhost:8113',
                         query,
                         '-a'],
                        stdout=subprocess.PIPE, env = myenv)
PCC25s = output.stdout.decode('utf-8').split()
PCC25s.pop(0)
print('Found %d PCCIv2.5'%len(PCC25s))
#print(PCC25s)

# Get list of CC
query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'CC\' and s.PART_PARENT_ID is NULL and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
#query = 'select s.BARCODE from mtd_cmsr.parts s where s.KIND_OF_PART = \'CC\' and ( s.PART_PARENT_ID is NULL or s.PART_PARENT_ID = 1000 ) and s.LOCATION_ID = %d'%(LOCATION_IDs[args.location])
output = subprocess.run(['rhapi.py', 
                         '-u', 'http://localhost:8113',
                         query,
                         '-a'],
                        stdout=subprocess.PIPE, env = myenv)
CCs = output.stdout.decode('utf-8').split()
CCs.pop(0)
#CCs = ["32110052300339"]
#CCs.extend([
#"32110052300245",
#"32110052300262",
#"32110052300263",
#"32110052300266",
#"32110052300268",
#"32110052300276",
#"32110052300277",
#"32110052300280",
#"32110052300281",
#"32110052300307",
#"32110052300370",
#"32110052300383",
#"32110052300392",
#"32110052300397",
#"32110052300440",
#"32110052300499",
#"32110052300502",
#"32110052300503",
#"32110052300506",
#"32110052300508",
#"32110052300509",
#"32110052300511",
#"32110052300512",
#"32110052300513",
#])
print('Found %d CC'%len(CCs))
#print(CCs)

pcc_csv_file = "info/COMMON/pcc_analysis_summary.csv"
pcc_df = pd.read_csv(pcc_csv_file)
#print(pcc_df)

cc_csv_file = "info/COMMON/cc_calibrations.csv"
cc_df = pd.read_csv(cc_csv_file)
#print(cc_df)



##########################
### sort CCs by IEO values 
cc_df['barcode'] = '32110052300' + cc_df['CC_num'].astype(int).astype(str).str.zfill(3)
cc_df_filtered = cc_df.dropna(subset=['L0_EOM_IEO', 'L1_EOM_IEO'])
cc_df_filtered = cc_df_filtered[cc_df_filtered['barcode'].isin(CCs)]
cc_df_filtered['worst_IEO'] = cc_df_filtered[['L0_EOM_IEO', 'L1_EOM_IEO']].apply(lambda x: max(abs(x['L0_EOM_IEO'] - 15), abs(x['L1_EOM_IEO'] - 15)), axis=1)
print('\n############################')
print('Found %d CCs with IEO values'%len(cc_df_filtered))
print(cc_df_filtered[['barcode', 'worst_IEO']].sort_values(by='worst_IEO', ascending=False))



###############################################################
# Get the list of df_25V where 'vouty_-31_-29_avg' is > limit25
limits = (1.175,2.475)
limits_EOM8 = [(1.175,2.55),(1.2,2.475)]

df_12V = pcc_df[pcc_df['pcc_barcode'].astype(str).str.contains('12V')]
df_25V = pcc_df[pcc_df['pcc_barcode'].astype(str).str.contains('25V')]

df_12V_filtered = df_12V[df_12V['vouty_-31_-29_avg'] > limits[0]].copy()
df_12V_filtered['barcode'] = '3211001231' + df_12V_filtered['pcc_barcode'].astype(str).str[-4:]
df_12V_filtered = df_12V_filtered[df_12V_filtered['barcode'].isin(PCC12s)]
df_12V_filtered = df_12V_filtered.sort_values(by='vouty_-31_-29_avg', ascending=False)

df_25V_filtered = df_25V[df_25V['vouty_-31_-29_avg'] > limits[1]].copy()
df_25V_filtered['barcode'] = '3211002531' + df_25V_filtered['pcc_barcode'].astype(str).str[-4:]
df_25V_filtered = df_25V_filtered[df_25V_filtered['barcode'].isin(PCC25s)]
df_25V_filtered = df_25V_filtered.sort_values(by='vouty_-31_-29_avg', ascending=False)

pairings_EOM8 = []
for jj in range(min(len(df_12V_filtered),len(df_25V_filtered))):
    accept = False
    for limit in limits_EOM8:
        if df_12V_filtered.iloc[jj]['vouty_-31_-29_avg'] > limit[0] and df_25V_filtered.iloc[jj]['vouty_-31_-29_avg'] > limit[1]:
            accept = True
    if accept == True:
        pairings_EOM8.append((df_12V_filtered.iloc[jj]['barcode'],df_25V_filtered.iloc[jj]['barcode']))
    if len(pairings_EOM8) == 9:
        break

print('\n###############################')
print('PCC pairings for EOM8 CC boards:')
for pairing in pairings_EOM8:
    print('PCCIv1.2: %s (%.3f V)  -   PCCIv2.5: %s (%.3f V)'%(pairing[0],df_12V_filtered[df_12V_filtered['barcode'] == pairing[0]]['vouty_-31_-29_avg'].values[0],pairing[1],df_25V_filtered[df_25V_filtered['barcode'] == pairing[1]]['vouty_-31_-29_avg'].values[0]))
    df_12V_filtered = df_12V_filtered[df_12V_filtered['barcode'] != pairing[0]]
    df_25V_filtered = df_25V_filtered[df_25V_filtered['barcode'] != pairing[1]]

print('\n###############################')
print('Remaining %d PCCIv1.2 within ranges'%len(df_12V_filtered))
#print(df_12V_filtered[['barcode','vouty_-31_-29_avg']])

print('\n###############################')
print('Remaining %d PCCIv2.5 within ranges'%len(df_25V_filtered))
#print(df_25V_filtered[['barcode','vouty_-31_-29_avg']])


# Divide df_25V_filtered into len(cc_df_filtered) chunks ordered by vouty_-31_-29_avg
num_chunks = len(cc_df_filtered)
df_25V_sorted = df_25V_filtered.sort_values(by='vouty_-31_-29_avg', ascending=False)
df_25V_chunks = []
chunk_size = len(df_25V_sorted) // num_chunks
remainder = len(df_25V_sorted) % num_chunks
start = 0
for i in range(num_chunks):
    end = start + chunk_size + (1 if i < remainder else 0)
    df_25V_chunks.append(df_25V_sorted.iloc[start:end])
    start = end

# Divide df_12V_filtered into len(cc_df_filtered) chunks ordered by vouty_-31_-29_avg
num_chunks = len(cc_df_filtered)
df_12V_sorted = df_12V_filtered.sort_values(by='vouty_-31_-29_avg', ascending=False)
df_12V_chunks = []
chunk_size = len(df_12V_sorted) // num_chunks
remainder = len(df_12V_sorted) % num_chunks
start = 0
for i in range(num_chunks):
    end = start + chunk_size + (1 if i < remainder else 0)
    df_12V_chunks.append(df_12V_sorted.iloc[start:end])
    start = end


for i, row in cc_df_filtered.sort_values(by='worst_IEO', ascending=False).reset_index(drop=True).iterrows():
    print(f"\n\n\n---> CC barcode: {row['barcode']}, worst_IEO: {row['worst_IEO']}")
    print("PCCIv1.2 barcodes and Vout:")
    for _, pcc_row in df_12V_chunks[i].iterrows():
        print(f"  {pcc_row['barcode']}: {'%.3f V'%pcc_row['vouty_-31_-29_avg']}")
    print("PCCIv2.5 barcodes and Vout:")
    for _, pcc_row in df_25V_chunks[i].iterrows():
        print(f"  {pcc_row['barcode']}: {'%.3f V'%pcc_row['vouty_-31_-29_avg']}")
    

###
#### Get the 'vouty_-31_-29_avg' values
###vouty_25V = df_25V['vouty_-31_-29_avg']
###vouty_12V = df_12V['vouty_-31_-29_avg']
###
###num_25V_good = (vouty_25V >= 2.475).sum()
###fraction_25V_good = (vouty_25V >= 2.475).mean()
###print(f"25V boards with vouty_-31_-29_avg >= 2.475: {num_25V_good}/{len(vouty_25V)} ({fraction_25V_good:.3f})")
###
###num_12V_good = (vouty_12V >= 1.175).sum()
###fraction_12V_good = (vouty_12V >= 1.175).mean()
###print(f"12V boards with vouty_-31_-29_avg >= 1.175: {num_12V_good}/{len(vouty_12V)} ({fraction_12V_good:.3f})")
###
#### Print barcodes of rejected 25V boards
###rejected_25V = df_25V[vouty_25V < 2.475]['pcc_barcode']
###print("Rejected 25V barcodes:")
###print(rejected_25V.to_list())
###
#### Print barcodes of rejected 12V boards
###rejected_12V = df_12V[vouty_12V < 1.175]['pcc_barcode']
###print("Rejected 12V barcodes:")
###print(rejected_12V.to_list())
###
##### Plot histograms for 25V and 12V as subpanels of the same plot
####fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
####
## 25V subplot
#axes[0].hist(vouty_25V, bins=30, alpha=0.7, color='blue')
#axes[0].set_xlabel('vouty_-31_-29_avg')
#axes[0].set_ylabel('Count')
#axes[0].set_title('25V')
#
## 12V subplot
#axes[1].hist(vouty_12V, bins=30, alpha=0.7, color='orange')
#axes[1].set_xlabel('vouty_-31_-29_avg')
#axes[1].set_title('12V')
#
#fig.suptitle('Histogram of vouty_-31_-29_avg for 25V and 12V')
#plt.tight_layout(rect=[0, 0.03, 1, 0.95])
#plt.show()
