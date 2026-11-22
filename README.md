# Machine Learning Process Assignment

This project demonstrates two supervised machine learning tasks using public datasets: classification for online shopping purchases and regression for air quality. A Django app lets a user submit CSV feature data for predictions and view the regression exploration charts.

**Live app:** [https://ml-process-assignment.onrender.com](https://ml-process-assignment.onrender.com)

## Project purpose

- **Classification:** predict whether an online shopping session ends in a purchase.
- **Regression:** estimate the measured carbon monoxide concentration, `CO(GT)`, from air quality sensor and weather measurements.
- **Django interface:** upload CSV rows and receive predictions. The regression page also presents univariate, bivariate, and multivariate analyses.

The shopping model uses extracted session features, not a shopper's identity or raw browsing history. The air quality model predicts `CO(GT)` from measurements; it is an educational estimate and not a certified safety reading.

## Datasets

- [UCI Online Shoppers Purchasing Intention](https://archive.ics.uci.edu/dataset/468/online): 12,330 sessions and 17 features. The target is `Revenue` (purchase or no purchase).
- [UCI Air Quality](https://archive.ics.uci.edu/dataset/360/air): hourly sensor readings. The target is `CO(GT)` in mg/m³. The UCI data uses `-200` to mark missing readings.

The script downloads these datasets through the `ucimlrepo` package when it runs.

## Machine learning process

### Online shopping classification

The script uses a stratified 60/20/20 train, validation, and test split. Numeric values are median-imputed and scaled. Categories are filled with the most common value and one-hot encoded. A logistic regression classifier uses balanced class weights because purchases are the minority class. Five-fold grid search selects `C` using F1 score.

### Air quality regression

Rows with a missing `CO(GT)` target are removed. Missing predictor readings are imputed during preprocessing. The data is split chronologically into 60% training, 20% validation, and 20% test data so later readings are held out. Ridge regression is tuned with five-fold cross-validation. Exploratory analysis uses the training portion only:

- **Univariate:** descriptive statistics and histograms for each numeric variable.
- **Bivariate:** feature-to-CO correlations and scatter plots for the four strongest numeric associations.
- **Multivariate:** a correlation matrix across numeric features and the CO target.

These analyses show patterns in the data; correlations do not establish causes.

## Results from the current run

| Task | Metric | Result |
|---|---|---:|
| Shopping classification | Test accuracy | 85.64% |
| Shopping classification | Test precision | 52.53% |
| Shopping classification | Test recall | 76.18% |
| Shopping classification | Test F1 | 62.18% |
| Shopping classification | Test ROC-AUC | 0.907 |
| Air quality regression | Test RMSE | 0.537 mg/m³ |
| Air quality regression | Test MAE | 0.346 mg/m³ |
| Air quality regression | Test R² | 0.841 |

For the shopping classifier, the test confusion matrix is `[[1821, 263], [91, 291]]`, with rows and columns ordered as no purchase, purchase. It found 291 purchases and missed 91. The test set has many more non-purchases than purchases, so accuracy alone is not a sufficient summary.

The air quality validation RMSE was 0.851 mg/m³, higher than the test RMSE. Interpret the test score cautiously because performance differed between these time periods. The script writes exact metrics for each run to `outputs/results/metrics.json`.

## Requirements

Python and the packages in `outputs/requirements.txt` are required. The first run needs internet access to retrieve the UCI datasets.

From the repository root in PowerShell:

```powershell
python -m pip install -r outputs\requirements.txt
python outputs\ml_assignment.py
```

The script trains both models and creates `outputs/results/`, including the metrics JSON, analysis charts, confusion matrix, test predictions, and saved model files.

## Run the Django app locally

Train the models first, then from the repository root:

```powershell
$env:DJANGO_DEBUG = "true"
cd outputs\webapp
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The main page accepts a CSV for either prediction task. The regression analysis page shows the univariate, bivariate, and multivariate results. CSV files must contain the input columns used by the selected model. Stop the local server with Ctrl+C.

## Render deployment

The repository-root `render.yaml` defines a Render Blueprint. Connect the GitHub repository to Render and create a Blueprint from this file. During the build, Render installs dependencies, downloads the UCI datasets, trains both models, collects static files, and starts Django with Gunicorn. The generated `outputs/results/` files do not need to be committed because the build creates them.

The Blueprint uses Render's free service plan for a coursework demonstration. Free services can sleep after inactivity and may take about a minute to wake. See [Render's free service limits](https://render.com/docs/free). This deployment demonstrates the app online but does not provide always-on production availability.

## Repository layout

```text
Assignment1/
├── render.yaml
├── README.md
└── outputs/
    ├── ml_assignment.py
    ├── requirements.txt
    ├── ML_Process_Report.docx
    ├── ML_Process_Presentation.pptx
    ├── results/                 # generated when the script runs
    └── webapp/                  # Django project and prediction pages
```

## Responsible use

This project is for coursework and demonstration. It does not establish cause and effect. Shopping predictions may be wrong and should not be used to make consequential decisions about individuals. Air quality predictions are not substitutes for calibrated instruments or official measurements.
