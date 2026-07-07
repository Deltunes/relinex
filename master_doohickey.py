import sys
import os
import subprocess
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
sys.path.insert(3, 'AWS_DOWNLOAD')
sys.path.insert(4, 'AWS_UPLOAD')
sys.path.insert(5, 'GIF_CONVERT')
from UBXtoRNXconv import UBXtoRNX, mkconv
from aws_download import aws_download
from aws_upload import aws_upload
from gif_maker import makeGIF
from clear_files import delFilesInDir

validYes = ["y", "Y", "yes", "YES", "Yes"]

def makeOutputDirs(masterOutputPath):
    os.makedirs(f"{masterOutputPath}", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/rinex", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/azielev", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/RNX_SUCCESS/concat", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/NAV_SUCCESS", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/hemi", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/IMAGE_SUCCESS/scatter", exist_ok=True)

    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/gifs", exist_ok=True)
    os.makedirs(f"{masterOutputPath}/GIF_SUCCESS/palettes", exist_ok=True)

masterOutputFile = open("masterOutputPath.txt", "r", encoding="utf-8")
masterOutputPath = masterOutputFile.readline()
masterOutputFile.close()
makeOutputDirs(masterOutputPath)

def collectRINEXdata(waitTime=60, epochInterval=10):
    # Variables
    i = 1
    quit = False
    conv = mkconv()
    aws_fileset = set()

    try:
        while not quit:
            _, _, quit = UBXtoRNX(fileno=i, waitTime=waitTime, epochInterval=epochInterval, outputPath=masterOutputPath)
            i += 1

            subprocess.run(["vcgencmd","get_throttled"])
            subprocess.run(["vcgencmd","measure_temp"])
            subprocess.run(["free","-h"])

            # If program is quit during UBXtoRNX, end while loop
            if quit:
                print("Quitting...")
                break

            print("Uploading RINEX and plots to AWS storage")
            try:
                aws_fileset = aws_upload(aws_fileset, masterOutputPath)
            except:
                print("Upload failed!")
            
    except KeyboardInterrupt:
        print("Keyboard Interrupt! Quitting...")

while True:
    opt1 = -1
    opt2 = -1
    print()
    print("What would you like to do?")
    print("\t1) Collect RINEX Data")
    print("\t2) AWS Download/Upload")
    print("\t3) Create GIF from RINEX files")
    print("\t4) Clear Files")
    print('\t5) Set output path ("." by default)')
    print("\t0) Quit")
    print()
    print("\t\t- ", end="")
    opt1 = input()
    try:
        opt1 = int(opt1)
    except:
        print("Invalid input. Try again.")
        continue
    match opt1:
        case 1:
            wait = "invalid"
            epochInt = "invalid"
            print()
            while wait == "invalid":
                print("Time between files?")
                print("\t- ", end="")
                wait = input()
                try:
                    wait = int(wait)
                except:
                    print("Invalid input. Try again.")
                    wait = "invalid"
                    continue

            while epochInt == "invalid":
                print("Epoch lengths?")
                print("\t- ", end="")
                epochInt = input()
                try:
                    epochInt = int(epochInt)
                except:
                    print("Invalid input. Try again.")
                    epochInt = "invalid"
                    continue
            
            collectRINEXdata(wait, epochInt)
        case 2:
            while opt2 != 0:
                print("Which action?")
                print("\t1) Download")
                print("\t2) Upload")
                print("\t0) Back")
                print()
                print("\t\t- ", end="")
                opt2 = input()
                try:
                    opt2 = int(opt2)
                except:
                    print("Invalid Input. Try again.")
                    continue
                match opt2:
                    case 1:
                        try:
                            aws_download(masterOutputPath)
                            print()
                        except:
                            print("Download failed! Check connection.")
                    case 2:
                        try:
                            aws_upload(masterOutputPath)
                            print()
                        except:
                            print("Download failed! Check connection.")
                    case 0:
                        break
                    case _:
                        print("Invalid Input. Try again.")
                        continue
        case 3:
            print()
            print("GIF conversion may take a while and use a good amount of RAM. Are you sure? y/n")
            print("\t- ", end="")
            contYes = input()
            if contYes in validYes:
                makeGIF(masterOutputPath)
        case 4:
            while opt2 != 0:
                show = False
                print("Clear files from which directories?")
                print("\t1) RNX_SUCCESS")
                print("\t2) NAV_SUCCESS")
                print("\t3) IMAGE_SUCCESS")
                print("\t4) GIF_SUCCESS")
                print("\t5) All of the above")
                print("\t0) Back")
                print()
                print("\t\t- ", end="")
                opt2 = input()
                try:
                    opt2 = int(opt2)
                except:
                    print("Invalid Input. Try again.")
                    continue

                dirs = []
                delPaths = ["RNX_SUCCESS", "NAV_SUCCESS", "IMAGE_SUCCESS", "GIF_SUCCESS"]
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
                        for path in delPaths:
                            dirs.append(path)
                    case 0:
                        break
                    case _:
                        print("Invalid Input. Try again.")
                        continue
                
                print()
                print("Show directory contents? y/n")
                print("\t- ", end="")
                showContents = input()
                if showContents in validYes:
                    show = True

                print("-=-=-=-")
                for dir in dirs:
                    if show:
                        for (root,dirs,files) in (os.walk(f"{masterOutputPath}/{dir}",topdown=True)):
                            for file in files:
                                print(f"{root}/{file}")

                    print()
                    print("Delete Files? y/n")
                    print("\t\t- ", end="")
                    delForReal = input()
                    if delForReal in validYes:
                        delFilesInDir(f"{masterOutputPath}/{dir}")
                    else:
                        print("Aborting File Deletion...")
                        continue         
        case 5:
            while True:
                print()
                print(f"Current output path: {masterOutputPath}")
                print("Change directory? y/n")
                print()
                print("\t\t- ", end="")
                change = input()
                if change not in validYes:
                    break

                print()
                print("Input new output directory.")
                print()
                print("\t\t- ", end="")
                newDir = input()
                if os.path.isdir(newDir) == False:
                    print("Invalid directory! Does not exist.")
                    continue
                else:
                    print("Output directory set!")
                    masterOutputPath = newDir

                    masterOutputFile = open("masterOutputPath.txt", "w", encoding="utf-8")
                    masterOutputFile.write(masterOutputPath)
                    masterOutputFile.close()
                    
                    makeOutputDirs(masterOutputPath)
                    break
        case 0:
            print()
            sys.exit()
        case _:
            print("Invalid Input. Try again.")

