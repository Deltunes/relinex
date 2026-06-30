import subprocess

cmdstr = "aws s3 cp s3://leaflink-rinex-doohickey/unique/RNX_SUCCESS/rinex/ ./RNX_SUCCESS/rinex/ --recursive"
subprocess.run(cmdstr.split(" "))
cmdstr = "aws s3 cp s3://leaflink-rinex-doohickey/unique/RNX_SUCCESS/azielev/ ./RNX_SUCCESS/azielev/ --recursive"
subprocess.run(cmdstr.split(" "))
