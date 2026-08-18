#!/bin/bash
LOG=/opt/keiba-unified/jra/scripts/v3_pipeline.log
exec > >(tee -a $LOG) 2>&1

cd /opt/keiba-unified
export PYTHONPATH=.
export KEIBA_DB_PATH=/opt/keiba-unified/jra/data/keiba_live.db

echo ''
echo '#### Pipeline start: '$(date)' ####'

echo ''
echo '=== [1/4] Wait for win training to finish ==='
while pgrep -f 'model_v3_win.py train' > /dev/null; do
  sleep 60
done
echo 'Win training process ended: '$(date)

echo ''
echo '=== [2/4] Win model verification ==='
python3 << 'PYE'
import pickle, numpy as np
with open('jra/data/models/model_v3_win.pkl','rb') as f:
    o = pickle.load(f)
m = o['model']
print('num_trees:', m.num_trees())
print('best_iter:', m.best_iteration if hasattr(m,'best_iteration') else 'N/A')
print('label_type:', o['label_type'])
print('pos_rate:', float(o['pos_rate']))
print('cv_logloss mean:', np.mean(o['cv_scores']), 'std:', np.std(o['cv_scores']))
imp = m.feature_importance(importance_type='gain')
fn = m.feature_name()
top = sorted(zip(fn,imp), key=lambda x:-x[1])[:15]
print('Top 15 features (gain):')
for n,v in top: print(f'  {n}: {v:.0f}')
PYE

echo ''
echo '=== [3/4] Place model training ==='
python3 -u jra/scripts/model_v3_place.py train

echo ''
echo '=== Place model verification ==='
python3 << 'PYE'
import pickle, numpy as np
with open('jra/data/models/model_v3_place.pkl','rb') as f:
    o = pickle.load(f)
m = o['model']
print('num_trees:', m.num_trees())
print('best_iter:', m.best_iteration if hasattr(m,'best_iteration') else 'N/A')
print('label_type:', o['label_type'])
print('pos_rate:', float(o['pos_rate']))
print('cv_logloss mean:', np.mean(o['cv_scores']), 'std:', np.std(o['cv_scores']))
imp = m.feature_importance(importance_type='gain')
fn = m.feature_name()
top = sorted(zip(fn,imp), key=lambda x:-x[1])[:15]
print('Top 15 features (gain):')
for n,v in top: print(f'  {n}: {v:.0f}')
PYE

echo ''
echo '=== [4/4] Backtest v3 ==='
python3 -u jra/scripts/backtest_v3.py

echo ''
echo '#### Pipeline complete: '$(date)' ####'
