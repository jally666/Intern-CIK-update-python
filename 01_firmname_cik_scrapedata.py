
import time
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from pandas import ExcelWriter
import re
import os
import string

#####################
# Step I: read data
#####################
#User enters the file location information
#s = raw_input('Input the file location ->')
#s2 = raw_input('Input the file name ->')
#s3 = raw_input('Input the save file name ->')
s="P:\PCAOB Staff\Interns\zhangy1\NAF\\test"
s2="test.xlsx"
s3="output1.xlsx"


#Start a timer for how long it takes to run the code
start_time = time.time()
#For the main file path, one needs to make sure they are forward slashes
s = string.replace(s, "\\", '/')

# Combining the main folder location and the xlsx file that has the list of ciks
main_location = s + '/' + s2
#main_location = "P:/PCAOB Staff/Interns/zhangy1/NAF/test/test.xlsx"
# Combining the temporary csv files for the different results with the folder location
results = s + '/' + s3
#results="P:/PCAOB Staff/Interns/zhangy1/NAF/test/output.xlsx"

#Pandas reading in the main list of firmnames
in_file = pd.read_excel(main_location)
IssuerName = in_file['IssuerName'].tolist() #transfer from df to list
IssuerName = [str(IssuerName[x]) for x in range(len(IssuerName))]  # transfer from unicode to ascii
#IssuerName = [IssuerName[x].encode('ascii','ignore') for x in range(len(IssuerName))]


#############################################
# STep II : create a new variable "issuer" 
#			and Clean the data 
#############################################
# create a new column issuer which is preprocessed IssuerName
IssuerName = [IssuerName[i].upper() for i in range(len(IssuerName))]
issuer=IssuerName

#this function is to remove keywords and strings after keywords
def remove(stri, keyword):
	if keyword in stri:
		if (len(keyword)+stri.find(keyword))==len(stri):
			return stri[:stri.find(keyword)]
		else:
			if stri[len(keyword)+stri.find(keyword)]==" ":
				return stri[:stri.find(keyword)]
			else:
				return stri
	else:
		return stri
		

# this function is to remove punctuations
def remove_punctuation(s):
    s = ''.join([i for i in s if i not in frozenset(string.punctuation)])
    return s

	
# remove useless labels	
issuer = filter(None, issuer) # remove missing data	
issuer=[remove(issuer[i]," LLC") for i in range(len(issuer))]
issuer=[remove(issuer[i]," INCORPORATION") for i in range(len(issuer))]
issuer=[remove(issuer[i]," INC") for i in range(len(issuer))]
issuer=[remove(issuer[i]," CORPORATION") for i in range(len(issuer))]
issuer=[remove(issuer[i]," CORP") for i in range(len(issuer))]
issuer=[remove(issuer[i]," COMPANY") for i in range(len(issuer))]
#issuer=[remove(issuer[i]," FUND") for i in range(len(issuer))] # I think I should not delete FUND and LP
issuer=[remove(issuer[i]," LTD") for i in range(len(issuer))]
# remove parentheses' strings
issuer=[re.sub(r'\(.*\)', '', issuer[i]) for i in range(len(issuer))]
#remove punctuations
issuer=[remove_punctuation(issuer[i]) for i in range(len(issuer))]
issuer = filter(None, issuer)  # remove missing data, just in case



#################################################
# Step III : Scrape CIK COMPANY STATE from SIC 
#			 and Filter out unmatched IssuerNames
#################################################

#Empty dataframes where different reuslts will be stored
wrong_issuer = pd.DataFrame()
results_df = pd.DataFrame()

# Loop keeps track of how many 500 iterations have passed
# Time2 keeps track of how many iterations have happenned

loop = 1
time2 = 0
with requests.Session() as s:
    s.get('https://www.sec.gov/')
	
#Start of the loop, i is the issuer for each row in the 'issuer' list
for i in issuer:
	print i
	index=issuer.index(i)
	progress = round((float(time2) / len(issuer)) * 100)
	if progress % 5==0:
		print "\n %d Percent Done" % (progress)
	time2 = time2 + 1
	#if issuer is too short, we won't run it, because it's too time-consuming
	if len(i) >= 2:  
		start=0
		# start of loop, from start=0 up to "No matching companies"
		while True: 
			CIK=[]
			COMPANY=[]
			STATE=[]
			#Main  header middle and footer which never changes
			header = 'https://www.sec.gov/cgi-bin/browse-edgar?company='
			middle = '&owner=include&match=contains&start='
			footer ='&count=40&hidefilings=0'
			#create url to parse through  header + issuer + middle + start number + fotter
			url = header + str(i) + middle + str(start)+ footer
			#r here is the url that we quieried
			r = s.get(url)
			#soup is an html tree where we took the content of r and put it in the html tree. IF you look up a given link, it should be the same html tree that you would see on that page
			soup = bs(r.content,'html.parser')
			#First think is to check if the issuer is a real company, thus we search the soup for the phase
			no_issuer =soup.find(text=re.compile("No matching companies"))
			if no_issuer==u'No matching companies.':
				break
			else:
				# scenario 1: the keyword directly relate to one specific company
				matches = soup.find(text=re.compile("Companies with names matching"))
				if pd.isnull(matches):
					try:
						r_cik=soup.find("div",{"id":"contentDiv"}).find("span",{"class":"companyName"}).find('a').string.strip().encode('ascii','ignore')
						r_company=soup.find("div",{"id":"contentDiv"}).find("span",{"class":"companyName"}).contents[0].encode('ascii','ignore')
						r_state=" "
						CIK.append(r_cik)
						COMPANY.append(r_company)
						STATE.append(r_state)
					except:
						pass
				# scenario 2 : find all ciks that contain this key word
				else:
					try:
						table = soup.find_all('table')
						rows=table[0].find_all('tr')
						for tr in rows[1:]:
							cols=tr.find_all('td')
							r_cik=cols[0].find('a').string.strip().encode('ascii','ignore')
							r_company=cols[1].contents[0].string.strip().encode('ascii','ignore')
							r_state=cols[2].string.strip().encode("ascii",'ignore')
							CIK.append(r_cik)
							COMPANY.append(r_company)
							STATE.append(r_state)
					except:
						pass	
				columns={'IssuerName':IssuerName[index],'issuer':i,'CIK':CIK,'COMPANY':COMPANY,'STATE':STATE}
				df=pd.DataFrame(columns)
				results_df=results_df.append(df)
				results_df= results_df.reset_index(drop=True) # here you need to reset index for later drop
				# scenario 3: this issuer has too many CIKs, too time-consuming
				if start > 400:  # you can change the number here to tolerate more name input
					results_df=results_df.drop(results_df[results_df.issuer==i].index)
					break
				else:
					start = start + 40
				
	# find the "outliars", some of them are no matching companies, others are too many ciks
	if i not in results_df["issuer"].tolist():
		col={'IssuerName':IssuerName[index],'issuer':i}
		df2=pd.DataFrame(col,index=[0])
		wrong_issuer=wrong_issuer.append(df2)

print "\n %d issuers is problematic" %(len(wrong_issuer)) 		
writer = ExcelWriter(results)
results_df.to_excel(writer,'Possible Companies',index=False)
wrong_issuer.to_excel(writer,'Wrong IssuerName',index=False)
writer.save()


		
	
	
	


	
