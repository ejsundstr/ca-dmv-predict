import argparse
import datetime
import time

import numpy as np
import pandas as pd

#In this folder
import scrape
import update_offices as upoff
import office_hours as oh

#Selenium attempt
from selenium import webdriver


strDesc='Makes and tetrahedron symmetric dissociation curve!'
parser=argparse.ArgumentParser(description=strDesc)
parser.add_argument('-s', '--save', action="store_true", help='Save the specific office as office.csv.')
parser.add_argument('-i', '--input', type=str, default='waitTime.csv', help='For an alternative csv file')
#parser.add_argument('-f', '--final', type=float, default=5.00000000, help='Specify the ending distance for the curve. Default: 5.0')
 
args = parser.parse_args()


#Create the two data frames
temp_name = upoff.update_offices()[1]
appt_df = pd.DataFrame(index=[datetime.datetime.now()], columns=list(temp_name.keys()),dtype=int)
non_df = pd.DataFrame(index=[datetime.datetime.now()], columns=list(temp_name.keys()),dtype=int)
temp_name = False

by_id = False 

driver = webdriver.PhantomJS()
driver.set_window_size(50, 50)

new_week = True

invfrequency = 30
secs_to_sleep = 0 
while True:
  if(new_week):
    if appt_df.shape[0] != 0:
      date_string = datetime.datetime.now().strftime('%Y-%m-%d') 
      appt_df.to_hdf('appt-'+date_string+'.hdf','table',mode='w')
      non_df.to_hdf('non-'+date_string+'.hdf','table',mode='w')
    #Obtain office data 
    by_id, by_name, update  = upoff.update_offices(by_id)
    wkdy_open,wkdy_close = oh.open_close(by_id)
    new_week = False
  
  curdt = datetime.datetime.now()
  day = curdt.weekday()
  curtime = curdt.time()
  #Are any offices open???
  if wkdy_open[day] < curtime  and curtime < wkdy_close[day]:
    appt = np.full(len(appt_df.columns),np.nan) 
    non =  np.full(len(non_df.columns),np.nan)
    init = time.time()
    #Collect Data
    for i,o in enumerate(appt_df.columns):
      if oh.is_open(by_name[o],curdt) and by_name[o]['cQueue']:
        oappt, onon = scrape.wait_times(driver,by_name[o]['number'])
        appt[i] = oappt
        non[i] = onon
    appt_df.loc[curdt] = appt
    non_df.loc[curdt] = non
    secs_to_sleep = invfrequency
  else:
    #Calculate sleep timer
    if curtime < wkdy_open[day]: #nothing open yet
      #When are they open?
      secs_to_sleep = (wkdy_open[day].hour-curtime.hour)*3600+(wkdy_open[day].minute-curtime.minute)*60
    elif wkdy_close[day] < curtime: # they are all closed
      #When are they open again? (more complicated)
      to_midnight = 0
      if curtime.minute > 0:
        to_midnight = (23-curtime.hour)*3600+(60-curtime.minute)*60 
      else:
        to_midnight = (24-curtime.hour)*3600
      if day != 6:
        next_day = day+1 
      else:
        new_week = True
        next_day = 0
      
      #this will also skip most of Sunday!
      to_open = (wkdy_open[next_day].hour)*3600+(wkdy_open[next_day].minute)*60
      secs_to_sleep = to_open+to_midnight
    #Minus a couple minutes for good measure
    secs_to_sleep -= 120
  
  if secs_to_sleep < 1:
    time.sleep(invfrequency)
  else:
    time.sleep(secs_to_sleep)
