from pathlib import Path
import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import render
from django.http import FileResponse, Http404, JsonResponse

RESULTS = Path(settings.BASE_DIR).parent / "results"
MAX_UPLOAD = 5 * 1024 * 1024
MAX_ROWS = 5000
CHARTS = {
    "univariate": "regression_univariate_distributions.png",
    "bivariate": "regression_bivariate_top_features.png",
    "multivariate": "regression_multivariate_correlation.png",
}

def home(request):
    result = None
    error = None
    if request.method == "POST":
        task = request.POST.get("task", "")
        upload = request.FILES.get("csv_file")
        filenames = {"shopping":"online_purchase_model.joblib", "air":"air_quality_co_model.joblib"}
        if task not in filenames or upload is None:
            error = "Choose a prediction type and select a CSV file."
        elif upload.size > MAX_UPLOAD:
            error = "The file must be smaller than 5 MB."
        else:
            try:
                model_path = RESULTS / filenames[task]
                if not model_path.exists():
                    raise FileNotFoundError(f"Model not found: {model_path}. Run the training script first.")
                model = joblib.load(model_path)
                data = pd.read_csv(upload)
                if data.empty:
                    raise ValueError("The CSV has no data rows.")
                if len(data) > MAX_ROWS:
                    raise ValueError(f"The CSV can contain at most {MAX_ROWS} rows.")
                expected = list(model.feature_names_in_)
                missing = [name for name in expected if name not in data.columns]
                if missing:
                    raise ValueError("CSV is missing required columns: " + ", ".join(missing))
                data = data[expected]
                if task == "shopping":
                    predicted = model.predict(data)
                    probability = model.predict_proba(data)[:, 1]
                    result = [{"prediction": "Purchase" if int(label) == 1 else "No purchase", "probability": f"{score:.1%}"} for label, score in zip(predicted, probability)]
                else:
                    predicted = model.predict(data)
                    result = [{"prediction": f"{value:.3f} mg/m³"} for value in predicted]
            except Exception as exc:
                error = str(exc)
    return render(request, "predictor/home.html", {"result": result, "error": error})


def regression_analysis(request):
    stats_path = RESULTS / "regression_univariate_stats.csv"
    corr_path = RESULTS / "regression_bivariate_correlations.csv"
    stats = pd.read_csv(stats_path, index_col=0).round(3).to_html(classes="data-table") if stats_path.exists() else None
    correlations = pd.read_csv(corr_path).round(3).to_html(index=False, classes="data-table") if corr_path.exists() else None
    return render(request, "predictor/regression_analysis.html", {"stats": stats, "correlations": correlations})

def analysis_chart(request, kind):
    filename = CHARTS.get(kind)
    if not filename:
        raise Http404("Chart not found")
    path = RESULTS / filename
    if not path.exists():
        raise Http404("Run the assignment script first to generate regression analysis charts")
    return FileResponse(path.open("rb"), content_type="image/png")


def health(request):
    return JsonResponse({"status": "ok"})
