#!/bin/bash

rm data/*
python3 crawler.py
bundle exec jekyll serve