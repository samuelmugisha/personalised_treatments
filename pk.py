# Patient plasma drug concentration profile and bleed pattern visualization 
# At the moment we use a single-compartment model, where the drug is considered
# to be distributed instantaniously into a unique compartment in the body (plasma), characterized
# by a volume of distribution equal to 3.2l (the typical amount of plasma in human body). 
# Samuel Mugisha, University of Manchester, 2018


import pyodbc
import pandas as pd
import datetime
import math
import matplotlib.pyplot as plt
import matplotlib.dates as md
import os
import time
                                             
# Connects to DB and returns a cursor for parsing the rows
def connectDB(ConnectionString = "DRIVER={ODBC Driver 13 for SQL Server};SERVER=.\MYSERVER;Trusted_Connection=yes;Database=Haemtrack"):
    conn = pyodbc.connect(ConnectionString)
    cursor = conn.cursor()
    return cursor, conn
    
# Here we query patient data
def queryPatientData(cursor, dateFrom, dateTo, patientID):
    cursor.execute("select * from [haemtrack].[dbo].[Treatments] LEFT JOIN [haemtrack].[dbo].[BleedDetails] ON [haemtrack].[dbo].[Treatments].TreatmentID = [haemtrack].[dbo].[BleedDetails].TreatmentID where TreatedDate >"+str(dateFrom) +"AND TreatedDate < "+str(dateTo)  +" AND PatientID = "+str(patientID)+ " order by PatientID, TreatedDate")
    return cursor

# Here we update the PKFigures table with new image
def updatePKTable(cursor, patientID, dateFrom, dateTo, outputPath, threshold):
    sqlString =  "INSERT INTO [haemtrack].[dbo].[PKFigures] (PatientID, DateFrom, DateTo, Figure, HalfLife, VOD, TimeStamp, Threshold) VALUES ("+str(patientID) +",'"+datetime.datetime.strptime(dateFrom.replace("'", ''),'%b %d, %Y').strftime('%Y%m%d')+"','" +datetime.datetime.strptime(dateTo.replace("'", ''),'%b %d, %Y').strftime('%Y%m%d')+ "',(Select BulkColumn  from Openrowset(Bulk " +repr(str(outputPath))+ ", Single_Blob) as img)," +str(halfLife)+ "," +str(VOD)+ ",'"+ time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"'," +str(threshold)  +")"            
    print(sqlString)
    cursor.execute(sqlString)    
    return cursor

# Functions that transform numbers to strings. These strings should be collected from DB in the future
def causeBleed(cause):
    switcher = {
        0: "Spontaneous",
        1: "Trauma/Activity",
        2: "Surgery/Dental",
    }
    return switcher.get(cause, "nothing")
    
def severityBleed(severity):
    switcher = {
        0: "Minor(not so bad)",
        1: "Major(very bad)",
        2: "Life or Limb threatening",
    }
    return switcher.get(severity, "nothing")    

def treatmentReason(reason):
    switcher = {
        1: "New Bleed",
        2: "FollowUp Bleed",
        3: "Prescribed treatment",
        4: "Routine Prophylaxis",
        5: "Surgery",
        6: "Activity",
        7: "Physiotherapy",
        8: "Immune Tolerance",
        9: "Other",
    }
    return switcher.get(reason, "nothing")   
    
# We get Treatment and Bleed data into Python Structures. We return a Treatment Series and a Bleeds dictionary 
def fillTS(cursor, dateFrom, dateTo):
    rangeFrom = datetime.datetime.strptime(dateFrom[1:-1], '%b %d, %Y')
    rangeTo = datetime.datetime.strptime(dateTo[1:-1], '%b %d, %Y')
    rangeTS=pd.date_range(rangeFrom, rangeTo, freq="5min")
    treatments = pd.Series(data=0, index=rangeTS)
    bleeds = {}
    treatmentReasons = {}
    while 1:
        row = cursor.fetchone()
        if not row:break
        dt=datetime.datetime.combine(row.TreatedDate, datetime.datetime.strptime(row.TreatedTime, '%H:%M %p').time())
        r=divmod(dt.minute,5)[1]
        if (r != 0 ):
            # we have a time series of 5min frequency and we enter this branch if the time of the treatment
            # is not divisible with 5. E.g. Treatment at time 13:06 is approximated with 13:10. 
            if (r < 2.5): 
                dt= dt - datetime.timedelta(minutes=r)
            else:
                dt = dt + datetime.timedelta(minutes=(5-r))
        #print(dt)
        treatments[dt] = row.TotalUnits
        if not row.Location is None:
            bleeds[dt] = [row.Location, row.BleedCause, row.BleedSeverity, row.TimeAfterBleed]
        if not row.Reason is None:
            treatmentReasons[dt] = row.Reason
    return treatments, bleeds, treatmentReasons
    
