#!/usr/bin/env python
import sys
import os
import os.path
import argparse
import logging
import subprocess
from multiprocessing import Pool
from time import sleep
import time
import datetime
from jiwer import wer


ACTUAL_PATH='/Users/zhongcong/deepspeech/actual/'

#Define per audio file result
class Result:
    start = None
    end = None
    pTime = None
    accuracy = None
    size = None
    cpu = None
    def __str__(self):
        return '%s, %s, %s, %s, %s,'%(self.start, self.end, self.accuracy, self.size, self.cpu)

#Get average cpu utliziation by timestamp
def getCpu(start, end, cpuStats):
    cpu = []
    for c in cpuStats:
        t, _ = c.split()
        t = float(t)
        rate = float(_[:-1])
        if t < start or t > end:
            continue
        if rate < 0.000001:
            continue
        cpu.append([t, rate])
    total = 0.0
    for c in cpu:
        total += c[1]
    return total/len(cpu)

#Process single actual result file
def processOne(path, name, rate, cpuStats):
    wavName, rep, _ = name.split('_')
    ret = Result()
    ret.size = os.path.getsize(path + 'audios/'+ wavName)
    with open(path+name, 'r') as result:
        start, end, accuracy = result.readline().split(',')
    
    ret.start = float(start)
    ret.end = float(end)
    ret.pTime = ret.end - ret.start
    ret.accuracy = float(accuracy)
    ret.cpu = getCpu(ret.start, ret.end, cpuStats)
    isPass = True if ret.accuracy > float(rate) else False
    with open('{}test_result.csv'.format(path), 'a') as csv:
        csv.write('{},{},{},{},{},{},{},{}\n'.format(wavName,ret.size,rep,ret.cpu,ret.pTime,rate,ret.accuracy, isPass))

    return ret

#Generate full test summary
def processSummary(path, results, cpuStats):
    pTime = sum( r.pTime for r in results) / len(results)
    accuracy = sum( r.accuracy for r in results) / len(results)
    start = min(r.start for r in results)
    end = max(r.end for r in results)
    cpu = getCpu(start, end, cpuStats)
    print(pTime, accuracy, cpu)

    #Check if any audio isn't processed
    cmd = []
    with open('{}testCmd'.format(path), 'r') as _:
        line = _.readline().replace('[', '').replace(']', '').replace(' ', '').replace('\'', '')
        cmd = line.split(',')

    rep = None
    for c in cmd:
        if c == '-rep':
            rep = int(cmd[cmd.index(c) + 1])

    print(rep)

    missing = []

    for wav in os.listdir(path+'audios/'):
        if os.path.isfile('{}audios/{}'.format(path, wav)):
            for r in range(rep):
                actual = '{}{}_{}_actual'.format(path, wav, r)
                if not os.path.isfile(actual):
                    missing.append(actual)
        else:
            raise Exception('cannot load audio file: {}'.format(wav))

    if missing:
        print('missing result for: {}'.format(missing))

    #Write summary file: average cpu utilization, average processting time and average accuracy
    with open('{}test_result_summary.csv'.format(path), 'a') as csv:
        csv.write('{},{},{}\n'.format(cpu,pTime,accuracy))

def main():
    parser = argparse.ArgumentParser(description='Process inputs')
    parser.add_argument('-p', dest='path', action='store', help='path of raw results')
    parser.add_argument('-r', dest='rate', action='store', help='Pass rate')
    parser.add_argument('-a', dest='all', action='store_true', help='Need overall results')

    args = parser.parse_args()

    cpuResult = '{}cpu_sample.txt'.format(args.path)
    if not os.path.isfile(cpuResult):
        raise Exception('{} missing cpu_sample.txt'.format(args.path))

    cpuStats = []
    with open(cpuResult, 'r') as cpu:
        for l in cpu.readlines():
            cpuStats.append(l.strip())

    audioResultNames = []
    for f in os.listdir(args.path):
        file = args.path + f
        if not os.path.isfile(file):
            continue
        if 'actual' not in f:
            continue
        audioResultNames.append(f)

    results = []

    with open('{}test_result.csv'.format(args.path), 'a') as csv:
        csv.write('audioName,size,repetition,cpu,process_time,expected_accuracy,actual_accuracy,is_pass\n')
    for name in audioResultNames:
        ret = processOne(args.path, name, args.rate, cpuStats)
        results.append(ret)

    if args.all:
        with open('{}test_result_summary.csv'.format(args.path), 'a') as csv:
            csv.write('cpu, process_time,accuracy\n')
        processSummary(args.path, results, cpuStats)

    return


if __name__ == '__main__':
    main()

