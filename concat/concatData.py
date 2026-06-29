import subprocess

rnxFilepath1 = "concat/success16.rnx"
rnxFilepath2 = "concat/success17.rnx"
azielevFilepath1 = "concat/azimuth&elevation16.txt"
azielevFilepath2 = "concat/azimuth&elevation17.txt"

rnxFilename1 = rnxFilepath1.split("/")[-1].split(".")[0]
rnxFilename2 = rnxFilepath2.split("/")[-1].split(".")[0]

subprocess.run(["./concat/gfzrnx", "-finp", f"{rnxFilepath1}", f"{rnxFilepath2}", "-fout", f"concat/{rnxFilename1}.rnx"])

azielevFile1 = open(azielevFilepath1, "r", encoding="utf-8")


azielevFile2 = open(azielevFilepath2, "r", encoding="utf-8")
