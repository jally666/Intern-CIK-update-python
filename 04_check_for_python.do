

import excel "P:\PCAOB Staff\Interns\zhangy1\NAF\test\test.xlsx", firstrow clear
save test, replace
import excel "P:\PCAOB Staff\Interns\zhangy1\NAF\test\output3.xlsx", firstrow clear
merge m:1 IssuerName using test
drop if _merge==2
drop _merge

******************************
* this part is flexible, just for good looking
format %50s IssuerName
order IssuerName Best_Name best_flag cik CIK COMPANY FormlyName*
br if best_flag==1 & cik != CIK

cap drop duplicate_flag
duplicates tag IssuerName, gen(duplicate_flag)
order duplicate_flag 
*******************************

* this step is to update cik
sort IssuerName
gen same_flag =1 if cik==CIK
egen have_flag=sum(same_flag), by(IssuerName)
order have_flag same_flag


replace cik=CIK if have_flag==0 & best_flag==1  // replace wrong or missing ciks
drop if have_flag==0 & same_flag != 1 & best_flag != 1 // drop useless data
drop if have_flag==1 & same_flag != 1  // find if cik exist in CIKs and drop others


****Result may still have duplicates, it's reasonable, since best_flag is not unique
***eg: IssuerName="AMERICAN OIL & GAS INC"
*** I guess we should compare STATE 

