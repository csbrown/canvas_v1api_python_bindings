import requests
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import local_models.local_models as pylomo
import sklearn.linear_model
import joblib
import numpy as np
import scipy.stats
import os
import collections
import functools
from canvas_api import *

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--course_id", type=str, default="636288")
    args = parser.parse_args()

    gradebook = get_gradebook(args.course_id)
    print(gradebook)
