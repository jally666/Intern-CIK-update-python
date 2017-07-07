
import requests
from pandas import ExcelWriter
import re
import os
import string
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy 

#####################
# Step I: read data
#####################

#User enters the file location information
#s = raw_input('Input the file location ->')
#s2 = raw_input('Input the file name ->')
#s3 = raw_input('Input the save file name ->')
s="P:\PCAOB Staff\Interns\zhangy1\NAF\\test"
s2="output2.xlsx"
s3="output3.xlsx"

#For the main file path, one needs to make sure they are forward slashes
s = string.replace(s, "\\", '/')

# Combining the main folder location and the xlsx file that has the list of issuernames
main_location = s + '/' + s2
#main_location = "P:/PCAOB Staff/Interns/zhangy1/NAF/test/output_filter2.xlsx"


# Combining the temporary csv files for the different results with the folder location
results = s + '/' + s3
#results="P:/PCAOB Staff/Interns/zhangy1/NAF/test/output_final.xlsx"
	
		
#Pandas reading the excel, excel contain issuer, company and cik
in_file = pd.read_excel(main_location)

###########################
# Step II: Clean the dataset
###########################
#remove the punctuation of one column in dataframe
def remove_punctuation(s):
    s = ''.join([i for i in s if i not in frozenset(string.punctuation)])
    return s

# subsitute punctuation with space

#use ratio partial_ratio token_set_ratio token_sort_ratio together
# reference: https://stackoverflow.com/questions/31806695/when-to-use-which-fuzz-function-to-compare-2-strings

#this function is to remove keywords and strings after keywords
def remove(str, keyword):
	if keyword in str:
		return str[:str.find(keyword)]
	else:
		return str


def find_best(name,list):
	up_list=[remove(list[i]," LLC")  for i in range(len(list))]
	up_list=[remove(up_list[i]," INCORPORATION") for i in range(len(up_list))]
	up_list=[remove(up_list[i]," INC") for i in range(len(up_list))]
	up_list=[remove(up_list[i]," CORPORATION") for i in range(len(up_list))]
	up_list=[remove(up_list[i]," CORP") for i in range(len(up_list))]
	up_list=[remove(up_list[i]," COMPANY") for i in range(len(up_list))]
#	up_list=[remove(up_list[i]," FUND") for i in range(len(up_list))]
	up_list=[remove(up_list[i]," LTD") for i in range(len(up_list))]
	v_sum=[]
	v1=[]
	v2=[]
	v3=[]
	v4=[]
	for i in list:
		i=i.upper()
		tv1=fuzz.ratio(name,i)
		tv2=fuzz.partial_ratio(name,i)
		tv3=fuzz.token_set_ratio(name,i)
		tv4=fuzz.token_sort_ratio(name, i)
		tv_sum=tv1+tv2+tv3+tv4
		v_sum.append(tv_sum)
		v1.append(tv1)
		v2.append(tv2)
		v3.append(tv3)
		v4.append(tv4)
	index=v_sum.index(max(v_sum))
	row={"Best_Name":list[index],"Sum_of_score":v_sum[index],"Score1":v1[index],"Score2":v2[index],"Score3":v3[index],"Score4":v4[index],"best_flag":numpy.nan}
	return row  # return a dataframe which contains issuername, matched company, four scors and best one's flag 
			
	
#preprocess the dataframe: remove punctuation, capitalize names, clean CIK, groupby 
in_file['COMPANY'] = in_file['COMPANY'].apply(remove_punctuation)
in_file['issuer'] = in_file['issuer'].apply(remove_punctuation)
in_file["issuer"] = in_file["issuer"].str.upper()
in_file["COMPANY"] = in_file["COMPANY"].str.upper()

for i in range(5):
	in_file=in_file.replace(numpy.nan,'',regex=True) #convert all float nan to blank string
	in_file["FormlyName"+str(i)]=[str(in_file["FormlyName"+str(i)][j]).upper() for j in range(len(in_file["FormlyName"+str(i)]))]  #upper string
	in_file["FormlyName"+str(i)]=[remove_punctuation(str(in_file["FormlyName"+str(i)][j])) for j in range(len(in_file["FormlyName"+str(i)]))] # remove_punctuation
	
group_file= in_file.groupby(by="issuer")
	
##################################
# Step III : Conduct fuzzy matching	
#################################
results_df = pd.DataFrame()
for issuer, group in group_file:
	names=group[["COMPANY","FormlyName0","FormlyName1","FormlyName2","FormlyName3","FormlyName4"]] 
	well_matched=pd.DataFrame()
	for j in range(names.shape[0]):
		company=str(names.iloc[j]["COMPANY"])  #extract jth Company name
		list=names.iloc[[j]].values.tolist() #just extract jth row
		tmp=[str(list[0][i]) for i in range(len(list[0]))] #convert every element into string in list
		row_best=find_best(issuer,tmp)
		row_best.update({"COMPANY":company})
		df=pd.DataFrame(row_best,index=[0])
		well_matched=well_matched.append(df)
		
	well_matched=well_matched.reset_index(drop=True)	
	well_matched=well_matched.drop(well_matched[(well_matched.Sum_of_score!=max(well_matched.Sum_of_score) )& ((well_matched.Score1+well_matched.Score2+well_matched.Score3) < 260)].index)
	well_matched.best_flag[well_matched[well_matched.Sum_of_score==max(well_matched.Sum_of_score)].index]=1
	
	well_matched=pd.merge(well_matched,group,on="COMPANY",how="left")
	results_df=results_df.append(well_matched)

	
# write the result into excel	
writer = ExcelWriter(results)
results_df.to_excel(writer,'Best matched',index=False)
writer.save()




