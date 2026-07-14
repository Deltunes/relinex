import sys
import os
import subprocess
import serial.tools.list_ports
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
sys.path.insert(3, 'AWS_UPDOWN')
sys.path.insert(4, 'GIF_CONVERT')
sys.path.insert(5, 'CONCAT_FILES')
from UBXtoRNX import UBXtoRNX
from UBXtoNAV import UBXtoNAV
from UBXtoNAVOBS import UBXtoNAVOBS
from aws_updown import aws_download, aws_upload
from gif_maker import makeGIF
from concatData import concatFilelistRNX, concatFilelistOBSNAV
from clear_files import delFilesInDir

validYes = ["y", "Y", "yes", "YES", "Yes"]

def makeOutputDirs(masterOutputPath):
    os.makedirs(f"{masterOutputPath}", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/rinex", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/azielev", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat/rinex", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat/azielev", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat/gif_data", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat/gif_data/rinex", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat/gif_data/azielev", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/NAV_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/hemi", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/scatter", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/gif_imgs", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/gif_imgs/hemi", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/gif_imgs/scatter", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/gifs", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/palettes", exist_ok=True)

def collectRINEXdata(waitTime=60, epochInterval=10, siteno=1, mode=1, comport=None):
    i = 1
    quit = False

    match mode:
        case 3:
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/obs", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/nav", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/obs", exist_ok=True)
            os.makedirs(f"{masterOutputPath}/OBSNAV_SUCCESS/site{siteno}/concat/nav", exist_ok=True)

    try:
        while not quit:
            match mode:
                case 1:
                    quit = UBXtoRNX(fileno=i, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case 2:
                    quit = UBXtoNAV(fileno=i, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case 3:
                    quit = UBXtoNAVOBS(fileno=i, siteno=siteno, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
                case _:
                    quit = UBXtoRNX(fileno=i, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath, comport=comport)
            i += 1

            try:
                subprocess.run(["vcgencmd","get_throttled"])
                subprocess.run(["vcgencmd","measure_temp"])
                subprocess.run(["free","-h"])
            except:
                print("Could not retrieve Raspberry Pi hardware info.")

            if quit:
                print("Quitting...")
                break

            print("Uploading RINEX and plots to AWS storage")
            try:
                aws_upload(bucketName, masterOutputPath)
            except:
                print("Upload failed! Check connection.")
            
    except KeyboardInterrupt:
        print("Keyboard Interrupt! Quitting...")

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

print()
while True:
    opt1 = -1
    opt2 = -1
    print("What would you like to do?")
    print("\t1) Collect RINEX Data")
    print("\t2) Combine RINEX files")
    print("\t3) Create GIF from RINEX files")
    print('\t4) Set output path ("." by default)')
    print("\t5) AWS Download/Upload")
    print("\t6) Clear Files")
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
        case 1:
            siteno = "invalid"
            mode = "invalid"
            wait = "invalid"
            epochInt = "invalid"
            while True:
                print(f"Current COMPORT: {comport}")
                print("Set new COMPORT? y/n")
                print("\t- ", end="")
                change = input()
                if change not in validYes:
                    break
                print()

                ports = serial.tools.list_ports.comports()
                for port in ports:
                    print(f"{port.device} - {port.description}")
                print()

                print("Input new COMPORT.")
                print("\t- ", end="")
                comport = input()

                comportFile = open("PERSISTENT_VAR/comport.txt", "w", encoding="utf-8")
                comportFile.write(comport)
                comportFile.close()

                break
            print()

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

            while wait == "invalid":
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
            
            collectRINEXdata(wait, epochInt, siteno, mode, comport)
            print()

        case 2:
            concatDirs = ["RNX_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS"]
            inDir = ""
            whichDir = -1

            while whichDir != 0:
                print("Concatenate which directory?")
                i = 1
                for dir in concatDirs:
                    howManyFiles = 0
                    for _, _, files in os.walk(f"{masterOutputPath}/{dir}"):
                        howManyFiles += len(files) 
                    print(f"{i}) {dir} - {howManyFiles} files")
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
                print()

                match whichDir:
                    case 1:
                        inDir = "RNX_SUCCESS"
                    case 2:
                        inDir = "NAV_SUCCESS"
                    case 3:
                        inDir = "OBSNAV_SUCCESS"

                siteno = "invalid"
                while siteno == "invalid":
                    print("Which site?")
                    i = 1
                    for siteDir in os.listdir(f"{masterOutputPath}/{inDir}"):
                        if siteDir != ".gitkeep":
                            print(f"{siteDir[4:]}) {siteDir}")
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
                    print()

                match whichDir:
                    case 1:
                        print("rnx")
                        inDir = "RNX_SUCCESS"
                        concatFilelistRNX(inDir, masterOutputPath)
                        break
                    case 2:
                        print("nav")
                        inDir = "NAV_SUCCESS"
                        break
                    case 3:
                        print("obsnav")
                        inDir = "OBSNAV_SUCCESS"
                        concatFilelistOBSNAV(inDir, siteno, masterOutputPath)
                        break
                    case 0:
                        break
                    case _:
                        print("Invalid input. Try again.")
                        print()
                        continue

        case 3:
            print("GIF conversion may take a while and use a good amount of RAM. Are you sure? y/n")
            print("\t- ", end="")
            contYes = input()
            if contYes in validYes:
                makeGIF(masterOutputPath)
            else:
                print()
                continue

        case 4:
            while True:
                print(f"Current output path: {masterOutputPath}")
                print("Change directory? y/n")
                print("\t- ", end="")
                change = input()
                print()
                if change not in validYes:
                    break

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

        case 5:
            while True:
                print(f"Current AWS bucket: {bucketName}")
                print("Set new bucket name? y/n")
                print("\t- ", end="")
                change = input()
                if change not in validYes:
                    break
                print()

                print("Input new bucket name.")
                print("\t- ", end="")
                bucketName = input()

                bucketFile = open("PERSISTENT_VAR/bucketName.txt", "w", encoding="utf-8")
                bucketFile.write(bucketName)
                bucketFile.close()

                break
            print()
                
            while opt2 != 0:
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

        case 6:
            while opt2 != 0:
                show = False
                print("Clear files from which directories?")
                print("\t1) RNX_SUCCESS")
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

                dirs = []
                delPaths = ["RNX_SUCCESS", "NAV_SUCCESS", "OBSNAV_SUCCESS", "IMAGE_SUCCESS", "GIF_SUCCESS"]
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

                print("Show directory contents? y/n")
                print("\t- ", end="")
                showContents = input()
                if showContents in validYes:
                    show = True
                print()

                for dir in dirs:
                    if show:
                        for (root,dirs,files) in (os.walk(f"{masterOutputPath}/{dir}",topdown=True)):
                            for file in files:
                                print(f"{root}/{file}")
                        print()

                    print("Delete Files? y/n")
                    print("\t- ", end="")
                    delForReal = input()
                    print()

                    if delForReal in validYes:
                        delFilesInDir(f"{masterOutputPath}/{dir}")
                        print()
                    else:
                        print("Aborting file deletion.")
                        print()
                        continue         

        case 0:
            print()
            sys.exit()

        case _:
            print("Invalid Input. Try again.")

