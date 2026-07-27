# Relinex
### Tools for collecting and processing GNSS data from Sparkfun ZED-F9P chips
**Recommended to run on Linux, has not been fully tested on other OS!**

Once cloned, run "python3 master_doohickey.py" from the main directory to use.

## Collect RINEX Data
You will be prompted to set the COMPORT that the Sparkfun chip is connected to. It will be empty by default. The COMPORT will be consistent between executions.

Observation   - Generates a RINEX 3.05 format (.rnx) observation file.

Navigation    - Generates a RINEX 3.05 format (.rnx) navigation file.

OBS and NAV   - Generates both. (Recommended)

Site number is the number that represents which site you are currently collecting from. It is used to distinguish collection periods and sources. It can be set to any integer, but I recommend formatting site numbers like this:

\/ - Collection period 5
 5 2
   /\ - Collection location

So, this is the 5th time collecting data at the 2nd collection location. There are definitely better ways to format site number, but this is what I have used.

## Combine RINEX files

## Create PNG from RINEX file
You must already have a concatenated RINEX observation file to create a PNG from a site.

## Create GIF from RINEX files
You do not need to have a concatenated RINEX observation file to create a GIF. Files will be concatenated and deleted for each frame generated.

## Set output path
("." by default)

## AWS Download/Upload
You will be prompted to set the name of the AWS S3 bucket that will be uploaded to/downloaded from. It will be empty by default. The bucket name will be consistent between executions.

You must configure AWS on your device for your account before relinex can upload from/download to the output directory.
1) On the AWS website, https://(region).console.aws.amazon.com/console/home, search IAM and click the first option
2) From the IAM page, click on "Manage access keys"
3) Scroll down to "Access keys" and click "Create access key"
4) Save the access key and the secret access key as a .csv file, or write it down
5) In WSL, run aws configure
6) Fill in the access key, secret access key, the region name, and the output format (json)


## Clear Files
