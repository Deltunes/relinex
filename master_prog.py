import sys
import os
import subprocess
import serial.tools.list_ports

# Connects subdirectories to master_prog for importing functions
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
sys.path.insert(3, 'AWS_UPDOWN')
sys.path.insert(4, 'GIF_CONVERT')
sys.path.insert(5, 'CONCAT_FILES')

# Import functions
from UBXtoOBS import UBXtoOBS
from UBXtoNAV import UBXtoNAV
from UBXtoNAVOBS import UBXtoNAVOBS
from gnssvod_oneSite import RNXtoIMG
from aws_updown import aws_download, aws_upload
from gif_maker import makeGIF
from concatData import concatFilelistOBS, concatFilelistNAV, concatFilelistOBSNAV
from clear_files import delFilesInDir

validYes = ["y", "Y", "yes", "yeS", "yEs", "Yes", "YEs", "yES", "YES"]

# Self explanatory.
# Makes the initial output directories
def makeOutputDirs(masterOutputPath):
    os.makedirs(f"{masterOutputPath}", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/OBS_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/NAV_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS", exist_ok=True)

# Continuously collect RINEX data
def collectRINEXdata(waitTime=60, epochInterval=10, siteno=1, mode=1, comport=None):
    i = 1
    quit = False

    # Make requried output directories for each collection mode
    match mode:
        case 1:
            os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/obs", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/azielev", exist_ok=True)

        case 2:
            os.makedirs(f"{masterOutputPath}/NAV_SUCCESS/site{siteno}/nav", exist_ok=True)

        case 3:
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/obs", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/nav", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/azielev", exist_ok=True)


    try:
        while not quit:
            # Collect data for waitTime seconds
            match mode:
                case 1:
                    quit = UBXtoOBS(fileno=i, siteno=siteno, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case 2:
                    quit = UBXtoNAV(fileno=i, siteno=siteno, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case 3:
                    quit = UBXtoNAVOBS(fileno=i, siteno=siteno, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case _:
                    quit = UBXtoOBS(fileno=i, siteno=siteno, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
            i += 1

            # Attempt to print status of Raspberry Pi, will pass if not running on Pi
            try:
                subprocess.run(["vcgencmd","get_throttled"])
                subprocess.run(["vcgencmd","measure_temp"])
                subprocess.run(["free","-h"])
            except:
                print("Could not retrieve Raspberry Pi hardware info.")

            # Attempt to upload to AWS bucket
            print("Uploading RINEX and plots to AWS storage")
            try:
                aws_upload(bucketName, masterOutputPath)
            except:
                print("Upload failed! Check connection.")
            
    except KeyboardInterrupt:
        print("Quitting...")

# Set up persistent variables
masterOutputFile = open("PERSISTENT_VAR/masterOutputPath.txt", "r", encoding="utf-8")
masterOutputPath = masterOutputFile.readline()
masterOutputFile.close()
makeOutputDirs(masterOutputPath)

comportFile = open("PERSISTENT_VAR/comport.txt", "r", encoding="utf-8")
comport = comportFile.readline()
comportFile.close()

bucketFile = open("PERSISTENT_VAR/bucketName.txt", "r", encoding="utf-8")
bucketName = bucketFile.readline()
bucketFile.close()

# Menu loop
print()
while True:
    opt1 = -1
    opt2 = -1
    print("What would you like to do?")
    print("\t1) Collect RINEX Data")
    print("\t2) Combine RINEX files")
    print("\t3) Create PNG from RINEX file")
    print("\t4) Create GIF from RINEX files")
    print('\t5) Set output path ("." by default)')
    print("\t6) AWS Download/Upload")
    print("\t7) Clear Files")
    print("\t0) Quit")
    print()
    print("\t\t- ", end="")
    opt1 = input()
    try:
        opt1 = int(opt1)
    except:
        print("Invalid input. Try again.")
        print()
        continue
    print()

    match opt1:
        # Collect RINEX Data
        case 1:
            # Initalize
            valid_ports = set()
            siteno = "invalid"
            mode = "invalid"
            wait = "invalid"
            epochInt = "invalid"

            # Set COMPORT
            print(f"Current COMPORT: {comport}")
            print("Set new COMPORT? y/n")
            print("\t- ", end="")
            change = input()
            if change in validYes:
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    valid_ports.add(port.device)
                    print(f"{port.device} - {port.description}")
                while comport not in valid_ports:
                    print("Input new COMPORT.")
                    print("\t- ", end="")
                    comport = input()

                    if comport in valid_ports:
                        comportFile = open("PERSISTENT_VAR/comport.txt", "w", encoding="utf-8")
                        comportFile.write(comport)
                        comportFile.close()
                    else:
                        print("Invalid comport. Try again.")
                        print()
                print()

            # Set collection mode
            while mode == "invalid":
                print("Collection mode?")
                print("\t1) Observation file")
                print("\t2) Navigation file")
                print("\t3) OBS and NAV file")
                print("\t\t- ", end="")
                mode = input()
                try:
                    mode = int(mode)
                except:
                    print("Invalid input. Try again.")
                    print()
                    mode = "invalid"
                    continue
                if mode not in [1,2,3]:
                    print("Invalid input. Try again.")
                    print()
                    mode = "invalid"
                    continue
                print()

            # Set site number
            while siteno == "invalid":
                print("Site number? (Must be unique)")
                print("\t- ", end="")
                siteno = input()
                try:
                    siteno = int(siteno)
                except:
                    print("Invalid input. Try again.")
                    print()
                    siteno = "invalid"
                    continue
            print()

            # Set time between files
            while wait == "invalid":
                if mode in [2,3]:
                    print("Time between files? (in seconds, should be >=90s to properly record navigation files)")
                else:
                    print("Time between files? (in seconds)")
                print("\t- ", end="")
                wait = input()
                try:
                    wait = int(wait)
                except:
                    print("Invalid input. Try again.")
                    print()
                    wait = "invalid"
                    continue
                print()

            # Set time between epochs
            while epochInt == "invalid":
                print("Time between written observations? (in seconds)")
                print("\t- ", end="")
                epochInt = input()
                try:
                    epochInt = int(epochInt)
                except:
                    print("Invalid input. Try again.")
                    print()
                    epochInt = "invalid"
                    continue
                print()

            # Collect data
            collectRINEXdata(wait, epochInt, siteno, mode, comport)
            print()

        # Comine RINEX files
        case 2:
            # Initialize
            concatDirs = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS"]
            inDir = ""

            # Which directory contains files to concatenate
            whichDir = "invalid"
            validOpts = set()
            validOpts.add(0)
            while whichDir == "invalid":
                print("Concatenate which directory?")
                i = 1
                for dir in concatDirs:
                    howManyFiles = 0
                    for _, _, files in os.walk(f"{masterOutputPath}/{dir}"):
                        howManyFiles += len(files) 
                    print(f"{i}) {dir} - {howManyFiles} files")
                    validOpts.add(i)
                    i += 1
                print("0) Back")
                print("\t- ", end="")
                whichDir = input()
                try:
                    whichDir = int(whichDir)
                except:
                    print("Invalid input. Try again.")
                    print()
                    whichDir = "invalid"
                if whichDir not in validOpts:
                    print("Invalid input. Try again.")
                    print()
                    whichDir = "invalid"
                print()

            # Set input directory so listdir knows which to list
            # Also, quit if back selected
            match whichDir:
                case 1:
                    inDir = "OBS_SUCCESS"
                case 2:
                    inDir = "NAV_SUCCESS"
                case 3:
                    inDir = "OBSNAV_SUCCESS"
                case 0:
                    print()
                    continue

            # Set site number
            siteno = "invalid"
            validOpts = set()
            validOpts.add(0)
            while siteno == "invalid":
                print("Which site?")
                i = 1
                for siteDir in os.listdir(f"{masterOutputPath}/{inDir}"):
                    if siteDir != ".gitkeep":
                        print(f"{siteDir[4:]}) {siteDir}")
                        validOpts.add(int(siteDir[4:]))
                    i += 1
                print("0) Back")
                print("\t- ", end="")
                siteno = input()
                try:
                    siteno = int(siteno)
                except:
                    print("Invalid input. Try again.")
                    print()
                    siteno = "invalid"
                if siteno not in validOpts:
                    print("Invalid input. Try again.")
                    print()
                    siteno = "invalid"
                print()

            # Quit if back selected
            if siteno == 0:
                print()
                continue

            # Create required directories and concatenate files
            match whichDir:
                case 1:
                    inDir = "OBS_SUCCESS"
                    os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat/obs", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat/azielev", exist_ok=True)
                    concatFilelistOBS(inDir, siteno, masterOutputPath)
                    break
                case 2:
                    inDir = "NAV_SUCCESS"
                    os.makedirs(f"{masterOutputPath}/NAV_SUCCESS/site{siteno}/concat", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/NAV_SUCCESS/site{siteno}/concat/nav", exist_ok=True)
                    concatFilelistNAV(inDir, siteno, masterOutputPath)
                    break
                case 3:
                    inDir = "OBSNAV_SUCCESS"
                    os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/obs", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/nav", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/azielev", exist_ok=True)
                    concatFilelistOBSNAV(inDir, siteno, masterOutputPath)
                    break
                case _:
                    print("Invalid input. Try again.")
                    print()
                    continue

        # Create PNG from RINEX file
        case 3:
            # Initialize
            graphDirs = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS"]
            whichDir = "invalid"
            inDir = ""
            validOpts = set()
            validOpts.add(0)

            # Which directory contains file to visualize
            while whichDir == "invalid":
                print("Graph which directory?")
                i = 1
                # List directories and number of files
                for dir in graphDirs:
                    howManyFiles = 0
                    for _, _, files in os.walk(f"{masterOutputPath}/{dir}"):
                        howManyFiles += len(files) 
                    print(f"{i}) {dir} - {howManyFiles} files")
                    validOpts.add(i)
                    i += 1
                print("0) Back")
                print("\t- ", end="")
                whichDir = input()
                try:
                    whichDir = int(whichDir)
                except:
                    print("Invalid input. Try again.")
                    print()
                    continue
                if whichDir not in validOpts:
                    print("Invalid input. Try again.")
                    print()
                    continue
                print()

            #Quit if back is inputted
            if whichDir == 0:
                break

            # Set input directory for listdir
            match whichDir:
                case 1:
                    inDir = "OBS_SUCCESS"
                case 2:
                    inDir = "NAV_SUCCESS"
                case 3:
                    inDir = "OBSNAV_SUCCESS"

            # Set site number
            siteno = "invalid"
            validOpts = set()
            validOpts.add(0)
            while siteno == "invalid":
                print("Which site?")
                i = 1
                for siteDir in os.listdir(f"{masterOutputPath}/{inDir}"):
                    if siteDir != ".gitkeep":
                        print(f"{siteDir[4:]}) {siteDir}")
                        validOpts.add(int(siteDir[4:]))
                    i += 1
                print("0) Back")
                print("\t- ", end="")
                siteno = input()
                try:
                    siteno = int(siteno)
                except:
                    print("Invalid input. Try again.")
                    print()
                    siteno = "invalid"
                if siteno not in validOpts:
                    print("Invalid input. Try again.")
                    print()
                    siteno = "invalid"
                print()
            if siteno == 0:
                break

            # Which concat file to visualize as PNG
            whichFile = "invalid"
            validOpts = set()
            validOpts.add(0)
            concatFiles = os.listdir(f"{masterOutputPath}/{inDir}/site{siteno}/concat/obs")
            while whichFile =="invalid":
                if len(concatFiles) > 0:
                    print("Graph which file?")
                    # Print all graphable files
                    for i in range(len(concatFiles)):
                        if concatFiles[i].endswith(".rnx"):
                            print(f"{i+1}) {concatFiles[i]}")
                            validOpts.add(i+1)
                    print("0) Back")
                    print("\t- ", end="")
                    whichFile = input()
                    try:
                        whichFile = int(whichFile)
                    except:
                        print("Invalid input. Try again.")
                        print()
                        whichFile = "invalid"
                    if whichFile not in validOpts:
                        print("Invalid input. Try again.")
                        print()
                        whichFile = "invalid"
                else:
                    print("No graphable files available! Combine files before graphing.")
                    break
                print()
            if whichFile == 0:
                break

            # Make required directories
            os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/hemi", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/scatter", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs/hemi", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs/scatter", exist_ok=True)

            # Visualize
            RNXtoIMG(f"{masterOutputPath}/{inDir}/site{siteno}/concat/obs/{concatFiles[whichFile-1]}", siteno, masterOutputPath)
            print()

        # Create GIF from RINEX files
        case 4:
            # Confirm GIF conversion
            print("GIF conversion may take a while and use a good amount of RAM. Are you sure? y/n")
            print("\t- ", end="")
            contYes = input()
            print()
            if contYes in validYes:
                # Initialize
                graphDirs = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS"]
                inDir = ""

                while True:
                    # Which directory contains files to visualize as GIF
                    whichDir = "invalid"
                    validOpts = set()
                    validOpts.add(0)
                    while whichDir == "invalid":
                        print("Make GIF from files in which directory?")
                        i = 1
                        for dir in graphDirs:
                            if dir == "NAV_SUCCESS":
                                i += 1
                            else:
                                howManyFiles = 0
                                for _, _, files in os.walk(f"{masterOutputPath}/{dir}"):
                                    howManyFiles += len(files) 
                                print(f"{i}) {dir} - {howManyFiles} files")
                                validOpts.add(i)
                                i += 1
                        print("0) Back")
                        print("\t- ", end="")
                        whichDir = input()
                        try:
                            whichDir = int(whichDir)
                        except:
                            print("Invalid input. Try again.")
                            print()
                            continue
                        if whichDir not in validOpts:
                            print("Invalid input. Try again.")
                            print()
                            continue
                        print()
                    if whichDir == 0:
                        break

                    # Set input directory for listdir
                    match whichDir:
                        case 1:
                            inDir = "OBS_SUCCESS"
                        case 3:
                            inDir = "OBSNAV_SUCCESS"

                    # Set siteno
                    siteno = "invalid"
                    validOpts = set()
                    validOpts.add(0)
                    while siteno == "invalid":
                        print("Which site?")
                        i = 1
                        for siteDir in os.listdir(f"{masterOutputPath}/{inDir}"):
                            if siteDir != ".gitkeep":
                                print(f"{siteDir[4:]}) {siteDir}")
                                validOpts.add(int(siteDir[4:]))
                            i += 1
                        print("0) Back")
                        print("\t- ", end="")
                        siteno = input()
                        try:
                            siteno = int(siteno)
                        except:
                            print("Invalid input. Try again.")
                            print()
                            siteno = "invalid"
                        if siteno not in validOpts:
                            print("Invalid input. Try again.")
                            print()
                            siteno = "invalid"
                        print()
                    if siteno == 0:
                        break

                    # Make required directories
                    match whichDir:
                        case 1:
                            os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat/gif_data", exist_ok=True)
                            os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat/gif_data/obs", exist_ok=True)
                            os.makedirs(f"{masterOutputPath}/OBS_SUCCESS/site{siteno}/concat/gif_data/azielev", exist_ok=True)
                        case 3:
                            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/gif_data", exist_ok=True)
                            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/gif_data/obs", exist_ok=True)
                            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/gif_data/azielev", exist_ok=True)

                    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs/scatter", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/site{siteno}/gif_imgs/hemi", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/site{siteno}/gifs", exist_ok=True)
                    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/site{siteno}/palettes", exist_ok=True)

                    # Visualize as GIF
                    makeGIF(siteno, inDir, masterOutputPath)
            else:
                print()
                continue

        # Set output directory
        case 5:
            while True:
                # Confirm change
                print(f"Current output path: {masterOutputPath}")
                print("Change directory? y/n")
                print("\t- ", end="")
                change = input()
                print()
                if change not in validYes:
                    break

                # Set new output directory
                print("Input new output directory.")
                print("\t- ", end="")
                newDir = input()
                if os.path.isdir(newDir) == False:
                    print("Invalid directory! Does not exist.")
                    continue
                else:
                    print("Output directory set!")
                    masterOutputPath = newDir

                    masterOutputFile = open("PERSISTENT_VAR/masterOutputPath.txt", "w", encoding="utf-8")
                    masterOutputFile.write(masterOutputPath)
                    masterOutputFile.close()
                    
                    makeOutputDirs(masterOutputPath)
                    break

        # AWS Download/Upload
        case 6:
            while True:
                # Check if bucket name should change
                print(f"Current AWS bucket: {bucketName}")
                print("Set new bucket name? y/n")
                print("\t- ", end="")
                change = input()
                if change not in validYes:
                    break
                print()

                # Change bucket name
                print("Input new bucket name.")
                print("\t- ", end="")
                bucketName = input()

                bucketFile = open("PERSISTENT_VAR/bucketName.txt", "w", encoding="utf-8")
                bucketFile.write(bucketName)
                bucketFile.close()

                break
            print()

            # Upload/Download Menu
            while opt2 != 0:
                # Upload or Download?
                print("Which action?")
                print("\t1) Download")
                print("\t2) Upload")
                print("\t0) Back")
                print("\t\t- ", end="")
                opt2 = input()
                try:
                    opt2 = int(opt2)
                except:
                    print("Invalid input. Try again.")
                    print()
                    continue
                print()

                # AWS Upload or Download
                match opt2:
                    case 1:
                        try:
                            aws_download(bucketName, outputPath=masterOutputPath)
                            print()
                        except:
                            print("Download failed! Check connection.")
                            print()
                    case 2:
                        try:
                            aws_upload(bucketName, outputPath=masterOutputPath)
                            print()
                        except:
                            print("Upload failed! Check connection.")
                    case 0:
                        break
                    case _:
                        print("Invalid input. Try again.")
                        print()
                        continue

        # Clear files
        case 7:
            while opt2 != 0:
                show = False
                # Which directory to clear?
                print("Clear files from which directories?")
                print("\t1) OBS_SUCCESS")
                print("\t2) NAV_SUCCESS")
                print("\t3) OBSNAV_SUCCESS")
                print("\t4) IMAGE_SUCCESS")
                print("\t5) GIF_SUCCESS")
                print("\t6) All of the above")
                print("\t0) Back")
                print("\t\t- ", end="")
                opt2 = input()
                try:
                    opt2 = int(opt2)
                except:
                    print("Invalid input. Try again.")
                    print()
                    continue

                # Set directories to clear
                dirs = []
                delPaths = ["OBS_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS", "IMAGE_SUCCESS", "GIF_SUCCESS"]
                match opt2:
                    case 1:
                        dirs.append(delPaths[0])
                    case 2:
                        dirs.append(delPaths[1])
                    case 3:
                        dirs.append(delPaths[2])
                    case 4:
                        dirs.append(delPaths[3])
                    case 5:
                        dirs.append(delPaths[4])
                    case 6:
                        for path in delPaths:
                            dirs.append(path)
                    case 0:
                        print()
                        break
                    case _:
                        print("Invalid input. Try again.")
                        print()
                        continue
                print()

                # Show contents?
                print("Show directory contents? y/n")
                print("\t- ", end="")
                showContents = input()
                if showContents in validYes:
                    show = True
                print()

                # Show contents and delete
                for dir in dirs:
                    # If show, show contents
                    if show:
                        for (root,dirs,files) in (os.walk(f"{masterOutputPath}/{dir}",topdown=True)):
                            for file in files:
                                print(f"{root}/{file}")
                        print()

                    # Confirm deletion
                    print("Delete Files? y/n")
                    print("\t- ", end="")
                    delForReal = input()
                    print()

                    # Delete files
                    if delForReal in validYes:
                        delFilesInDir(f"{masterOutputPath}/{dir}")
                        print()
                    else:
                        print("Aborting file deletion.")
                        print()
                        continue         

        # Quit
        case 0:
            print()
            sys.exit()

        case _:
            print("Invalid Input. Try again.")

