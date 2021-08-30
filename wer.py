#!/usr/bin/env python

from jiwer import wer

hypothesis = "he has he must hurry you must stay on the path"
ground_truth = "razu you must hurry you must stay the path"

error = wer(ground_truth, hypothesis)
print(error)
