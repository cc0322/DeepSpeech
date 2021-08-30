# DeepSpeech
Test Summary - DeepSpeech.pdf - Test report for all the test cases/test run

runv2.py - docker execute a deepspeech transcription by options
--help
usage: runv2.py [-h] [-cid CID] [-audio AUDIOSOURCE] [-mode MODE] [-rep REPTITION] [-accuracy ACCURACY] [-cpu CPUPERIOD]
                [-cpucap CPUCAP]

Process inputs

optional arguments:
  -h, --help          show this help message and exit
  -cid CID            container id
  -audio AUDIOSOURCE  source of audio file names
  -mode MODE          sequential process of source audios or parallel
  -rep REPTITION      how many times to repeat the source inputs
  -accuracy ACCURACY  accuracy passing rate
  -cpu CPUPERIOD      CPU sample period
  -cpucap CPUCAP      CPU max rate to stop test

result.py - When runv2.py finished, if the result is valid, run this file to generate test_result.csv and test_result_summary.csv for diagram and statistics data
--help
usage: result.py [-h] [-p PATH] [-r RATE] [-a]

Process inputs

optional arguments:
  -h, --help  show this help message and exit
  -p PATH     path of raw results
  -r RATE     Pass rate
  -a          Need overall results

actual folder - All the test run has its own folder by start timestamp in actual folder. Raw data and result.py result data are both in the test run folder.

expected folder - Expected transcription text by audio name.

source folder - Audio file list to be run by runv2.py

wer.py - third party jiwer for WER rate

Future work:
1. Send parameters by configuration file, eliminate abolute path
2. More error handling and documentation
3. Set timeout for each thread to avoid non-response process
and more to come
