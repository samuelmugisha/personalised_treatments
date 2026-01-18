# Model to improve adherence to medications in Haemophiliac patients
A parametrized model which takes as input a discrete set of temporal treatments from a database and produces a time series of pharmacokinetic curves representing drug concentration in the body. 
<img src = "report/haemophilia.jpg" style="float:center;width:640px;height:320px;">

**Background:**
Poor adherence to treatment of chronic diseases is a global problem of
striking magnitude. There is no gold standard for measuring treatment adherence. Traditional
medication adherence measures, for instance, pill counts, self-patient reports,
etc. do not account for the pharmacokinetic properties of drugs in the body, hence they
misrepresent the true therapeutic exposure. Improving the effectiveness of treatment
adherence measures saves lives, time and money.

**Methods:** We have implemented a system to model the pharmacokinetics of drugs
taken by patients (with particular relevance to haemophilia) and ranked patients according
to adherence from a defined therapeutic threshold. Data were obtained from
Haemtrack; a patient diary system used by patients in the UK. We have implemented
and compared ranking algorithms based on manhattan and euclidean distance, and Dynamic
Time Warping.

**Results:** A list of patients, ranked by their adherence according to their euclidean
and manhattan distance was obtained. The same patient listing was obtained using the
Dynamic Time warping algorithm; this consistency of order acts as informal validation
of the ranking. Health professionals could be prompted by email at predefined intervals
informing them of non-adherent patients.

**Conclusion:** The proposed adherence measure captured pharmacokinetic properties
of the drug and the patient drug-taking behavior. Patients were ranked according to
their adherence and health professionals could be prompted by email notifying them of
non-adherent patients, improving monitoring of patient adherence especially as regards
to chronic diseases and potentially saving time, money and lives.

**Key Terms:**
- Adherence
- Pharmacokinetics
- Drug therapy
- Manhattan distance
- Euclidean distance
- Time series
- Dynamic time warping

**Key learnings:**
- Time-series analysis
- Python
- SQL
- Bash/Cmd scripts
- Basic Pharmacokinetics

