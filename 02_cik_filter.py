import requests
from pandas import ExcelWriter
from bs4 import BeautifulSoup as bs
import re
import os
import string
import pandas as pd
import numpy 
import time

####################################################
# Step I: read data and append two dataset together
####################################################

#User enters the file location information
#s = raw_input('Input the file location ->')
#s2 = raw_input('Input the file name ->')
#s3 = raw_input('Input the save file name ->')
s="P:\PCAOB Staff\Interns\zhangy1\NAF\\test"
s2="output1.xlsx"
s2_1="output1_1.xlsx"
s3="output2.xlsx"


#For the main file path, one needs to make sure they are forward slashes
s = string.replace(s, "\\", '/')

# Combining the main folder location and the xlsx file that has the list of issuernames
main_location = s + '/' + s2
main_location1= s + '/' + s2_1
#main_location = "P:/PCAOB Staff/Interns/zhangy1/NAF/test/output.xlsx"
start_time = time.time()

# Combining the temporary csv files for the different results with the folder location
results = s + '/' + s3

# set the criteria of filing list, if CIK has one of this, we keep it
filing=['10-K', '20-F', '10KSB', 'S-1','40-F', 'S-4', '1-F']

in_file = pd.read_excel(main_location)
in_file1= pd.read_excel(main_location1)
in_file = in_file.append(in_file1)
in_file=in_file.reset_index(drop=True) #it's very important, for future drop data

in_file['CIK'] = in_file["CIK"].str[0:10] #clean CIK

#create formerly name 
in_file["FormlyName0"]=""
in_file["FormlyName1"]=""
in_file["FormlyName2"]=""
in_file["FormlyName3"]=""
in_file["FormlyName4"]=""

CIK = in_file['CIK'].tolist()
CIK = [str(CIK[x]) for x in range(len(CIK))]  


################################################
# Step II: check CIKs and filter out invalid ones
#			and scrape available formerly names			
################################################
with requests.Session() as s:
    s.get('https://www.sec.gov/')

results_df = pd.DataFrame()

for i in range(len(CIK)):
	progress = round((float(i) / len(CIK)) * 100)
	if progress % 5==0:
		print "\n %d Percent Done" % (progress)
	#Criteria 1: the number of items. 
	header="https://www.sec.gov/cgi-bin/browse-edgar?CIK="
	footer="&owner=exclude&action=getcompany"
	url=header + CIK[i] +footer
	r = s.get(url)
	#soup is an html tree where we took the content of r and put it in the html tree.
	soup = bs(r.content,'html.parser')
	table=soup.find("table",{"class":"tableFile2"})
	row= table.find_all("tr")
	ident= soup.find("p",{"class":"identInfo"})
	#scrape the all formerly name
	formerly=ident.find_all(text=re.compile("formerly:")) 
	for j in range(len(formerly)):
		in_file["FormlyName"+str(j)][i]=formerly[j].string.strip().encode('ascii','ignore')
	if len(row)<10:			# check if the number of item less than 10, if so we drop this row
		in_file["CIK"][i]= numpy.nan
		continue
	else:
		#Criteria 2 :if CIK contain our aim filings
		header1='https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='
		middle='&type='
		footer1='&dateb=&owner=exclude&count=40'
		flag=len(filing)
		for j in filing:	
			url1=header1 + CIK[i] + middle + str(j) + footer1
			r1 = s.get(url1)
			soup1 = bs(r1.content,'html.parser')
			table=soup1.find("table",{"class":"tableFile2"})
			row= table.find_all("tr")
			if len(row)>1:
				break
			else:
				flag=flag-1
		if flag == 0:
			in_file["CIK"][i]= numpy.nan

			

results_df=in_file.dropna(subset=["CIK"])

# remove parentheses' strings
def remove_parenthese(s):
	return re.sub(r'\(.*\)', '', str(s))

# clean the FormlyNames
def remove_fomerly(s):
	return str(s).replace("formerly:","").strip()
# remove parentheses' strings

for i in range(5):
	results_df["FormlyName"+str(i)]=results_df["FormlyName"+str(i)].apply(remove_parenthese)
	results_df["FormlyName"+str(i)]=results_df["FormlyName"+str(i)].apply(remove_fomerly)


# write the result into excel	
writer = ExcelWriter(results)
results_df.to_excel(writer,'filtered',index=False)
writer.save()

print "\n For %d CIKs it took"  % (x), time.time() - start_time, "seconds to find the filings"
























