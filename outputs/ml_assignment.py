"""Two ML tasks using public UCI data. Run: python outputs/ml_assignment.py"""
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
from ucimlrepo import fetch_ucirepo
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib

OUT=Path(__file__).resolve().parent/'results'; OUT.mkdir(exist_ok=True)
SEED=42

def prep(X, numeric, categorical):
    return ColumnTransformer([
        ('num', Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler())]), numeric),
        ('cat', Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore'))]), categorical)
    ])

def online_shopping():
    ds=fetch_ucirepo(id=468)
    X=ds.data.features.copy(); y=ds.data.targets.iloc[:,0].astype(int)
    X=X.drop(columns=[c for c in X.columns if c.lower() in ['id']],errors='ignore')
    numeric=X.select_dtypes(include='number').columns.tolist(); categorical=X.select_dtypes(exclude='number').columns.tolist()
    Xtrain,Xtemp,ytrain,ytemp=train_test_split(X,y,test_size=.4,random_state=SEED,stratify=y)
    Xval,Xtest,yval,ytest=train_test_split(Xtemp,ytemp,test_size=.5,random_state=SEED,stratify=ytemp)
    pipe=Pipeline([('prep',prep(X,numeric,categorical)),('model',LogisticRegression(max_iter=2000,class_weight='balanced'))])
    grid=GridSearchCV(pipe,{'model__C':[.1,1,10]},scoring='f1',cv=5,n_jobs=-1).fit(Xtrain,ytrain)
    model=grid.best_estimator_; pv=model.predict(Xval); pt=model.predict(Xtest); proba=model.predict_proba(Xtest)[:,1]
    metrics={'rows':len(X),'features':X.shape[1],'purchase_rate':float(y.mean()),'positive_label':'Revenue=True (purchase)',
      'validation_f1':float(f1_score(yval,pv)),'test_accuracy':float(accuracy_score(ytest,pt)),
      'test_precision':float(precision_score(ytest,pt)),'test_recall':float(recall_score(ytest,pt)),
      'test_f1':float(f1_score(ytest,pt)),'test_roc_auc':float(roc_auc_score(ytest,proba)),
      'confusion_matrix':confusion_matrix(ytest,pt).tolist(),'best_params':grid.best_params_}
    joblib.dump(model,OUT/'online_purchase_model.joblib')
    pd.DataFrame(confusion_matrix(ytest,pt),index=['actual no','actual yes'],columns=['pred no','pred yes']).to_csv(OUT/'purchase_confusion_matrix.csv')
    return metrics

def air_quality():
    ds=fetch_ucirepo(id=360)
    X=ds.data.features.copy()
    targets=ds.data.targets
    # UCI may return CO(GT) in the features table instead of a target table.
    # Locate it in either place, then remove it from the inputs to avoid leakage.
    target_table = targets if targets is not None else X
    target=next((c for c in target_table.columns if 'CO(GT)' in c), None)
    if target is None:
        raise ValueError('Could not find the CO(GT) target column in the downloaded Air Quality data.')
    y=target_table[target].replace(-200,float('nan'))
    if target in X.columns:
        X=X.drop(columns=[target])
    X=X.replace(-200,float('nan'))
    keep=y.notna(); X=X.loc[keep].reset_index(drop=True); y=y.loc[keep].astype(float).reset_index(drop=True)
    # Retain sensor and weather features; sequential rows stay chronological.
    n=len(X); a=int(.6*n); b=int(.8*n)
    Xtr,Xva,Xte=X.iloc[:a],X.iloc[a:b],X.iloc[b:]; ytr,yva,yte=y.iloc[:a],y.iloc[a:b],y.iloc[b:]
    numeric=X.select_dtypes(include='number').columns.tolist(); categorical=X.select_dtypes(exclude='number').columns.tolist()
    # Regression EDA on training data only: one variable, two-variable, and multiple-variable views.
    train_eda=Xtr[numeric].copy()
    train_eda['CO(GT)']=ytr.to_numpy()
    train_eda.describe().to_csv(OUT/'regression_univariate_stats.csv')
    axes=train_eda.hist(figsize=(14,10),bins=25)
    plt.suptitle('Univariate distributions: training data')
    plt.tight_layout(); plt.savefig(OUT/'regression_univariate_distributions.png',dpi=150); plt.close()
    corr=train_eda.corr(numeric_only=True)
    target_corr=corr['CO(GT)'].drop('CO(GT)').dropna().sort_values(key=lambda values: values.abs(),ascending=False)
    target_corr.rename('correlation_with_CO_GT').to_csv(OUT/'regression_bivariate_correlations.csv')
    top=target_corr.head(4).index.tolist()
    fig,axs=plt.subplots(2,2,figsize=(10,8))
    for ax,name in zip(axs.flat,top):
        ax.scatter(train_eda[name],train_eda['CO(GT)'],s=9,alpha=.35)
        ax.set_xlabel(name); ax.set_ylabel('CO(GT) mg/m^3'); ax.set_title(f'{name} vs CO(GT)')
    for ax in list(axs.flat)[len(top):]: ax.set_visible(False)
    fig.tight_layout(); fig.savefig(OUT/'regression_bivariate_top_features.png',dpi=150); plt.close(fig)
    corr.to_csv(OUT/'regression_multivariate_correlation.csv')
    fig,ax=plt.subplots(figsize=(12,10)); im=ax.imshow(corr,cmap='RdBu_r',vmin=-1,vmax=1)
    ax.set_xticks(range(len(corr.columns)),corr.columns,rotation=75,ha='right',fontsize=7)
    ax.set_yticks(range(len(corr.columns)),corr.columns,fontsize=7)
    fig.colorbar(im,ax=ax,label='Pearson correlation'); ax.set_title('Multivariate numeric correlation matrix (training data)')
    fig.tight_layout(); fig.savefig(OUT/'regression_multivariate_correlation.png',dpi=150); plt.close(fig)
    pipe=Pipeline([('prep',prep(X,numeric,categorical)),('model',Ridge())])
    grid=GridSearchCV(pipe,{'model__alpha':[.1,1,10,100]},scoring='neg_mean_squared_error',cv=5,n_jobs=-1).fit(Xtr,ytr)
    model=grid.best_estimator_; pv=model.predict(Xva); pt=model.predict(Xte)
    metrics={'rows_after_missing_target_removal':len(X),'features':X.shape[1],'target':'CO(GT) in mg/m^3',
      'missing_predictor_cells_before_imputation':int(X.isna().sum().sum()),'split':'chronological 60/20/20',
      'validation_rmse':float(mean_squared_error(yva,pv)**.5),'test_rmse':float(mean_squared_error(yte,pt)**.5),
      'test_mae':float(mean_absolute_error(yte,pt)),'test_r2':float(r2_score(yte,pt)),'best_params':grid.best_params_}
    joblib.dump(model,OUT/'air_quality_co_model.joblib')
    pd.DataFrame({'actual':yte,'predicted':pt}).to_csv(OUT/'air_quality_test_predictions.csv',index=False)
    plt.figure(figsize=(6,5)); plt.scatter(yte,pt,s=12,alpha=.5); plt.xlabel('Observed CO(GT)'); plt.ylabel('Predicted CO(GT)'); plt.title('Air quality test predictions'); plt.tight_layout(); plt.savefig(OUT/'air_quality_test_plot.png',dpi=150); plt.close()
    return metrics

if __name__=='__main__':
    result={'online_shopping_classification':online_shopping(),'air_quality_regression':air_quality(),'random_seed':SEED}
    (OUT/'metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))
