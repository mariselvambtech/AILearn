<!-- converted from assignment.xlsx -->

## Sheet: Sheet1
| multiple linear regression |  |  | r2 score |
| --- | --- | --- | --- |
|  |  |  | 0.76 |
| SVM |  |  |  |
| kernel | gamma | c | r2 score |
| rbf | scale | 1 | -0.106 |
| rbf | auto | 1 | -0.106 |
| rbf | auto | 0.5 | -0.135 |
| rbf | scale | 0.5 | -0.135 |
| linear | scale | 1 | -0.11 |
| linear | auto | 1 | -0.11 |
| linear | auto | 0.5 | -0.12 |
| linear | scale | 0.5 | -0.12 |
| poly | scale | 1 | -0.099 |
| poly | auto | 1 | couldnot get result as model.fit takes longer time |
| poly | scale | 0.5 | -0.08 |
| poly | auto | 0.5 | couldnot get result as model.fit takes longer time |
| Random forest regressor |  |  |  |
| n_estimator | criterion |  | r2 score |
| 50 | squared_error |  | 0.818 |
| 100 | squared_error |  | 0.82 |
| 100 | absolute_error |  | 0.829 |
| 50 | absolute_error |  | 0.829 |
| 50 | friedman_mse |  | 0.819 |
| 100 | friedman_mse |  | 0.82 |
| 100 | poisson |  | 0.822 |
| 50 | poisson |  | 0.819 |
| Decision tree |  |  |  |
| splitter | criterion |  | r2 score |
| random | squared_error |  | 0.67 |
| best | squared_error |  | 0.67 |
| best | friedman_mse |  | 0.66 |
| random | friedman_mse |  | 0.7 |
| best | absolute_error |  | 0.72 |
| random | absolute_error |  | 0.69 |
| best | poisson |  | 0.66 |
| random | poisson |  | 0.69 |