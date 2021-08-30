#!/usr/bin/env python
import sys
import os
import os.path
import argparse
import subprocess
from multiprocessing import Pool
from time import sleep
import time
from jiwer import wer

CMD = '/usr/local/bin/docker exec {} deepspeech --model deepspeech-0.9.3-models.pbmm --scorer deepspeech-0.9.3-models.scorer --audio {}'

SAMPLE_CPU_CMD = '/usr/local/bin/docker stats --no-stream --format "{{.CPUPerc}}" '

ACTUAL_PATH='/Users/zhongcong/deepspeech/actual/'

COPY_CMD = '/usr/local/bin/docker cp {}:/DeepSpeech/{} {}'

#Store input argument
class Arguments:
    cid = None
    rep = None
    audios= {}
    mode = None
    accuracy = None
    cpuPeriod = None
    cpuCap = None
    def __init__(self, args):
        self.cid = args.cid
        if args.mode in ['seq', 'para']:
            self.mode = args.mode
        else:
            raise Exception('wrong mode {}'.format(args.mode))
        self.rep = int(args.reptition)
        if args.accuracy is not None:
            self.accuracy = float(args.accuracy)
        self.cpuPeriod = float(args.cpuPeriod)
        if args.cpuCap is not None:
            self.cpuCap = float(args.cpuCap)
        with open(args.audioSource, 'r') as source:
            lines = source.readlines()
            for line in lines:
                line = line.strip()
                wav, expected = line.split(',')
                if os.path.isfile(expected):
                    self.audios[wav] = expected
                else:
                    raise Exception('wrong input file: {}, {}'.format(wav, expected))
            
#Download audio file from docker container
def copyAudioFiles(cid, audioPath, audios):
    for wav in audios:
        cmd = COPY_CMD.format(cid, wav, audioPath)
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, text=True)
        process.communicate()[0]
        print('copied {}'.format(wav))

#Prepare docker command without repetition
def getCmdList(cid, audios, accuracy, dirPath):
    ret = []
    for wav in audios:
        ret.append([cid, wav, audios[wav], accuracy, dirPath])
    return ret

#Get cpu stats by input intervals
def sampleCPU(args):
    cid = args[0]
    period = args[1]
    dirPath = args[2]
    cpuCap = args[3]
    cmd = SAMPLE_CPU_CMD + cid
    procs = []
    while True:
        ct = time.time()
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, text=True)
        if procs:
            for p in procs:
                proc = p[0]
                startTime = p[1]
                if proc.poll() is not None:
                    out = proc.communicate()[0]
                    out = out[1:-2]
                    print(startTime, out)
                    with open('{}{}/cpu_sample.txt'.format(ACTUAL_PATH, dirPath), 'a') as sample:
                        sample.write('{} {}\n'.format(startTime,out))
                    procs.remove(p)
                else:
                    break
        procs.append([process, ct])
        sleep(period)

#run actual transcription per file
def runDocker(args):
    rep = args[0]
    cid = args[1]
    wav = args[2]
    exp = args[3]
    accuracyth = args[4]

    dirPath = args[5]
    cmd = CMD.format(cid, wav)
    startTime =time.time()
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    actual = process.communicate()[0].strip()
    endTime =time.time()
    with open(exp, 'r') as _:
        expected = _.readline().strip()
    error = wer(expected, actual)
    print(endTime, wav, accuracyth, 1.0 -error, endTime-startTime)
    with open('{}/{}/{}_{}_actual'.format(ACTUAL_PATH,dirPath,wav,rep), 'w') as _:
        _.write('{},{},{}\n{}'.format(startTime, endTime, 1.0 - error, actual))


def main():
    parser = argparse.ArgumentParser(description='Process inputs')
    parser.add_argument('-cid', dest='cid', action='store', help='container id')
    parser.add_argument('-audio', dest='audioSource', action='store', help = 'source of audio file names')
    parser.add_argument('-mode', dest='mode', action='store', help='sequential process of source audios or parallel')
    parser.add_argument('-rep', dest='reptition', action='store', help='how many times to repeat the source inputs')
    parser.add_argument('-accuracy', dest='accuracy', action='store', help='accuracy passing rate')
    parser.add_argument('-cpu', dest='cpuPeriod', action='store', help='CPU sample period')
    parser.add_argument('-cpucap', dest='cpuCap', action='store', help='CPU max rate to stop test')

    args = parser.parse_args()
    arguments = Arguments(args)

    #create test run folder
    dirPath = int(time.time())
    resultPath = '{}{}'.format(ACTUAL_PATH,dirPath)
    if not os.path.isdir(resultPath):
        os.mkdir(resultPath)
    print('created result path: {}'.format(resultPath))
    #Save command argument
    with open('{}/testCmd'.format(resultPath), 'w') as testCmd:
        testCmd.write('{}'.format(sys.argv))
    audioSourcePath = resultPath + '/audios'
    if not os.path.isdir(audioSourcePath):
        os.mkdir(audioSourcePath)
    #Copy audio files from docker container
    copyAudioFiles(arguments.cid, audioSourcePath + '/', arguments.audios)
    #Prepare docker command    
    origCmdList = getCmdList(arguments.cid, arguments.audios, arguments.accuracy, dirPath)
    cmdList = []
    for i in range(arguments.rep):
        for cmd in origCmdList:
            _=[i]
            _.extend(cmd)
            cmdList.append(_)
    #Define poolsize by parallal or sequential run
    poolSize = 1
    if arguments.mode == 'seq':
        poolSize += 1
    elif arguments.mode == 'para':
        poolSize += len(cmdList)
    #Actual transcription process
    with Pool(poolSize) as pool:
        sample_proc = pool.map_async(sampleCPU, [[arguments.cid, arguments.cpuPeriod, dirPath, arguments.cpuCap]])
        sleep(5)
        pool.map(runDocker, cmdList)
        sleep(5)

if __name__ == '__main__':
    main()

