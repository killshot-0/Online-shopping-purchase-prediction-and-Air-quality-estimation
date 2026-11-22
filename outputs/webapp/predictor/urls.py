from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name="home"),
    path("regression-analysis/", views.regression_analysis, name="regression_analysis"),
    path("analysis-chart/<slug:kind>/", views.analysis_chart, name="analysis_chart"),
    path("health/", views.health, name="health"),
]
