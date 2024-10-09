#!/usr/bin/env python3

import argparse
import glob
import os

import utils


def get_file_details(f) :
    
    fdir = os.path.dirname(f)
    fdir = "." if not len(fdir) else fdir
    fbase = os.path.basename(f)
    fname, fext = os.path.splitext(fbase)
    
    #csumfile = f"{fname}.sha512"
    
    return {
        "fdir": fdir,
        "fbase": fbase,
        "fname": fname,
        "fext": fext,
    }

# Compute checksums of hdf5 and root file extensions (only)
# Transfer files
# Compare checksums of aforementioned extensions (only)

def main() :
    
    # Argument parser
    parser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter)
    
    parser.add_argument(
        "--srcs",
        help = "Source directory or file",
        type = str,
        nargs = "*",
        required = True,
    )
    
    parser.add_argument(
        "--dest",
        help = (
            "Destination path (can be remote path like user@host:/path/to/directory); "
            "can take a dummy string if no copying is required"
        ),
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--destlocal",
        help = "Destination path mounted locally",
        type = str,
        required = True,
    )
    
    parser.add_argument(
        "--sumonly",
        help = "Only create checksums",
        default = False,
        action = "store_true",
    )
    
    parser.add_argument(
        "--sumf",
        help = "Force checksum creation even if it exists",
        default = False,
        action = "store_true",
    )
    
    parser.add_argument(
        "--cmponly",
        help = (
            "Only compare files\n"
            "sum: compare checksums; destination checksum files must exist in <destlocal>\n"
            "cmp: compare byte by byte"
        ),
        choices = ["sum", "cmp"],
        #default = "cmp",
    )
    
    # Parse arguments
    args = parser.parse_args()
    #d_args = vars(args)
    
    l_file = []
    l_file_relative = []
    l_ext = (".hdf5", ".h5", ".root")
    
    for src in args.srcs :
        
        while "//" in src:
            
            src = src.replace("//", "/")
        
        src = src[0: -1] if src.endswith("/") else src
        
        if (os.path.isfile(src)) :
            
            fdetails = get_file_details(f)
            
            l_file.append(src)
            l_file_relative.append(fdetails["basename"])
        
        else :
            
            l_tmp = glob.glob(f"{src}/**", recursive = True)
            l_tmp = [_f for _f in l_tmp if os.path.isfile(_f) and _f.endswith(l_ext)]
            l_file.extend(l_tmp)
            
            # If src is a/b, and the file is a/b/c/file.root
            # Get b/c/file.root, which is the path relative to the destination
            srcdir = src.split("/")[-1]
            l_file_relative.extend([f"{srcdir}/{_f[len(src):]}" for _f in l_tmp])
    
    nfiles = len(l_file)
    cwd = os.getcwd()
    
    if ((not args.cmponly) or args.sumonly) :
        
        print("\n")
        print("="*50)
        print(f"Producing checksums for extensions {', '.join(l_ext)} ...")
        
        for ifile, f in enumerate(l_file) :
            
            fdetails = get_file_details(f)
            csumfile = f"{fdetails['fname']}.sha512"
            
            if (not os.path.exists(f"{fdetails['fdir']}/{csumfile}") or args.sumf) :
                
                l_cmd = [
                    f"cd {fdetails['fdir']}; sha512sum {fdetails['fbase']} > {csumfile}",
                    f"cd {cwd}"
                ]
                
                utils.run_cmd_list(l_cmd)
                
                print(f"[{ifile+1}/{nfiles}] Produced checksum for file {f}: {fdetails['fdir']}/{csumfile}")
            
            else :
                
                print(f"[{ifile+1}/{nfiles}] Skipping file {f}; checksum exists: {fdetails['fdir']}/{csumfile}")
        
        print("Finished producing checksums.")
    
    if ((not args.cmponly) and (not args.sumonly)) :
        
        print("\n")
        print("="*50)
        print("Copying files ...")
        
        for src in args.srcs :
            
            l_cmd = [
                f"/bin/bash -c \'sftp -r {args.dest} <<< \"put {src} .\"\'"
            ]
            
            utils.run_cmd_list(l_cmd, debug = True)
        
        print("Finished copying files.")
    
    if (not args.sumonly) :
        
        print("\n")
        print("="*50)
        print("Starting comparisons ...")
        
        destlocal = os.path.abspath(args.destlocal)
        
        l_failed = []
        
        for ifile, f in enumerate(l_file_relative) :
            
            fdetails = get_file_details(f)
            fdestlocal = f"{destlocal}/{fdetails['fdir']}/{fdetails['fbase']}"
            
            if (args.cmponly == "cmp") :
                
                cmd = f"cmp -s {l_file[ifile]} {fdestlocal}"
                cmd_retval = os.system(cmd)
            
            elif (not args.cmponly or args.cmponly == "sum") :
                
                csumfile = f"{fdetails['fname']}.sha512"
                
                cmd = f"cd {destlocal}/{fdetails['fdir']}; sha512sum --status -c {csumfile}"
                cmd_retval = os.system(cmd)
            
            print(f"[{ifile+1}/{nfiles}] Status {cmd_retval} for file {fdestlocal}")
            
            if (cmd_retval) :
                
                l_failed.append(l_file[ifile])
            
        
        print("\n")
        print("="*50)
        
        if len(l_failed) :
            
            print(f"Failed {len(l_failed)}/{nfiles} files:")
            print("\n".join(l_failed))
        
        else :
            
            print("No failed files. Success!")
    
    return 0


if __name__ == "__main__" :
    
    main()