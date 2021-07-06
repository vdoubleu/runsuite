import sys
import tempfile
import os
import pathlib
import subprocess


compileCommand = "g++ -Wall"


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorText(text, color):
    return color + str(text) + colors.ENDC

def parseArgs(args):
    helpText = "run it in two ways: \npython runsuite.py <testfolder> <programFiles...> (will auto compile for you)\npython runsuite.py -e <testfolder> <executable> (will try to run the executable file)" 

    if len(args) == 1:
        print("input more args: python runsuite.py <testFolder> <programFiles>")
        return None

    if "--help" in args or "-h" in args:
        print(helpText)
        return None

    if len(args) > 2:
        if "-e" in args:
            return {"testFolder": args[2], "executable": args[3]}
        else:
            return {"testFolder": args[1], "programFiles": args[2:]}
    else:
        return {"testFolder": args[1]}


if __name__ == "__main__":
    argRes = parseArgs(sys.argv)

    if argRes is None:
        sys.exit()

    testFiles = set(os.listdir(argRes["testFolder"]))

    execCommand = ""
    if "executable" in argRes:
        execCommand = argRes["executable"]
    elif "programFiles" in argRes:
        programFiles = argRes["programFiles"]
        compileAllOut = subprocess.Popen(compileCommand + " " + " ".join(programFiles), shell=True)
        compileAllOut.wait()

        if compileAllOut.returncode != 0:
            print("\n==Error Compiling Program==\n\n")
            sys.exit(1)
        else:
            print("\n==Successfully Compiled Program==\n\n")

        execCommand = "./a.out"

    testsCompleted = 0
    failedTests = 0
    for file in testFiles:
        testFailed = 0

        if file.endswith(".in"):
            fullFilePath = argRes["testFolder"] + "/" + file 
            tmpFile, tmpFilePath = tempfile.mkstemp()
            try:
                pathStem = pathlib.Path(file).stem 

                valgrindAllOut = subprocess.Popen("valgrind --leak-check=full --error-exitcode=1 {} <{} >{}".format(execCommand, fullFilePath, tmpFilePath), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                valgrindAllOut.wait()
                valCode = valgrindAllOut.returncode

                if valCode != 0:
                    valErr = valgrindAllOut.stderr.read().decode()
                    print("{} contains a memory leak.".format(colorText(pathStem, colors.FAIL)))
                    print(valErr)
                    testFailed = 1

                outFileName = pathStem + ".out"
                fullOutfileName = argRes["testFolder"] + "/" + outFileName

                if outFileName in testFiles:
                    diffAllOut = subprocess.Popen("diff {} {}".format(tmpFilePath, fullOutfileName), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    diffAllOut.wait()

                    diffCode = diffAllOut.returncode
                    if diffCode == 0:
                        print("{} has no differences!".format(colorText(pathStem, colors.OKGREEN)))
                    else:
                        print("{} failed with the following differences.".format(colorText(pathStem, colors.FAIL)))
                        diffOut = diffAllOut.stdout.read().decode()
                        print(diffOut)
                        testFailed = 1
            finally:
                os.remove(tmpFilePath)
            
            failedTests += testFailed
            testsCompleted += 1

    print("\n\n-------------------------------------------------------------------------\n")
    if failedTests == 0:
        print("All {} tests passed".format(testsCompleted))
        print("\n-------------------------------------------------------------------------")
    else:
        print("Test complete. Ran {} total tests with {} successful and {} failed."
                .format(
                    colorText(testsCompleted, colors.OKBLUE), 
                    colorText(testsCompleted - failedTests, colors.OKGREEN), 
                    colorText(failedTests, colors.FAIL))
                )
        print("\n-------------------------------------------------------------------------")
        sys.exit(-1)



