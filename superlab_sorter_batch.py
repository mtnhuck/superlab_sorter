import os
import glob
import pandas as pd
import numpy as np
import math
import operator
from datetime import datetime

def superlab_sorter(filename):
    print('Processing '+filename)
    # given filename pull SID, study name, date and time
    with open(filename) as f:
        mylist = f.read().splitlines()

    subject=mylist[0]
    study=mylist[1]
    [date,time]=mylist[2].split("\t")
    del mylist
    #load file as pandas skipping first few rows for a clean import
    superlabdf=pd.read_csv(filename,sep='\t',skiprows=5)
    superlabdf['changed'] = superlabdf['Name.2'].ne(superlabdf['Name.2'].shift().bfill()).astype(int)
    #superlabdf.head(5)
    #need to setup event correctly since superlab doesn't make a unique event #
    superlabdf.loc[0, 'event']=0
    for i in range(1, len(superlabdf)):
        superlabdf.loc[i, 'event'] = superlabdf.loc[i-1, 'event'] + superlabdf.loc[i, 'changed']
    #superlabdf['event'].head(20)
    #separate into triggers and key presses
    triggerdf=superlabdf.loc[superlabdf['Key.1'] == 5]
    triggerdf=triggerdf.reset_index(drop=True) #reset index in case someone pressed a button before first trigger
    keypresses=superlabdf.loc[superlabdf['Key.1'].isin([1,2,3,4])]
    firsttrigger=triggerdf['Time'][0]
    print('First trigger at '+str(firsttrigger)+', subtracting this value from the rest of the cumulative times')
    pd.options.mode.chained_assignment = None  # default='warn'
    triggerdf['Time'] = triggerdf['Time']-firsttrigger
    keypresses['Time'] = keypresses['Time']-firsttrigger

    keypresses[keypresses.Time<0]
    keypresses=keypresses.reset_index(drop=True) #reset index in case someone pressed a button before first trigger


    #triggerdf['Name.2'].head(5)
    #triggerdf['Time'].tail(10)

    #for each trial pull the time that it actually started at from trigger above
    triggerdf['onset']=triggerdf['Time'].shift(periods=1)
    #this retains instructions screen, which is fine
    triggerdf['onset'][0]=-9999
    #identifies when a shift happened in trial
    triggerdf['changed'] = triggerdf['event'].ne(triggerdf['event'].shift().bfill()).astype(int)
    #select only times where what was presented on screen changed
    triggeruniquedf=triggerdf.loc[triggerdf['changed'] == 1].reset_index(drop=True)

    #are there any duplicate key presses within a trial?
    try:
        pd.concat(g for _, g in keypresses.groupby("event") if len(g) > 1)
        print("Please take a look at these particular responses and rerun this script")
    except ValueError:
        print("No duplicate button presses!")



    #get rid of extraneous columns
    triggeruniquedf = triggeruniquedf[['Name','Name.1','Name.2','Name.3','event','onset']]
    keypresses=keypresses[['Name.3','event','Key.1','Time.1']]
    #identify quick responses
    print('Printing quick subject responses below')
    print(keypresses[keypresses['Time.1']<500])

    #merge presentation and responses now that keypresses have been dealt with
    mergedf=pd.merge(triggeruniquedf, keypresses, how='outer', on='event')
    mergedf['subject']=subject
    mergedf['study']=study
    mergedf['date']=date
    mergedf['start_time']=time

    #write a modified file
    print('Writing output to '+'SuperlabSorter'+filename[:-4]+'.csv')
    mergedf.to_csv('SuperlabSorter'+filename[:-4]+'.csv')

for infile in glob.glob('*.txt'):
    print("current file is: " + infile)
    superlab_sorter(infile)
