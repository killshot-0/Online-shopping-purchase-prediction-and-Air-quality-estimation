# Django application and deployment

## Run locally
From the main project folder, install packages and train the models:

```powershell
python -m pip install -r outputs/requirements.txt
python outputs/ml_assignment.py
$env:DJANGO_DEBUG = "true"
cd outputs/webapp
python manage.py runserver
```

Open http://127.0.0.1:8000/. The home page predicts shopping purchase or air quality from an input CSV. The regression analysis page displays univariate, bivariate, and multivariate outputs.

## Deploy using Render Blueprint
The repository-root `render.yaml` describes a Render web service. Connect the project repository to Render and create a Blueprint from it. Render builds the dependencies, downloads the UCI datasets, trains the models, collects static files, and starts Django with Gunicorn. The configuration uses a generated secret, disables debug, enables HTTPS settings, and checks `/health/`.

The Blueprint uses Render's free plan to keep the coursework demo at no charge. Render says free services are intended for previews/hobby use, can sleep after 15 minutes without traffic, and may take about a minute to wake. For a production service that must stay available, select a paid plan and review Render's current costs.

This app accepts CSV uploads, does not store the uploaded data, and limits files to 5 MB and 5,000 rows. Configure additional rate limiting if making it publicly accessible. Never commit real secrets. Django's deployment check should be run after connecting the actual service.