#We transform the Treatment time series into PK series knowing the half life and the volume of distribution
def generatePK(ts, halfLife):
    tenhalflives = (10* 60* halfLife)
    ke =  math.log(2)/(halfLife * 60)  #constant of excretion computed using halflife
    for t in ts[ts>0].index:
        for i in range(5,tenhalflives,5):
           if( (t + datetime.timedelta(minutes=i)) <= ts.index[-1] ):
              if (ts[t +  datetime.timedelta(minutes=i) ]==0):
                  ts[t +  datetime.timedelta(minutes=i) ] = ts[t] * math.pow(2.718,-ke*i)
              else:
                   ts[t +  datetime.timedelta(minutes=i) ] = ts[t +  datetime.timedelta(minutes=i) ]+ ts[(t +  datetime.timedelta(minutes=i)) -  datetime.timedelta(minutes=5) ]
                   break;
    return ts 
    
    

# Compute time above/below a specified treshold as percentage 
def aboveBelow(ts, threshold):
     above = 0
     below = 0
     for i in ts.index:
         if (ts[i]>threshold): above=above+1
         else: below=below+1
     return above/(above+below), below/(above+below)

#  We plot the time series data showing the bleed details as well
def plotTs(ts, threshold, patientID, bleeds, treatmentReasons, halfLife, VOD):
    plt.ioff()
    legend=[]
    plt.figure(figsize=(20,10))
    plt.plot(ts.T/VOD, color="orange", linewidth=2.0)
    plt.title("Patient ID="+str(patientID) + " PK profile from "+  str(ts.index[0].date()) + " to "+ str(ts.index[-1].date()) + "; Half-Life= "+str(halfLife) + " Volume of Distribution= "+str(VOD)+"dL" , color= "black")
    print(ts['22/03/2015 01:10:00' :'22/03/2015 02:20:00'].to_string())
    ax = plt.gca()
    xfmt = md.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_formatter(xfmt)
    ymin, ymax = ax.get_ylim()
    for key, value in bleeds.items() :
        ax.vlines(x=key, ymin=ymin, ymax=ymax-(ymax*0.2) ,color='r', linestyles="solid", linewidth=5)
        text= value[0].replace(" ", "") + ","  + causeBleed(value[1]) + "," + severityBleed(value[2])
        timeAtBleed = key - datetime.timedelta(minutes= round(value[3] / 5, 1))
        ax.annotate(text, xy=(timeAtBleed-datetime.timedelta(minutes=500),ymax-(ymax*0.2)), horizontalalignment="left",  rotation=90 )
    for key, value in treatmentReasons.items() :
        text=  treatmentReason(value)  
        ax.annotate(text, xy=(key,ts[key]/VOD-40), horizontalalignment="left",  rotation=90)
        ax.annotate(str(ts[key]-ts[key - datetime.timedelta(minutes=5)])+" IUs", xy=(key, ts.T[key]/VOD+5), horizontalalignment="center", verticalalignment="top")
    ax.hlines(xmin=ts.index[0], xmax=ts.index[-1] , y=threshold, color="blue")
    above, below = aboveBelow(ts/VOD, threshold) 
    legend.append(str(round(above,2)) + " %Above, " + str(round(below,2))+" %Below, "+ "Threshold: "+ str(threshold))
    plt.legend(legend)  
    ax.set_ylabel('Factor VIII IU/dl')
    return plt

def showFigure(cursor, dateFrom = "'Mar 15, 2016'" , dateTo="'Apr 15, 2016'", patientID=105, threshold=50 , halfLife=10, VOD=32, outputPath="local.jpg"):
    cursor = queryPatientData(cursor, dateFrom=dateFrom, dateTo=dateTo, patientID=patientID)
    ts, bleeds, treatmentReasons = fillTS(cursor,dateFrom, dateTo)
    ts= generatePK(ts, halfLife)
    plt = plotTs(ts, threshold, patientID, bleeds, treatmentReasons,halfLife, VOD)
    return plt
 
# Save image to db
def saveToDB(cursor, patientID, dateFrom, dateTo, halfLife, VOD, outputPath, threshold):
     updatePKTable(cursor, patientID, dateFrom, dateTo, outputPath, threshold)
     return
     
    


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-dateFrom', help='Date From',required=True)
parser.add_argument('-dateTo',help='Date To', required=True)
parser.add_argument('-patientID',help='Patient ID', required=True)
parser.add_argument('-threshold',help='Threshold horizontal line', required=True)
parser.add_argument('-VOD',help='Volume of distribution', required=True)
parser.add_argument('-halfLife',help='Half Life', required=True)
parser.add_argument('-connectionString',help='DB connection string', required=True)
parser.add_argument('-outputPath',help='Where to save image', required=True)
args = parser.parse_args()


dateFrom=args.dateFrom
dateTo =args.dateTo

print(dateFrom)
print(dateTo)
patientID=args.patientID
threshold=int(args.threshold)
halfLife=int(args.halfLife)
VOD=int(args.VOD)
connectionString=args.connectionString
outputPath =  args.outputPath.replace("\"","") + "\\"+ datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S') + ".jpg"
print(outputPath)
cursor,conn = connectDB(connectionString)
plot = showFigure(cursor, dateFrom, dateTo, patientID, threshold, halfLife, VOD, outputPath)
#save file
plot.savefig(outputPath, format='jpg')   
#save db
saveToDB(cursor, patientID, dateFrom, dateTo, halfLife, VOD, outputPath, threshold) 
conn.commit()   
conn.close()
#os.remove(outputPath)




