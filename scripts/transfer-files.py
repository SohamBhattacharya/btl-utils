#!/usr/bin/env python3

import argparse
import glob
import os
import psutil

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


def main() :
    """
    Compute checksums of specified file extensions
    Transfer files
    Compare checksums of aforementioned extensions (only)
    """
    
    # Argument parser
    parser = argparse.ArgumentParser(formatter_class = utils.Formatter)
    
    parser.add_argument(
        "--srcs",
        help = "Source directory or file\n   ",
        type = str,
        nargs = "*",
        required = True,
    )
    
    parser.add_argument(
        "--dest",
        help = "Remote destination path, for e.g. user@host:/path/to/directory/\n   ",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--destlocal",
        help = "Destination path mounted locally\n   ",
        type = str,
        required = False,
    )
    
    parser.add_argument(
        "--exts",
        help = "Space separated list of extensions to be considered: .ext1 .ext2 ...\n   ",
        type = str,
        nargs = "+",
        required = False,
        default = [".hdf5", ",hf5"],
    )
    
    parser.add_argument(
        "--sumonly",
        help = "Only create checksums\n   ",
        default = False,
        action = "store_true",
    )
    
    parser.add_argument(
        "--sumf",
        help = "Force checksum creation even if it exists\n   ",
        default = False,
        action = "store_true",
    )
    
    parser.add_argument(
        "--cmponly",
        help = (
            "Only compare files\n"
            "sum: compare checksums; destination checksum files must exist in <destlocal>\n"
            "cmp: compare byte by byte\n   "
        ),
        choices = ["sum", "cmp"],
        #default = "cmp",
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    
    # Check if remote destination is valid 
    if (args.dest and (not args.cmponly) and (not args.sumonly)) :
        
        dest = args.dest if (":" in args.dest) else f"{args.dest}:/"
        uhost, destpath = dest.split(":")
        user, host = uhost.split("@")
        destpath = destpath if len(destpath) else "/"
        
        # Trailing comma after user is necessary to pass an empty password
        cmd = f"lftp -c \"open -u {user}, sftp://{host}; cd {destpath}\""
        print(cmd)
        cmd_retval = os.system(cmd)
        
        if (cmd_retval) :
            
            print(f"Error: cannot connect or invalid destination path: {args.dest}")
            exit(cmd_retval)
    
    
    # Check if locally mounted destination is valid
    if (args.destlocal) :
        
        if (not os.path.exists(args.destlocal)) :
            
            print(f"Error: cannot find destlocal: {args.destlocal}")
            exit(1)
        
        partitions = psutil.disk_partitions(all = True)
        # Select the remote partitions mounted using sshfs
        partitions = [_part for _part in partitions if (part.fstype in ["fuse.sshfs"])]
        
        ismountpoint = False
        destlocal = os.path.abspath(args.destlocal)
        
        for part in partitions :
            
            if part.fstype != "fuse.sshfs" :
                
                continue
            
            if destlocal.startswith(part.mountpoint) :
                
                ismountpoint = True
                break
        
        
        if (not ismountpoint) :
            
            print(f"Error: destlocal is not (or, is not inside) a valid mountpoint: {args.destlocal}")
            exit(1)
    
    
    l_file = []
    l_file_relative = []
    
    
    # Get the list of files with specified extensions
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
            l_tmp = [_f for _f in l_tmp if os.path.isfile(_f) and _f.endswith(tuple(args.exts))]
            l_file.extend(l_tmp)
            
            # If src is a/b, and the file is a/b/c/file.ext
            # Get b/c/file.ext, which is the path relative to the destination
            srcdir = src.split("/")[-1]
            l_file_relative.extend([f"{srcdir}/{_f[len(src):]}" for _f in l_tmp])
    
    nfiles = len(l_file)
    cwd = os.getcwd()
    
    
    # Produce checksums for files with specified extensions
    if ((not args.cmponly) or args.sumonly) :
        
        print("\n")
        print("="*50)
        print(f"Producing checksums for extensions {', '.join(args.exts)} ...")
        
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
    
    
    # Copy files with specified extensions
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
    
    
    # Check the destination files
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