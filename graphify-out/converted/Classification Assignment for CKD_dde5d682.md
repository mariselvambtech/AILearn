<!-- converted from Classification Assignment for CKD.docx -->

Classification Assignment
Problem Statement or Requirement:
A requirement from the Hospital, Management asked us to create a predictive
model which will predict the Chronic Kidney Disease (CKD) based on the
several parameters. The Client has provided the dataset of the same.
1.) Identify your problem statement. To identify the CKD based on the parameters like age	bp, sugar level etc.,
2.) Tell basic info about the dataset (Total number of rows, columns) . The dataset has 399, rows 25 columns

3.) Mention the pre-processing method if you’re doing any (like converting
string to number – nominal data)
- The output column is classification which is yes or no type of answer,  so converted it into 1 or 0 using dataset['classification'] = dataset['classification'].map({'yes':1,'no':0})
- converted the data to ordinal using pd.get dummies dataset = pd.get_dummies(dataset,drop_first=True)
- converted the output classification column to 1D array dependent = dataset[['classification']].values.ravel()
- Standardised the input colums using ('sc',StandardScaler())
4.) Develop a good model with good evaluation metric. You can use any
machine learning algorithm; you can create many models. Finally, you
have to come up with final model.
5.) All the research values of each algorithm should be documented. (You
can make tabulation or screenshot of the results.)
6.) Mention your final model, justify why u have chosen the same.
Note: Mentioned points are necessary, kindly mail your document as
well as .ipynb (code file) with respective name.

 Sub file name also should be properly named for Example
(SVM_Ramisha_Assi-5.ipynb)
Communication is important (How you are representing the
document.)
Kindly uploaded in the Github and Share it with us

Decision Tree
has score of ROC AUC 0.987

Best params are

Random Forest
has score of ROC AUC 0.9993


Best params are

SVM classifiation
has score of ROC AUC 0.9991

Best params are


As a final conclusion, Support vector machine classification has the highest rate  of AUC score that can be considered as best model for CKD use case