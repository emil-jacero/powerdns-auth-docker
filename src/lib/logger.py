#!/usr/bin/env python3

import logging

def create_logger(name="default_logger"):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)7s - [%(funcName)s] %(message)s')

    # Create Streamhandler, outputting to stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    #log.info("Start logging!")
    return log
